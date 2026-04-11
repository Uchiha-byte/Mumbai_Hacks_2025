from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Literal
from app.core.quick_analyzer import get_quick_analyzer
from app.core.storage import get_storage
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

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
@limiter.limit("5/minute")
async def analyze_content(request: Request, request_data: AnalysisRequest):
    """
    Standard deep analysis endpoint - uses direct service calls
    """
    try:
        if request_data.content_type == "text":
            from app.core.analysis_service import text_analysis_service
            import json
            result_dict = await text_analysis_service.analyze(request_data.content)
            return AnalysisResponse(result=json.dumps(result_dict, indent=2), agent_used="Gemini 2.5 Flash")

        elif request_data.content_type == "image":
            from app.core.media_service import detect_deepfake_image
            result = await detect_deepfake_image(request_data.content)
            return AnalysisResponse(result=result, agent_used="GPT-4o Vision")

        elif request_data.content_type == "audio":
            from app.core.media_service import detect_deepfake_audio
            result = await detect_deepfake_audio(request_data.content)
            return AnalysisResponse(result=result, agent_used="HuggingFace")

        elif request_data.content_type == "video":
            from app.core.media_service import detect_deepfake_video
            result = await detect_deepfake_video(request_data.content)
            return AnalysisResponse(result=result, agent_used="HuggingFace")

        else:
            raise HTTPException(status_code=400, detail="Unsupported content type")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quick-analyze", response_model=QuickAnalysisResponse)
@limiter.limit("10/minute")
async def quick_analyze(request: Request, request_data: QuickAnalysisRequest):
    """
    Fast analysis endpoint - uses similarity search and forensics (2-5s response)
    """
    try:
        analyzer = get_quick_analyzer()
        storage = get_storage()
        
        # Route based on content type
        if request_data.content_type == "text":
            result = await analyzer.analyze_text(request_data.content)
        elif request_data.content_type == "image":
            result = await analyzer.analyze_image(request_data.content)
        else:
            raise HTTPException(status_code=422, detail=f"Content type '{request_data.content_type}' not yet supported for quick analysis")
        
        # Save to storage
        analysis_id = storage.save_analysis({
            "content_type": request_data.content_type,
            "verdict": result["verdict"],
            "confidence": result["confidence"],
            "metadata": request_data.metadata
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
