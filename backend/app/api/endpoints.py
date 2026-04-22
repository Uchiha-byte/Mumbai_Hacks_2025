from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Literal
import asyncio
from collections import defaultdict
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
    reason_codes: List[str] = []
    low_confidence: bool = False
    deep_analysis_recommended: bool = False
    deep_analysis_started: bool = False

class FeedbackRequest(BaseModel):
    analysis_id: Optional[str] = None
    original_content: str
    predicted_verdict: str
    user_verdict: str
    user_confidence: int  # 1-5
    comments: Optional[str] = None


QUALITY_METRICS = {
    "quick_total": 0,
    "quick_timeout_fallbacks": 0,
    "quick_low_confidence": 0,
    "quick_deep_analysis_started": 0,
    "verdict_counts": defaultdict(int),
    "reason_code_counts": defaultdict(int),
}


def _record_quick_metrics(result: dict):
    QUALITY_METRICS["quick_total"] += 1
    QUALITY_METRICS["verdict_counts"][result.get("verdict", "UNKNOWN")] += 1
    for code in result.get("reason_codes", []):
        QUALITY_METRICS["reason_code_counts"][code] += 1
    if "timeout_fallback" in result.get("reason_codes", []):
        QUALITY_METRICS["quick_timeout_fallbacks"] += 1
    if result.get("low_confidence"):
        QUALITY_METRICS["quick_low_confidence"] += 1
    if result.get("deep_analysis_started"):
        QUALITY_METRICS["quick_deep_analysis_started"] += 1

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
            try:
                result_dict = await asyncio.wait_for(
                    text_analysis_service.analyze(request_data.content),
                    timeout=25.0
                )
            except asyncio.TimeoutError:
                result_dict = {
                    "verdict": "MIXED",
                    "confidence": 35,
                    "reasoning": "Deep analysis timed out; returning safe fallback.",
                    "source": "deep_timeout_fallback",
                    "reason_codes": ["deep_timeout_fallback", "low_confidence"]
                }
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
        
        deep_task_started = False

        # Route based on content type
        if request_data.content_type == "text":
            try:
                result = await asyncio.wait_for(
                    analyzer.analyze_text(request_data.content),
                    timeout=12.0
                )
            except asyncio.TimeoutError:
                result = analyzer.build_timeout_response(request_data.content)
        elif request_data.content_type == "image":
            result = await analyzer.analyze_image(request_data.content)
        else:
            raise HTTPException(status_code=422, detail=f"Content type '{request_data.content_type}' not yet supported for quick analysis")

        result.setdefault("reason_codes", [])
        result.setdefault("low_confidence", False)
        result.setdefault("deep_analysis_recommended", False)

        if request_data.content_type == "text" and (
            result.get("deep_analysis_recommended") or result.get("low_confidence")
        ):
            # Fire-and-forget deep analysis for improved follow-up quality.
            from app.core.analysis_service import text_analysis_service
            asyncio.create_task(text_analysis_service.analyze(request_data.content))
            deep_task_started = True

        result["deep_analysis_started"] = deep_task_started
        _record_quick_metrics(result)
        
        # Save to storage
        analysis_id = storage.save_analysis({
            "content_type": request_data.content_type,
            "verdict": result["verdict"],
            "confidence": result["confidence"],
            "metadata": request_data.metadata,
            "reason_codes": result.get("reason_codes", []),
            "deep_analysis_started": deep_task_started
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
            "embeddings": embeddings.get_stats(),
            "quality_metrics": await get_quality_metrics()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality-metrics")
async def get_quality_metrics():
    storage = get_storage()
    feedback = storage.get_all_feedback()

    # Derived metrics from user feedback.
    by_label = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    false_positive_count = 0
    for item in feedback:
        predicted = str(item.get("predicted_verdict", "UNKNOWN")).upper()
        actual = str(item.get("user_verdict", "UNKNOWN")).upper()
        if predicted == actual:
            by_label[predicted]["tp"] += 1
        else:
            by_label[predicted]["fp"] += 1
            by_label[actual]["fn"] += 1
            if predicted in {"FAKE", "VERIFIED"}:
                false_positive_count += 1

    precision_recall = {}
    for label, row in by_label.items():
        precision = row["tp"] / (row["tp"] + row["fp"]) if (row["tp"] + row["fp"]) else 0.0
        recall = row["tp"] / (row["tp"] + row["fn"]) if (row["tp"] + row["fn"]) else 0.0
        precision_recall[label] = {"precision": round(precision, 3), "recall": round(recall, 3)}

    quick_total = QUALITY_METRICS["quick_total"] or 1
    return {
        "quick_total": QUALITY_METRICS["quick_total"],
        "fallback_rate": round(QUALITY_METRICS["quick_timeout_fallbacks"] / quick_total, 3),
        "timeout_rate": round(QUALITY_METRICS["quick_timeout_fallbacks"] / quick_total, 3),
        "low_confidence_rate": round(QUALITY_METRICS["quick_low_confidence"] / quick_total, 3),
        "deep_analysis_trigger_rate": round(QUALITY_METRICS["quick_deep_analysis_started"] / quick_total, 3),
        "false_positive_rate_fake_verified": round(false_positive_count / max(len(feedback), 1), 3),
        "verdict_counts": dict(QUALITY_METRICS["verdict_counts"]),
        "reason_code_counts": dict(QUALITY_METRICS["reason_code_counts"]),
        "precision_recall_by_verdict": precision_recall,
        "feedback_samples": len(feedback)
    }
