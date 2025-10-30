from fastapi import APIRouter, Request, Depends
from app.controllers import ai_controller
from app.core.auth import verify_api_key

router = APIRouter()

@router.post("/completions")
async def create_completion(request: Request, api_key: str = Depends(verify_api_key)):
    return await ai_controller.chat_completions(request)
