from fastapi import APIRouter, Request
from app.controllers import ai_controller

router = APIRouter()

@router.post("/completions")
async def create_completion(request: Request):
    return await ai_controller.chat_completions(request)
