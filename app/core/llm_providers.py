import os, json, time
import contextvars
import requests as _req
import httpx
from typing import Dict, List, Iterable
from openai import OpenAI, AzureOpenAI

# LLM Context Management
ACTIVE_LLM = contextvars.ContextVar("ACTIVE_LLM", default="chatgpt")
LLAMA_MODEL = contextvars.ContextVar("LLAMA_MODEL", default=os.getenv("OLLAMA_MODEL", "llama3.1:8b"))

# Ollama Configuration
OLLAMA_BASE = (os.getenv("OLLAMA_BASE") or "http://localhost:11434").rstrip("/")
OLLAMA_CHAT = f"{OLLAMA_BASE}/api/chat"
OLLAMA_TAGS = f"{OLLAMA_BASE}/api/tags"
OLLAMA_VERSION = f"{OLLAMA_BASE}/api/version"

# OpenAI/Azure Clients
USE_AZURE = os.getenv("AZURE_OPENAI", "false").lower() in ("1","true","yes")
if USE_AZURE:
    OAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    OAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    OAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    OAI_API_VER = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    oai_client = AzureOpenAI(api_key=OAI_API_KEY, azure_endpoint=OAI_ENDPOINT, api_version=OAI_API_VER)
    CHAT_MODEL = OAI_DEPLOYMENT
else:
    OAI_API_KEY = os.getenv("OPENAI_API_KEY")
    oai_client = OpenAI(api_key=OAI_API_KEY)
    CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")

def set_active_llm(provider: str, model: str | None = None):
    prov = (provider or "").strip().lower()
    if prov == "llama":
        ACTIVE_LLM.set("llama")
        if model:
            LLAMA_MODEL.set(model)
    else:
        ACTIVE_LLM.set("chatgpt")

def get_active_llm():
    return ACTIVE_LLM.get(), LLAMA_MODEL.get()

def _ollama_messages_from_openai(messages: list[dict]) -> list[dict]:
    """Map OpenAI-style messages to Ollama chat format."""
    out = []
    for m in messages:
        role = (m.get("role") or "").strip()
        content = m.get("content") or ""
        if not role or not content:
            continue
        out.append({"role": role, "content": content})
    return out

def _ollama_list_tags() -> list[str]:
    try:
        r = _req.get(OLLAMA_TAGS, timeout=10)
        r.raise_for_status()
        data = r.json() or {}
        models = data.get("models") or []
        return [m.get("name") for m in models if isinstance(m, dict) and m.get("name")]
    except Exception:
        return []

def _explain_ollama_404(model: str) -> str:
    tags = _ollama_list_tags()
    if tags:
        return (f"Ollama returned 404 for model '{model}'. Installed models are:\n"
                + "\n".join([f" - {t}" for t in tags])
                + "\nSet OLLAMA_MODEL to one of the above, or pull the desired tag:\n"
                + f"  ollama pull {model}\n")
    return (f"Ollama returned 404 for model '{model}'. No matching tag found. "
            f"Check that the model is pulled:\n  ollama pull {model}\n"
            f"Or set OLLAMA_MODEL to an installed tag.\n")

def _ollama_chat_stream_sync(messages: list[dict], model: str) -> Iterable[str]:
    """Streaming chat with Ollama (/api/chat). Synchronous."""
    payload = {
        "model": model,
        "messages": _ollama_messages_from_openai(messages),
        "stream": True,
    }
    with _req.post(OLLAMA_CHAT, json=payload, stream=True, timeout=300) as r:
        if r.status_code == 404:
            try:
                body = r.json()
                detail = body.get("error") or body
            except Exception:
                detail = r.text
            raise RuntimeError(_explain_ollama_404(model) + f"\nDetails: {detail}")
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            msg = (obj or {}).get("message") or {}
            chunk = msg.get("content") or ""
            if chunk:
                yield chunk

def _ollama_chat_once_sync(messages: list[dict], model: str) -> str:
    """Single chat response with Ollama (/api/chat, stream=False)."""
    payload = {
        "model": model,
        "messages": _ollama_messages_from_openai(messages),
        "stream": False,
    }
    r = _req.post(OLLAMA_CHAT, json=payload, timeout=300)
    if r.status_code == 404:
        try:
            body = r.json()
            detail = body.get("error") or body
        except Exception:
            detail = r.text
        raise RuntimeError(_explain_ollama_404(model) + f"\nDetails: {detail}")
    r.raise_for_status()
    data = r.json() or {}
    msg = (data or {}).get("message") or {}
    return msg.get("content") or ""

def oai_stream(messages: list[dict], temperature=0.2, max_tokens=2000) -> Iterable[str]:
    """Streams from the active provider (Llama or OpenAI)."""
    provider, llama_model = get_active_llm()
    if provider == "llama":
        for chunk in _ollama_chat_stream_sync(messages, llama_model):
            yield chunk
        return

    # OpenAI/Azure path
    stream = oai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=temperature,
        stream=True,
        max_tokens=max_tokens
    )
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta and delta.content is not None:
            yield delta.content

def oai_plan(question: str, planner_system: str) -> Dict:
    """Planner step that returns JSON. Uses active provider."""
    provider, llama_model = get_active_llm()
    if provider == "llama":
        msgs = [
            {"role": "system", "content": planner_system},
            {"role": "user",   "content": question},
        ]
        try:
            result_text = _ollama_chat_once_sync(msgs, llama_model)
        except Exception as e:
            from app.utils.helpers import logger
            logger.error(f"[planner] Llama failed: {e}")
            return {"action": "chat", "final_answer": f"I couldn't plan with llama ({e})."}
        try:
            return json.loads(result_text)
        except Exception:
            return {"action": "chat", "final_answer": result_text}

    # OpenAI/Azure path
    resp = oai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role":"system","content": planner_system},
                  {"role":"user","content": question}],
        temperature=0.1,
        max_tokens=2000,
    )
    txt = resp.choices[0].message.content.strip()
    try:
        return json.loads(txt)
    except Exception:
        if any(w in question.lower() for w in ["hi","hello","salam","hey"]):
            return {"action":"chat", "final_answer":"Hi! How can I help you today?"}
        return {"action":"chat", "final_answer":"I'm here. Ask about tickers or dividends and I'll pull the data."}