import mimetypes, time, requests
import logging
from typing import Optional
from app.config.settings import NODE_ANALYZE_URL

logger = logging.getLogger("ai_controller")

def is_upload_like(obj) -> bool:
    return obj is not None and hasattr(obj, "filename") and hasattr(obj, "content_type") and hasattr(obj, "read")

def _is_upload(obj) -> bool:
    return obj is not None and hasattr(obj, "filename") and hasattr(obj, "content_type") and hasattr(obj, "read")

def extract_text_via_node(file_name: str, file_bytes: bytes, content_type: str | None = None, rid: str | None = None) -> str:
    tag = f"[{rid}]" if rid else ""
    try:
        guessed = content_type or mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        files = {"file": (file_name, file_bytes, guessed)}
        t0 = time.time()
        logger.info(f"{tag} Handoff → Node {NODE_ANALYZE_URL} file='{file_name}' ctype='{guessed}' size={len(file_bytes)}")
        r = requests.post(NODE_ANALYZE_URL, files=files, timeout=120)
        elapsed = int((time.time() - t0) * 1000)
        logger.info(f"{tag} Node response status={r.status_code} elapsed={elapsed}ms")
        r.raise_for_status()
        data = r.json() or {}
        txt = (data.get("text") or "").strip()
        logger.info(f"{tag} Extracted text length={len(txt)} chars")
        if not txt:
            logger.warning(f"{tag} Node returned empty text")
        return txt
    except Exception as e:
        logger.exception(f"{tag} analyze upload failed: {e}")
        return ""