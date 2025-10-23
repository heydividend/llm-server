import os
import time
import uuid
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.routes import chat as ai_routes


# Setup logging before anything else
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("app")

# Initialize FastAPI
app = FastAPI(title="Chat + SQL Server (Streaming) + Enhanced Web Search")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


# Timing Middleware
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        rid = str(uuid.uuid4())[:8]
        request.state.rid = rid
        start = time.time()

        response = await call_next(request)

        elapsed_ms = int((time.time() - start) * 1000)
        logger.info(f"[{rid}] {request.method} {request.url.path} done in {elapsed_ms} ms")

        return response


# Add middleware and routes
app.add_middleware(TimingMiddleware)
app.include_router(ai_routes.router, prefix="/v1/chat", tags=["AI"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/")
async def root():
    return FileResponse("static/index.html")
