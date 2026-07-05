from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from backend.database import get_db, TriageItem
from agents.coordinator_agent import analyze_waste

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str
    message: str
    image_url: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    status: str

@router.post("/", response_model=ChatResponse)
async def handle_chat(request: ChatRequest, db: Session = Depends(get_db)):
    # Call the ADK Agent with user_id to maintain chat context
    agent_result = await analyze_waste(
        user_query=request.message, 
        image_url=request.image_url, 
        user_id=request.user_id
    )
    if agent_result["status"] == "flagged":
        # Append raw response to notes so the admin can see what the AI outputted
        notes = agent_result["notes"]
        if agent_result.get("raw_response"):
            notes += f" [AI Draft: {agent_result['raw_response']}]"
            
        new_item = TriageItem(
            user_id=request.user_id,
            user_query=request.message,
            image_url=request.image_url,
            agent_notes=notes
        )
        db.add(new_item)
        db.commit()
        return ChatResponse(
            response="This looks like it might be hazardous or requires special disposal. I have flagged this for our human experts to review. You will be notified shortly!",
            status="flagged"
        )
    else:
        # Return the successful agent response
        return ChatResponse(
            response=agent_result["raw_response"],
            status="success"
        )
