import os, json, time
import contextvars
import requests as _req
import httpx
from typing import Dict, List, Iterable, Optional
from openai import OpenAI, AzureOpenAI

# Gemini import (optional, for Azure VM deployment)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False

# LLM Context Management
ACTIVE_LLM = contextvars.ContextVar("ACTIVE_LLM", default="chatgpt")
LLAMA_MODEL = contextvars.ContextVar("LLAMA_MODEL", default=os.getenv("OLLAMA_MODEL", "llama3.1:8b"))

# Ollama Configuration
OLLAMA_BASE = (os.getenv("OLLAMA_BASE") or "http://localhost:11434").rstrip("/")
OLLAMA_CHAT = f"{OLLAMA_BASE}/api/chat"
OLLAMA_TAGS = f"{OLLAMA_BASE}/api/tags"
OLLAMA_VERSION = f"{OLLAMA_BASE}/api/version"

# OpenAI/Azure Clients with timeout and retry configuration
OAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "60"))
OAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "3"))

http_client = httpx.Client(
    timeout=httpx.Timeout(OAI_TIMEOUT, connect=10.0),
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
)

USE_AZURE = os.getenv("AZURE_OPENAI", "false").lower() in ("1","true","yes")
if USE_AZURE:
    OAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    OAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    OAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    OAI_API_VER = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    
    if not OAI_ENDPOINT or not OAI_API_KEY:
        raise ValueError("Azure OpenAI enabled but AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY not set")
    
    oai_client = AzureOpenAI(
        api_key=OAI_API_KEY,
        azure_endpoint=OAI_ENDPOINT,
        api_version=OAI_API_VER,
        http_client=http_client,
        max_retries=OAI_MAX_RETRIES
    )
    CHAT_MODEL = OAI_DEPLOYMENT
    print(f"[INFO] 🔵 Azure OpenAI initialized: endpoint={OAI_ENDPOINT}, deployment={OAI_DEPLOYMENT}, api_version={OAI_API_VER}")
else:
    OAI_API_KEY = os.getenv("OPENAI_API_KEY")
    oai_client = OpenAI(
        api_key=OAI_API_KEY,
        http_client=http_client,
        max_retries=OAI_MAX_RETRIES
    )
    CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = None
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_client = genai.GenerativeModel('gemini-2.5-pro')
        print(f"[INFO] 🟢 Gemini 2.5 Pro initialized for chart/FX analysis")
    except Exception as e:
        print(f"[WARN] ⚠️  Gemini initialization failed: {e}")
elif not GEMINI_AVAILABLE:
    print("[WARN] ⚠️  google-generativeai package not installed - install for production deployment")
else:
    print("[WARN] ⚠️  GEMINI_API_KEY not set - Gemini features disabled")

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


def oai_stream_with_model(
    messages: list[dict],
    model_deployment: str,
    temperature=0.2,
    max_tokens=2000
) -> Iterable[str]:
    """
    Streams from a specific Azure OpenAI deployment (GPT-5, Grok-4, etc).
    Used by multi-model routing system.
    """
    if not USE_AZURE:
        raise ValueError("oai_stream_with_model requires Azure OpenAI to be enabled")
    
    stream = oai_client.chat.completions.create(
        model=model_deployment,
        messages=messages,
        temperature=temperature,
        stream=True,
        max_tokens=max_tokens
    )
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta and delta.content is not None:
            yield delta.content


def gemini_stream(messages: list[dict], temperature=0.2, max_tokens=2000) -> Iterable[str]:
    """
    Streams from Gemini 2.5 Pro.
    Used for chart analysis, FX trading, and multimodal queries.
    """
    if not gemini_client:
        raise ValueError("Gemini client not initialized - check GEMINI_API_KEY")
    
    # Convert OpenAI-style messages to Gemini format
    gemini_history = []
    system_instruction = None
    
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        
        if role == "system":
            system_instruction = content
        elif role == "user":
            gemini_history.append({"role": "user", "parts": [content]})
        elif role == "assistant":
            gemini_history.append({"role": "model", "parts": [content]})
    
    # Create chat session
    chat = gemini_client.start_chat(history=gemini_history[:-1] if len(gemini_history) > 1 else [])
    
    # Get last user message
    last_message = gemini_history[-1]["parts"][0] if gemini_history else ""
    
    # Stream response
    response = chat.send_message(
        last_message,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
        stream=True
    )
    
    for chunk in response:
        if chunk.text:
            yield chunk.text


def gemini_chat_once(messages: list[dict], temperature=0.2, max_tokens=2000) -> str:
    """Non-streaming Gemini response"""
    chunks = list(gemini_stream(messages, temperature, max_tokens))
    return "".join(chunks)