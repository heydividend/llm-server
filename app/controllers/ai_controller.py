import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse

from app.config import settings
from app.utils.helper import (
    is_upload_like,
    extract_text_via_node,
    _maybe_flatten_vision_json,
    handle_request,
)

from app.utils.extract_tickers import extract_tickers_function

from app.logger_module import QueryResponseLogger
from app.services import conversation_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("ai_controller")

# === Environment setup ===
BASE = "/home/azureuser/llm/server"
ENV = os.path.join(BASE, ".env") if os.path.isdir(BASE) else ".env"
load_dotenv(ENV)




# === Query/Response Logger ===

# Initialize logger
query_logger = QueryResponseLogger(log_dir=os.path.join(BASE, "logs") if os.path.isdir(BASE) else "logs")

# === SQL Server configuration ===
HOST = os.getenv("SQLSERVER_HOST")
PORT = os.getenv("SQLSERVER_PORT", "1433")
DB   = os.getenv("SQLSERVER_DB")
USER = os.getenv("SQLSERVER_USER")
PWD  = os.getenv("SQLSERVER_PASSWORD")
DRV  = os.getenv("ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
LOGIN_TIMEOUT = os.getenv("SQLSERVER_LOGIN_TIMEOUT", "10")
CONN_TIMEOUT  = os.getenv("SQLSERVER_CONN_TIMEOUT", "20")

# === API keys & feature flags ===
GOOGLE_CSE_KEY = os.getenv("GOOGLE_CSE_KEY", "").strip()
GOOGLE_CSE_CX  = os.getenv("GOOGLE_CSE_CX", "").strip()
BING_API_KEY   = os.getenv("BING_API_KEY", "").strip()

AUTO_WEB_FALLBACK = os.getenv("AUTO_WEB_FALLBACK", "true").lower() in ("1", "true", "yes")
FAST_WEB_MAX_PAGES = int(os.getenv("FAST_WEB_MAX_PAGES", "5"))


def process_query_with_tickers(query: str, rid: str, debug: bool = False) -> tuple:
    """Extract tickers from query and return updated query with ticker information."""
    ticker_result = extract_tickers_function(query, debug=debug)
    
    if ticker_result["success"] and ticker_result["detected_tickers"]:
        updated_query = ticker_result["updated_query"]
        detected_tickers = ticker_result["detected_tickers"]
        elapsed_ms = ticker_result["elapsed_ms"]
        
        ticker_info = f"[TICKER_EXTRACTION] Detected tickers: {', '.join(detected_tickers)} (processed in {elapsed_ms}ms)\n"
        
        logger.info(
            f"[{rid}] Ticker extraction: found {len(detected_tickers)} ticker(s) "
            f"{detected_tickers} in {elapsed_ms}ms"
        )
        
        if debug and ticker_result.get("debug_info"):
            logger.info(f"[{rid}] Ticker debug info: {ticker_result['debug_info']}")
        
        return updated_query, ticker_info, detected_tickers
    else:
        if not ticker_result["success"]:
            logger.warning(f"[{rid}] Ticker extraction failed: {ticker_result.get('error', 'unknown error')}")
        else:
            logger.info(f"[{rid}] No tickers detected in query")
        
        return query, "", []


def handle_conversation_memory(
    session_id: str = None,
    conversation_id: str = None,
    user_query: str = "",
    rid: str = "",
    max_history_tokens: int = 4000
) -> dict:
    """
    Handle conversation memory: create session/conversation if needed, load history, save user message.
    
    Returns:
        Dict with session_id, conversation_id, and conversation_history
    """
    try:
        if not session_id or not conversation_service.session_exists(session_id):
            session_id = conversation_service.create_session()
            logger.info(f"[{rid}] Created new session: {session_id}")
        else:
            conversation_service.update_session_activity(session_id)
            logger.info(f"[{rid}] Using existing session: {session_id}")
        
        if not conversation_id or not conversation_service.conversation_exists(conversation_id):
            conversation_id = conversation_service.create_conversation(session_id)
            logger.info(f"[{rid}] Created new conversation: {conversation_id}")
        else:
            logger.info(f"[{rid}] Using existing conversation: {conversation_id}")
        
        conversation_history = conversation_service.get_conversation_history(
            conversation_id,
            max_tokens=max_history_tokens
        )
        logger.info(f"[{rid}] Loaded {len(conversation_history)} messages from history")
        
        try:
            conversation_service.add_message(
                conversation_id=conversation_id,
                role="user",
                content=user_query,
                metadata={"rid": rid}
            )
            logger.info(f"[{rid}] Saved user message to conversation {conversation_id}")
        except Exception as e:
            logger.warning(f"Failed to save conversation message (non-critical): {e}")
        
        return {
            "session_id": session_id,
            "conversation_id": conversation_id,
            "conversation_history": conversation_history
        }
        
    except Exception as e:
        logger.error(f"[{rid}] Conversation memory error: {e}")
        return {
            "session_id": session_id or "",
            "conversation_id": conversation_id or "",
            "conversation_history": []
        }


async def chat_completions(request: Request):
    """
    Handles chat completion requests with daily query/response logging.
    """
    rid = getattr(request.state, "rid", str(uuid.uuid4())[:8])
    ctype = request.headers.get("content-type", "").lower()

    # ---------- MULTIPART ----------
    if ctype.startswith("multipart/form-data"):
        try:
            form = await request.form()
        except Exception as e:
            logger.exception(f"[{rid}] form parsing failed: {e}")
            return JSONResponse({"error": "invalid multipart form"}, status_code=400)

        # Log form overview
        form_overview = []
        for k, v in form.multi_items():
            vtype = type(v).__name__
            vlen = None
            try:
                if isinstance(v, (str, bytes)):
                    vlen = len(v)
                elif hasattr(v, "read"):
                    b = await v.read()
                    vlen = len(b)
                    if hasattr(v, "seek"):
                        await v.seek(0)
            except Exception:
                pass
            form_overview.append({"key": k, "type": vtype, "len": vlen})
            logger.info(f"[{rid}] form field key='{k}' type={vtype} len={vlen}")

        req_model = (form.get("model") or "").strip()

        # Parse text fields
        messages_raw = form.get("messages", "[]")
        meta_raw     = form.get("meta", "{}")
        stream_raw   = form.get("stream", "true")
        debug_raw    = form.get("debug", "false")

        try:
            messages = json.loads(messages_raw) if messages_raw else []
            assert isinstance(messages, list)
        except Exception:
            logger.warning(f"[{rid}] invalid JSON in 'messages'")
            return JSONResponse({
                "error": "invalid JSON in 'messages' form field",
                "received_messages": messages_raw,
                "form_overview": form_overview
            }, status_code=400)

        try:
            meta = json.loads(meta_raw) if meta_raw else {}
            assert isinstance(meta, dict)
        except Exception:
            logger.warning(f"[{rid}] invalid JSON in 'meta'")
            return JSONResponse({
                "error": "invalid JSON in 'meta' form field",
                "received_meta": meta_raw,
                "form_overview": form_overview
            }, status_code=400)

        if not messages:
            return JSONResponse({"error": "messages[] required", "form_overview": form_overview}, status_code=400)

        # Extract system + last user question
        system_blobs, question = [], ""
        for m in messages:
            if m.get("role") == "system" and m.get("content"):
                system_blobs.append(m["content"])
        for m in reversed(messages):
            if m.get("role") == "user":
                question = m.get("content", "")
                break
        if not question:
            return JSONResponse({"error": "no user content found", "form_overview": form_overview}, status_code=400)

        user_system_all = "\n\n".join(system_blobs) if system_blobs else ""

        debug  = str(debug_raw).lower() in ("1","true","yes","on")
        stream = str(stream_raw).lower() in ("", "1","true","yes","on")

        # === TICKER EXTRACTION ===
        updated_question, ticker_info, detected_tickers = process_query_with_tickers(
            question, rid, debug=debug
        )

        # Build overrides
        overrides = {
            "planner_system": (meta.get("planner_system") or "").strip(),
            "answer_system":  (meta.get("answer_system")  or "").strip(),
            "prepend_user":   (meta.get("prepend_user")   or "").strip(),
            "use_web":        bool(meta.get("use_web", False)),
            "llm_provider":   (meta.get("llm_provider")   or req_model or "").strip(),
            "llama_model":    (meta.get("llama_model")    or "").strip(),
        }

        if ticker_info:
            overrides["prepend_user"] = (ticker_info + overrides["prepend_user"]).strip()

        # Handle file upload
        preferred_keys = ["file", "files", "file[]", "files[]", "upload", "attachment"]
        upload = None
        picked_key = None

        for key in preferred_keys:
            cand = form.get(key)
            if is_upload_like(cand):
                upload, picked_key = cand, key
                break
        if not upload:
            for key in preferred_keys:
                try:
                    lst = form.getlist(key)
                except Exception:
                    lst = None
                if lst:
                    for v in lst:
                        if is_upload_like(v):
                            upload, picked_key = v, key
                            break
                if upload:
                    break
        if not upload:
            for k, v in form.multi_items():
                if is_upload_like(v):
                    upload, picked_key = v, k
                    break
        
        if is_upload_like(upload):
            try:
                up_name = upload.filename or "upload.bin"
                up_ct   = upload.content_type or "application/octet-stream"
                up_bytes = await upload.read()
                logger.info(f"[{rid}] picked upload key='{picked_key}' name='{up_name}' size={len(up_bytes)}")
            except Exception as e:
                logger.exception(f"[{rid}] reading upload failed: {e}")
                return JSONResponse({"error": "failed to read uploaded file"}, status_code=400)

            extracted_text = extract_text_via_node(up_name, up_bytes, up_ct, rid=rid)

            if extracted_text:
                extracted_text = _maybe_flatten_vision_json(extracted_text)
                MAX_PREPEND = 4000
                if len(extracted_text) > MAX_PREPEND:
                    extracted_text = extracted_text[:MAX_PREPEND] + f"\n\n...[truncated] (orig={len(extracted_text)} chars)..."
                overrides["prepend_user"] = (f"FILE_TEXT (OCR/DI extract):\n{extracted_text}\n\n" + overrides["prepend_user"]).strip()

        # === CONVERSATION MEMORY ===
        session_id_raw = (form.get("session_id") or "").strip()
        conversation_id_raw = (form.get("conversation_id") or "").strip()
        
        conv_memory = handle_conversation_memory(
            session_id=session_id_raw if session_id_raw else None,
            conversation_id=conversation_id_raw if conversation_id_raw else None,
            user_query=question,
            rid=rid
        )
        
        session_id = conv_memory["session_id"]
        conversation_id = conv_memory["conversation_id"]
        conversation_history = conv_memory["conversation_history"]
        
        overrides["conversation_history"] = conversation_history
        
        # === LOG QUERY ===
        query_logger.log_query(
            rid=rid,
            query=question,
            metadata={
                "detected_tickers": detected_tickers,
                "original_query": question,
                "updated_query": updated_question,
                "use_web": overrides.get("use_web"),
                "llm_provider": overrides.get("llm_provider"),
                "stream": stream,
                "has_file": is_upload_like(upload),
                "session_id": session_id,
                "conversation_id": conversation_id
            }
        )

        logger.info(
            f"[{rid}] Processing request: stream={stream}, debug={debug}, tickers={detected_tickers}, "
            f"conversation_id={conversation_id}"
        )

        # Generate response
        gen = handle_request(updated_question, user_system_all, overrides, debug=debug)
        
        if stream:
            # Wrapper to collect chunks while streaming
            async def stream_and_log():
                collected = []
                try:
                    for chunk in gen:
                        collected.append(chunk)
                        yield chunk
                finally:
                    response_text = "".join(collected)
                    
                    # Save assistant response to conversation
                    try:
                        conversation_service.add_message(
                            conversation_id=conversation_id,
                            role="assistant",
                            content=response_text,
                            metadata={"rid": rid, "detected_tickers": detected_tickers}
                        )
                    except Exception as e:
                        logger.warning(f"Failed to save conversation message (non-critical): {e}")
                    
                    # Log after streaming completes
                    query_logger.log_full_conversation(
                        rid=rid,
                        query=question,
                        response=response_text,
                        metadata={
                            "detected_tickers": detected_tickers,
                            "original_query": question,
                            "updated_query": updated_question,
                            "stream": True,
                            "use_web": overrides.get("use_web"),
                            "session_id": session_id,
                            "conversation_id": conversation_id
                        }
                    )
            
            logger.info(f"[{rid}] streaming response → SSE")
            return StreamingResponse(stream_and_log(), media_type="text/event-stream")

        # Non-streaming
        collected = []
        for chunk in gen:
            collected.append(chunk)
        text = "".join(collected)
        
        # === SAVE ASSISTANT RESPONSE ===
        try:
            conversation_service.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=text,
                metadata={"rid": rid, "detected_tickers": detected_tickers}
            )
        except Exception as e:
            logger.warning(f"Failed to save conversation message (non-critical): {e}")
        
        # === LOG FULL CONVERSATION ===
        query_logger.log_full_conversation(
            rid=rid,
            query=question,
            response=text,
            metadata={
                "detected_tickers": detected_tickers,
                "original_query": question,
                "updated_query": updated_question,
                "stream": False,
                "use_web": overrides.get("use_web"),
                "session_id": session_id,
                "conversation_id": conversation_id
            }
        )
        
        logger.info(f"[{rid}] non-stream response length={len(text)}")
        return JSONResponse({
            "id": "chatcmpl-local",
            "object": "chat.completion",
            "choices": [{"message": {"role": "assistant", "content": text}}],
            "metadata": {
                "detected_tickers": detected_tickers,
                "original_query": question,
                "updated_query": updated_question,
                "session_id": session_id,
                "conversation_id": conversation_id
            }
        })

    # ---------- JSON path ----------
    try:
        body = await request.json()
    except Exception as e:
        logger.warning(f"[{rid}] invalid JSON body: {e}")
        return JSONResponse({"error": "invalid JSON"}, status_code=400)

    messages = body.get("messages", [])
    if not isinstance(messages, list) or not messages:
        return JSONResponse({"error": "messages[] required"}, status_code=400)

    # Extract system + last user question
    system_blobs, question = [], ""
    for m in messages:
        if m.get("role") == "system" and m.get("content"):
            system_blobs.append(m["content"])
    for m in reversed(messages):
        if m.get("role") == "user":
            question = m.get("content", "")
            break
    if not question:
        return JSONResponse({"error": "no user content found"}, status_code=400)

    user_system_all = "\n\n".join(system_blobs) if system_blobs else ""
    meta = (body.get("meta", {}) or {})
    req_model = (body.get("model") or "").strip()

    debug  = bool(body.get("debug", False))
    stream = bool(body.get("stream", True))

    # === TICKER EXTRACTION ===
    updated_question, ticker_info, detected_tickers = process_query_with_tickers(
        question, rid, debug=debug
    )

    overrides = {
        "planner_system": (meta.get("planner_system") or "").strip(),
        "answer_system":  (meta.get("answer_system")  or "").strip(),
        "prepend_user":   (meta.get("prepend_user")   or "").strip(),
        "use_web":        bool(meta.get("use_web", False)),
        "llm_provider":   (meta.get("llm_provider")   or req_model or "").strip(),
        "llama_model":    (meta.get("llama_model")    or "").strip(),
    }

    if ticker_info:
        overrides["prepend_user"] = (ticker_info + overrides["prepend_user"]).strip()

    # === CONVERSATION MEMORY ===
    session_id_raw = (body.get("session_id") or "").strip()
    conversation_id_raw = (body.get("conversation_id") or "").strip()
    
    conv_memory = handle_conversation_memory(
        session_id=session_id_raw if session_id_raw else None,
        conversation_id=conversation_id_raw if conversation_id_raw else None,
        user_query=question,
        rid=rid
    )
    
    session_id = conv_memory["session_id"]
    conversation_id = conv_memory["conversation_id"]
    conversation_history = conv_memory["conversation_history"]
    
    overrides["conversation_history"] = conversation_history

    # === LOG QUERY ===
    query_logger.log_query(
        rid=rid,
        query=question,
        metadata={
            "detected_tickers": detected_tickers,
            "original_query": question,
            "updated_query": updated_question,
            "use_web": overrides.get("use_web"),
            "llm_provider": overrides.get("llm_provider") == "llama" if overrides.get("llm_provider")  else "fallback",
            "stream": stream,
            "session_id": session_id,
            "conversation_id": conversation_id
        }
    )

    logger.info(
        f"[{rid}] (JSON) Processing: stream={stream}, debug={debug}, tickers={detected_tickers}, "
        f"conversation_id={conversation_id}"
    )

    gen = handle_request(updated_question, user_system_all, overrides, debug=debug)
    
    if stream:
        async def stream_and_log():
            collected = []
            try:
                for chunk in gen:
                    collected.append(chunk)
                    yield chunk
            finally:
                response_text = "".join(collected)
                
                # Save assistant response to conversation
                try:
                    conversation_service.add_message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=response_text,
                        metadata={"rid": rid, "detected_tickers": detected_tickers}
                    )
                except Exception as e:
                    logger.warning(f"Failed to save conversation message (non-critical): {e}")
                
                query_logger.log_full_conversation(
                    rid=rid,
                    query=question,
                    response=response_text,
                    metadata={
                        "detected_tickers": detected_tickers,
                        "original_query": question,
                        "updated_query": updated_question,
                        "stream": True,
                        "use_web": overrides.get("use_web"),
                        "session_id": session_id,
                        "conversation_id": conversation_id
                    }
                )
        
        logger.info(f"[{rid}] (JSON) streaming response → SSE")
        return StreamingResponse(stream_and_log(), media_type="text/event-stream")

    # Non-streaming
    collected = []
    for chunk in gen:
        collected.append(chunk)
    text = "".join(collected)
    
    # === SAVE ASSISTANT RESPONSE ===
    try:
        conversation_service.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=text,
            metadata={"rid": rid, "detected_tickers": detected_tickers}
        )
    except Exception as e:
        logger.warning(f"Failed to save conversation message (non-critical): {e}")
    
    # === LOG FULL CONVERSATION ===
    query_logger.log_full_conversation(
        rid=rid,
        query=question,
        response=text,
        metadata={
            "detected_tickers": detected_tickers,
            "original_query": question,
            "updated_query": updated_question,
            "stream": False,
            "use_web": overrides.get("use_web"),
            "session_id": session_id,
            "conversation_id": conversation_id
        }
    )
    
    logger.info(f"[{rid}] (JSON) non-stream response length={len(text)}")
    return JSONResponse({
        "id": "chatcmpl-local",
        "object": "chat.completion",
        "choices": [{"message": {"role": "assistant", "content": text}}],
        "metadata": {
            "detected_tickers": detected_tickers,
            "original_query": question,
            "updated_query": updated_question,
            "session_id": session_id,
            "conversation_id": conversation_id
        }
    })