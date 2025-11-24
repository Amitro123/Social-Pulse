from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List
from api.database import db
from datetime import datetime

router = APIRouter(prefix="/api", tags=["campaigns"]) 

class CampaignIn(BaseModel):
    id: Optional[str] = None
    topic: str
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    trigger_count: Optional[int] = None
    created_at: Optional[str] = None

class CampaignOut(BaseModel):
    id: str
    topic: str
    summary: Optional[str]
    sentiment: Optional[str]
    trigger_count: Optional[int]
    created_at: str

@router.get("/campaigns", response_model=List[CampaignOut])
async def list_campaigns(limit: int = 20):
    rows = db.list_campaigns(limit=limit)
    return [
        {
            "id": r.get("id"),
            "topic": r.get("topic"),
            "summary": r.get("summary"),
            "sentiment": r.get("sentiment"),
            "trigger_count": r.get("trigger_count"),
            "created_at": r.get("created_at"),
        }
        for r in rows
    ]

@router.post("/campaigns", response_model=CampaignOut)
async def create_campaign(c: CampaignIn):
    cid = c.id or f"c-{int(datetime.utcnow().timestamp()*1000)}"
    payload = {
        "id": cid,
        "topic": c.topic,
        "summary": c.summary,
        "sentiment": c.sentiment,
        "trigger_count": c.trigger_count,
        "created_at": c.created_at or datetime.utcnow().isoformat(),
    }
    db.save_campaign(payload)
    return payload
