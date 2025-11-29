from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Literal
from langchain_core.messages import HumanMessage
from app.agents.supervisor import get_supervisor_agent
from app.agents.text_agent import get_text_agent
from app.agents.image_agent import get_image_agent
from app.agents.audio_agent import get_audio_agent
from app.agents.video_agent import get_video_agent
from app.agents.quick_agent import get_quick_analyzer
from app.core.storage import get_storage

router = APIRouter()

class AnalysisRequest(BaseModel):
    content: str
    content_type: str  # text, image, audio, video

class AnalysisResponse(BaseModel):
    result: str
    agent_used: str

# New models for quick analysis
class QuickAnalysisRequest(BaseModel):
    content: str
    content_type: Literal["text", "image"]
    metadata: dict = {}

class QuickAnalysisResponse(BaseModel):
    verdict: Literal["FAKE", "SUSPECT", "MIXED", "VERIFIED"]
    confidence: int  # 0-100
    summary_one_liner: str
    tl_dr_bullets: List[str]
    evidence: List[dict]
    reasons: List[str]

class FeedbackRequest(BaseModel):
    analysis_id: Optional[str] = None
    original_content: str
    predicted_verdict: str
    user_verdict: str
    user_confidence: int  # 1-5
    comments: Optional[str] = None

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_content(request: AnalysisRequest):
    """
    Standard deep analysis endpoint - uses full agent reasoning
    """
    try:
        if request.content_type == "text":
            agent = get_text_agent()
            result = agent.invoke({"messages": [HumanMessage(content=request.content)]})
            return AnalysisResponse(result=result["messages"][-1].content, agent_used="Text Analysis Agent")
            
        elif request.content_type == "image":
            agent = get_image_agent()
            result = agent.invoke({"messages": [HumanMessage(content=request.content)]})
            return AnalysisResponse(result=result["messages"][-1].content, agent_used="Image Forensics Agent")
            
        elif request.content_type == "audio":
            agent = get_audio_agent()
            result = agent.invoke({"messages": [HumanMessage(content=request.content)]})
            return AnalysisResponse(result=result["messages"][-1].content, agent_used="Audio Verification Agent")
            
        elif request.content_type == "video":
            agent = get_video_agent()
            result = agent.invoke({"messages": [HumanMessage(content=request.content)]})
            return AnalysisResponse(result=result["messages"][-1].content, agent_used="Video Analysis Agent")
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported content type")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quick-analyze", response_model=QuickAnalysisResponse)
async def quick_analyze(request: QuickAnalysisRequest):
    """
    Fast analysis endpoint - uses similarity search and forensics (2-5s response)
    """
    try:
        analyzer = get_quick_analyzer()
        storage = get_storage()
        
        # Route based on content type
        if request.content_type == "text":
            result = analyzer.analyze_text(request.content)
        elif request.content_type == "image":
            result = analyzer.analyze_image(request.content)
        else:
            raise HTTPException(status_code=422, detail=f"Content type '{request.content_type}' not yet supported for quick analysis")
        
        # Save to storage
        analysis_id = storage.save_analysis({
            "content_type": request.content_type,
            "verdict": result["verdict"],
            "confidence": result["confidence"],
            "metadata": request.metadata
        })
        
        return QuickAnalysisResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit user feedback on analysis results
    """
    try:
        storage = get_storage()
        
        feedback_data = {
            "analysis_id": feedback.analysis_id,
            "original_content": feedback.original_content[:200],  # Truncate for storage
            "predicted_verdict": feedback.predicted_verdict,
            "user_verdict": feedback.user_verdict,
            "user_confidence": feedback.user_confidence,
            "comments": feedback.comments
        }
        
        feedback_id = storage.save_feedback(feedback_data)
        
        return {
            "status": "success",
            "feedback_id": feedback_id,
            "message": "Feedback recorded. Thank you for helping improve accuracy!"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats():
    """
    Get system statistics
    """
    try:
        storage = get_storage()
        from app.core.embeddings import get_embeddings_manager
        
        embeddings = get_embeddings_manager()
        
        return {
            "storage": storage.get_stats(),
            "embeddings": embeddings.get_stats()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
