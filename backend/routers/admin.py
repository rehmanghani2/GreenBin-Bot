from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime
from backend.database import get_db, TriageItem

router = APIRouter()

class TriageItemResponse(BaseModel):
    id: int
    user_id: str
    user_query: str
    status: str
    agent_notes: str | None
    
    class Config:
        from_attributes = True

class ResolutionRequest(BaseModel):
    admin_resolution: str

@router.get("/pending", response_model=List[TriageItemResponse])
def get_pending_items(db: Session = Depends(get_db)):
    items = db.query(TriageItem).filter(TriageItem.status == "NEEDS_REVIEW").all()
    return items

@router.post("/resolve/{item_id}")
def resolve_item(item_id: int, request: ResolutionRequest, db: Session = Depends(get_db)):
    item = db.query(TriageItem).filter(TriageItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    item.status = "RESOLVED"
    item.admin_resolution = request.admin_resolution
    item.resolved_at = datetime.utcnow()
    
    db.commit()
    
    # In a real app, you would send a push notification back to the user_id here
    return {"message": "Item resolved successfully", "item_id": item.id}
