import os
import time
import uuid
import logging
import json
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from sqlalchemy import text
from app.routes import chat as ai_routes
from app.routes import income_ladder
from app.core.database import engine
from app.core.auth import verify_api_key


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
app.include_router(income_ladder.router, prefix="/v1", tags=["Income Ladder"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/healthz")
def healthz():
    return {"ok": True}


class PortfolioAllocation(BaseModel):
    ticker: str
    shares: Optional[float] = None
    target_allocation_pct: Optional[float] = None
    notes: Optional[str] = None


class SavePortfolioRequest(BaseModel):
    name: str = Field(..., description="Portfolio or watchlist name")
    type: str = Field(..., description="Type: 'portfolio' or 'watchlist'")
    allocations: List[Dict] = Field(..., description="List of position allocations")
    metadata: Optional[Dict] = Field(default_factory=dict, description="Additional metadata (e.g., target_income, years, risk_tolerance)")
    email: Optional[str] = Field(None, description="User email (optional)")


@app.post("/v1/portfolio/save")
async def save_portfolio(request: SavePortfolioRequest, api_key: str = Depends(verify_api_key)):
    """
    Save a portfolio or watchlist with positions.
    
    Args:
        request: Portfolio save request with name, type, allocations, and metadata
        
    Returns:
        Success response with group_id
    """
    try:
        if request.type not in ["portfolio", "watchlist"]:
            raise HTTPException(status_code=400, detail="Type must be 'portfolio' or 'watchlist'")
        
        if not request.allocations:
            raise HTTPException(status_code=400, detail="At least one allocation is required")
        
        user_id = None
        if request.email:
            user_query = text("""
                IF NOT EXISTS (SELECT 1 FROM dbo.user_profiles WHERE email = :email)
                BEGIN
                    INSERT INTO dbo.user_profiles (email, name) VALUES (:email, :email);
                END
                SELECT user_id FROM dbo.user_profiles WHERE email = :email;
            """)
            
            with engine.begin() as conn:
                result = conn.execute(user_query, {"email": request.email})
                row = result.fetchone()
                if row:
                    user_id = row[0]
        
        metadata_json = json.dumps(request.metadata) if request.metadata else None
        
        insert_group_query = text("""
            INSERT INTO dbo.portfolio_groups (user_id, name, type, metadata)
            OUTPUT INSERTED.group_id
            VALUES (:user_id, :name, :type, :metadata);
        """)
        
        with engine.begin() as conn:
            result = conn.execute(insert_group_query, {
                "user_id": user_id,
                "name": request.name,
                "type": request.type,
                "metadata": metadata_json
            })
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=500, detail="Failed to create portfolio group")
            group_id = row[0]
            
            for alloc in request.allocations:
                ticker = alloc.get("ticker")
                if not ticker:
                    continue
                
                shares = alloc.get("shares")
                target_allocation_pct = alloc.get("target_allocation_pct") or alloc.get("allocation_pct")
                notes = alloc.get("notes")
                
                insert_position_query = text("""
                    INSERT INTO dbo.portfolio_positions 
                    (group_id, ticker, shares, target_allocation_pct, notes)
                    VALUES (:group_id, :ticker, :shares, :target_allocation_pct, :notes);
                """)
                
                conn.execute(insert_position_query, {
                    "group_id": group_id,
                    "ticker": ticker,
                    "shares": shares,
                    "target_allocation_pct": target_allocation_pct,
                    "notes": notes
                })
        
        logger.info(f"Successfully saved {request.type} '{request.name}' with group_id={group_id}")
        
        return JSONResponse({
            "success": True,
            "message": f"{request.type.title()} '{request.name}' saved successfully",
            "group_id": group_id,
            "positions_count": len(request.allocations)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving portfolio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save {request.type}: {str(e)}")


@app.get("/")
async def root():
    return FileResponse("static/index.html")
