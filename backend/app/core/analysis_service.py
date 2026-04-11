import logging
import json
from typing import Dict
from app.core.fact_check import ClaimDetector, GoogleFactCheckAPI, NewsAPIClient, EnsembleAnalyzer
from app.core.database import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)


class TextAnalysisService:
    def __init__(self):
        self.claim_detector = ClaimDetector()
        self.fact_check = GoogleFactCheckAPI(settings.GOOGLE_FACTCHECK_API_KEY)
        self.news_api = NewsAPIClient(settings.NEWS_API_KEY)
        self.ensemble = EnsembleAnalyzer()

    async def analyze(self, text: str) -> Dict:
        db = get_db()

        # 1. Claim Detection
        claim_data = await self.claim_detector.extract_claims(text)
        if not claim_data.get("has_claims") or not claim_data.get("claims"):
            return await self._finalize(text, db, {
                "verdict": "NOT_VERIFIABLE",
                "confidence": 95,
                "reasoning": "No verifiable factual claims detected in the text.",
                "source": "claim_detector"
            })

        claims = claim_data.get("claims", [])
        primary_claim = claims[0].get("text", text) if claims else text

        # 2. Google Fact Check
        fact_result = await self.fact_check.get_verdict(primary_claim)
        if fact_result.get("found") and fact_result.get("confidence", 0) > 80:
            return await self._finalize(text, db, {
                "verdict": fact_result.get("verdict"),
                "confidence": fact_result.get("confidence"),
                "reasoning": f"Verified via Google Fact Check. Sources: {', '.join(fact_result.get('sources', []))}",
                "source": "fact_check"
            })

        # 3. News Verification
        news_result = await self.news_api.verify_claim_with_news(primary_claim)
        if news_result.get("found_in_news") and news_result.get("credible_sources", 0) >= 2:
            top_arts = news_result.get('top_articles', [])
            return await self._finalize(text, db, {
                "verdict": news_result.get("verdict"),
                "confidence": news_result.get("confidence"),
                "reasoning": f"Verified in recent news. Credible sources: {news_result.get('credible_sources')}. Top articles: {', '.join(top_arts)}",
                "source": "news"
            })

        # 4. Ensemble AI
        ensemble_result = await self.ensemble.ensemble_verdict(primary_claim)
        return await self._finalize(text, db, {
            "verdict": ensemble_result.get("verdict", "UNKNOWN"),
            "confidence": ensemble_result.get("confidence", 0),
            "reasoning": "Result based on multi-model AI ensemble consensus.",
            "source": "ensemble"
        })

    async def _finalize(self, text: str, db, result: Dict) -> Dict:
        result["content_type"] = "text"

        try:
            db_record = {
                "content": text,
                "content_type": "text",
                "verdict": result.get("verdict"),
                "confidence": result.get("confidence"),
                "reasoning": result.get("reasoning"),
                "source": result.get("source")
            }
            saved = await db.save_analysis(db_record)
            if saved and "id" in saved:
                result["analysis_id"] = saved["id"]
        except Exception as e:
            logger.error(f"Error saving analysis to DB: {e}")

        return result


# Module-level singleton
text_analysis_service = TextAnalysisService()


def get_text_analysis_service() -> TextAnalysisService:
    """Returns the global TextAnalysisService singleton."""
    return text_analysis_service
