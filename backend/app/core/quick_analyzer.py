import logging
from typing import Dict
from app.core.fact_check import GoogleFactCheckAPI, ClaimDetector, NewsAPIClient
from app.core.config import settings
from app.core.database import get_db
import asyncio

logger = logging.getLogger(__name__)

class QuickAnalyzer:
    def __init__(self):
        self.fact_check = GoogleFactCheckAPI(settings.GOOGLE_FACTCHECK_API_KEY)
        self.claim_detector = ClaimDetector()
        self.news_api = NewsAPIClient(settings.NEWS_API_KEY)
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.db = get_db()
        from app.core.forensics import get_forensics
        self.forensics = get_forensics()

    async def analyze_text(self, text: str) -> Dict:
        # 1. Extract core claim first for better searching
        claim_data = await self.claim_detector.extract_claims(text)
        claims = claim_data.get("claims", [])
        primary_claim = claims[0].get("text", text) if claims else text
        
        # 2. Generate embedding for similarity search
        embedding = await asyncio.to_thread(lambda: self.model.encode([primary_claim])[0].tolist())
        
        # 3. Query Supabase (Simultaneous with Fact Check)
        matches_task = self.db.search_similar_hoaxes(embedding_vector=embedding, threshold=0.85, count=1)
        fact_task = self.fact_check.get_verdict(primary_claim)
        
        matches, fact_result = await asyncio.gather(matches_task, fact_task)
        
        # Priority 1: Direct match in our database
        if matches:
            top_match = matches[0]
            similarity = float(top_match.get("similarity", 0))
            if similarity > 0.85:
                confidence = int(similarity * 100)
                verdict = top_match.get("verdict", "FAKE")
                return {
                    "verdict": verdict,
                    "confidence": confidence,
                    "matched_hoax": top_match.get("content"),
                    "similarity": round(similarity, 2),
                    "summary_one_liner": f"Matched known '{verdict.lower()}' in TruthScan database.",
                    "tl_dr_bullets": ["High similarity to verified hoax pattern", f"Similarity score: {confidence}%", f"Category: {top_match.get('category', 'General')}"],
                    "evidence": [{"type": "similarity_match", "score": similarity}],
                    "reasons": [f"Direct match in local vector store (Similarity: {similarity:.0%})"]
                }
        
        # Priority 2: Google Fact Check hit
        if fact_result.get("found") and fact_result.get("verdict") != "UNKNOWN":
            return {
                "verdict": fact_result.get("verdict"),
                "confidence": fact_result.get("confidence"),
                "matched_hoax": None,
                "similarity": 0,
                "summary_one_liner": f"Verified via Google Fact Check ({fact_result.get('verdict')}).",
                "tl_dr_bullets": ["Authenticated against Google's claim database", f"Sources: {', '.join(fact_result.get('sources', [])[:2])}", "Instant verification hit"],
                "evidence": [{"type": "fact_check", "sources": fact_result.get("sources")}],
                "reasons": [f"Fact-check consensus: {fact_result.get('verdict')}"]
            }
            
        # Priority 3: Quick News check (especially for recent events)
        news_result = await self.news_api.verify_claim_with_news(primary_claim)
        if news_result.get("found_in_news") and news_result.get("credible_sources", 0) >= 1:
            return {
                "verdict": news_result.get("verdict"),
                "confidence": news_result.get("confidence"),
                "matched_hoax": None,
                "similarity": 0,
                "summary_one_liner": f"Cross-referenced with recent news articles.",
                "tl_dr_bullets": [f"Found {news_result.get('total_articles')} related news articles", f"Credible sources: {news_result.get('credible_sources')}", "Verification based on news trends"],
                "evidence": [{"type": "news_check", "articles": news_result.get("top_articles")}],
                "reasons": ["Detected in credible news cycle"]
            }
            
        # Priority 4: LLM Preliminary Analysis (for speculative claims)
        if claims and "preliminary_verdict" in claims[0]:
            prelim = claims[0]
            confidence = 80 if prelim["preliminary_verdict"] != "SUSPECT" else 50
            return {
                "verdict": prelim["preliminary_verdict"],
                "confidence": confidence,
                "matched_hoax": None,
                "similarity": 0,
                "summary_one_liner": f"AI Preliminary Assessment: {prelim['preliminary_verdict']}",
                "tl_dr_bullets": [prelim.get("preliminary_reasoning", "Speculative claim detected"), "No direct verification in public databases", "Logical assessment indicates high uncertainty"],
                "evidence": [{"type": "ai_assessment", "reasoning": prelim.get("preliminary_reasoning")}],
                "reasons": ["AI Logical Verification Engine"]
            }

        # 5. Final Fallback
        return {
             "verdict": "MIXED",
             "confidence": 30,
             "matched_hoax": None,
             "similarity": 0,
             "summary_one_liner": "No rapid conclusive evidence found.",
             "tl_dr_bullets": ["No direct matches in hoax databases", "News cycle is inconclusive", "Run Deep Analysis for full multi-agent verification"],
             "evidence": [],
             "reasons": ["Inconclusive rapid scan"]
        }

    async def analyze_image(self, image_data: str) -> Dict:
        forensics_result = await asyncio.to_thread(self.forensics.analyze_image, image_data)
        
        verdict = forensics_result.get("verdict", "UNKNOWN")
        manipulation_score = forensics_result.get("manipulation_score", 0.0)
        
        verdict_map = {"MANIPULATED": "FAKE", "AUTHENTIC": "VERIFIED", "SUSPECT": "SUSPECT", "UNKNOWN": "MIXED"}
        verdict = verdict_map.get(verdict, "MIXED")
        
        confidence = int(manipulation_score * 100) if verdict == "FAKE" else 85 if verdict == "VERIFIED" else 50
        
        return {
            "verdict": verdict,
            "confidence": confidence,
            "summary_one_liner": f"{verdict}: Image forensics analysis completed",
            "tl_dr_bullets": ["Digital manipulation check", f"Manipulation Score: {manipulation_score:.0%}"],
            "evidence": [{"type": "image_forensics", "manipulation_score": manipulation_score}],
            "reasons": ["Forensics checks completed"]
        }

# Global instance
_quick_analyzer = None

def get_quick_analyzer():
    global _quick_analyzer
    if _quick_analyzer is None:
        _quick_analyzer = QuickAnalyzer()
    return _quick_analyzer
