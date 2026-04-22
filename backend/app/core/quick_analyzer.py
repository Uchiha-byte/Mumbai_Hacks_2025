import asyncio
import hashlib
import logging
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import settings
from app.core.database import get_db
from app.core.fact_check import ClaimDetector, GNewsClient, GoogleFactCheckAPI, NewsAPIClient

logger = logging.getLogger(__name__)


class QuickAnalyzer:
    def __init__(self):
        self.fact_check = GoogleFactCheckAPI(settings.GOOGLE_FACTCHECK_API_KEY)
        self.claim_detector = ClaimDetector()
        self.news_api = NewsAPIClient(settings.NEWS_API_KEY)
        self.gnews_api = GNewsClient(settings.GNEWS_API_KEY)
        self.model = None
        self.model_load_attempted = False
        self.db = get_db()
        self.forensics = None

        self.cache_ttl_seconds = 180
        self.result_cache: Dict[str, Dict] = {}
        self.provider_failures = {
            "fact_check": {"failures": 0, "open_until": 0.0},
            "news_api": {"failures": 0, "open_until": 0.0},
            "gnews_api": {"failures": 0, "open_until": 0.0}
        }

    def _content_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _load_embedding_model(self) -> Optional[object]:
        self._prefer_project_venv_site_packages()
        try:
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as error:
            logger.warning("SentenceTransformer failed to load; using deterministic embedding fallback: %s", error)
            return None

    def _prefer_project_venv_site_packages(self):
        """
        Prefer backend/.venv packages when the server is launched from a non-venv Python.
        This prevents protobuf mismatch issues seen with user-level site-packages.
        """
        backend_dir = Path(__file__).resolve().parents[2]
        venv_site = backend_dir / ".venv" / "Lib" / "site-packages"
        if not venv_site.exists():
            return
        venv_site_str = str(venv_site)
        if venv_site_str not in sys.path:
            sys.path.insert(0, venv_site_str)
        # If protobuf was already imported from user-site, evict it so imports resolve from .venv.
        bad_modules = []
        for name, module in list(sys.modules.items()):
            module_path = getattr(module, "__file__", "") or ""
            if name.startswith("google.protobuf") and "AppData\\Roaming\\Python" in module_path:
                bad_modules.append(name)
        for name in bad_modules:
            sys.modules.pop(name, None)

    async def _ensure_model_loaded(self):
        if self.model is not None or self.model_load_attempted:
            return
        self.model_load_attempted = True
        try:
            self.model = await asyncio.wait_for(asyncio.to_thread(self._load_embedding_model), timeout=2.5)
        except asyncio.TimeoutError:
            logger.warning("Embedding model load timed out; continuing with fallback embeddings.")
            self.model = None
        except Exception as error:
            logger.warning("Embedding model load failed: %s", error)
            self.model = None

    async def _embedding_for_claim(self, claim: str) -> List[float]:
        await self._ensure_model_loaded()
        if self.model is not None:
            return await asyncio.to_thread(lambda: self.model.encode([claim])[0].tolist())
        # Stable fallback embedding: keeps similarity endpoint available even without transformers.
        digest = hashlib.sha256(claim.encode("utf-8")).digest()
        values = [((byte / 255.0) * 2) - 1 for byte in digest]
        # Supabase vector search expects 384-d vectors.
        fallback = (values * 12)[:384]
        return fallback

    async def _with_retry(self, coro_factory, retries: int = 2, base_delay: float = 0.35):
        last_error = None
        for attempt in range(retries + 1):
            try:
                return await coro_factory()
            except Exception as error:
                last_error = error
                if attempt == retries:
                    break
                await asyncio.sleep(base_delay * (2**attempt) + random.uniform(0.05, 0.2))
        raise last_error

    def _provider_open(self, provider_name: str) -> bool:
        return time.time() < self.provider_failures[provider_name]["open_until"]

    def _mark_provider_success(self, provider_name: str):
        self.provider_failures[provider_name]["failures"] = 0
        self.provider_failures[provider_name]["open_until"] = 0.0

    def _mark_provider_failure(self, provider_name: str):
        bucket = self.provider_failures[provider_name]
        bucket["failures"] += 1
        if bucket["failures"] >= 3:
            # Circuit-break for 45s after repeated failures.
            bucket["open_until"] = time.time() + 45.0

    def _cache_get(self, key: str) -> Optional[Dict]:
        entry = self.result_cache.get(key)
        if not entry:
            return None
        if entry["expires_at"] < time.time():
            self.result_cache.pop(key, None)
            return None
        return entry["value"]

    def _cache_set(self, key: str, value: Dict):
        self.result_cache[key] = {"expires_at": time.time() + self.cache_ttl_seconds, "value": value}

    def build_timeout_response(self, text: str) -> Dict:
        return {
            "verdict": "MIXED",
            "confidence": 42,
            "summary_one_liner": "Quick scan timed out; low-confidence fallback returned.",
            "tl_dr_bullets": [
                "One or more providers timed out during quick scan",
                "Fallback confidence is intentionally capped",
                "Deep analysis recommended for a stronger verdict"
            ],
            "evidence": [{"type": "timeout_fallback"}],
            "reasons": ["Timeout-safe fallback from quick analysis"],
            "reason_codes": ["timeout_fallback", "low_confidence"],
            "low_confidence": True,
            "deep_analysis_recommended": True
        }

    def _calibrate_confidence(
        self,
        verdict: str,
        base_confidence: int,
        similarity: float,
        trusted_news_hits: int,
        ai_only: bool
    ) -> int:
        confidence = int(base_confidence)
        if similarity >= 0.90 and trusted_news_hits >= 1:
            confidence = max(confidence, 90)
        if ai_only:
            confidence = min(confidence, 60)
        if trusted_news_hits == 0 and verdict in {"VERIFIED", "FAKE"}:
            confidence = min(confidence, 72)
        return max(15, min(99, confidence))

    async def _safe_provider_call(
        self,
        provider_name: str,
        coro_factory,
        reason_codes: List[str],
        retries: int = 1
    ):
        if self._provider_open(provider_name):
            reason_codes.append(f"{provider_name}_circuit_open")
            return None
        try:
            result = await self._with_retry(coro_factory, retries=retries, base_delay=0.25)
            self._mark_provider_success(provider_name)
            return result
        except Exception as error:
            self._mark_provider_failure(provider_name)
            logger.warning("%s provider failed: %s", provider_name, error)
            reason_codes.append(f"{provider_name}_failed")
            return None

    async def analyze_text(self, text: str) -> Dict:
        cache_key = self._content_hash(text)
        cached = self._cache_get(cache_key)
        if cached:
            cached_response = dict(cached)
            cached_response["reason_codes"] = list(set(cached_response.get("reason_codes", []) + ["cache_hit"]))
            return cached_response

        try:
            claim_data = await asyncio.wait_for(self.claim_detector.extract_claims(text), timeout=4.5)
        except asyncio.TimeoutError:
            claim_data = {"has_claims": True, "claims": [{"text": text, "category": "unknown"}]}
            reason_codes = ["claim_extraction_timeout"]
        else:
            reason_codes: List[str] = []
        claims = claim_data.get("claims", [])
        primary_claim = claims[0].get("text", text) if claims else text
        matches = []
        similarity = 0.0

        try:
            embedding = await self._embedding_for_claim(primary_claim)
            matches = await self.db.search_similar_hoaxes(
                embedding_vector=embedding,
                threshold=0.80,
                count=1
            )
        except Exception as error:
            logger.warning("Similarity lookup failed: %s", error)
            reason_codes.append("similarity_lookup_failed")

        if matches:
            top_match = matches[0]
            similarity = float(top_match.get("similarity", 0))
            if similarity >= 0.80:
                verdict = top_match.get("verdict", "FAKE")
                confidence = self._calibrate_confidence(
                    verdict=verdict,
                    base_confidence=int(similarity * 100),
                    similarity=similarity,
                    trusted_news_hits=0,
                    ai_only=False
                )
                result = {
                    "verdict": verdict,
                    "confidence": confidence,
                    "matched_hoax": top_match.get("content"),
                    "similarity": round(similarity, 2),
                    "summary_one_liner": f"Matched known '{verdict.lower()}' pattern in hoax vector store.",
                    "tl_dr_bullets": [
                        "Direct semantic similarity with known hoax data",
                        f"Similarity score: {int(similarity * 100)}%",
                        f"Category: {top_match.get('category', 'General')}"
                    ],
                    "evidence": [{"type": "similarity_match", "score": similarity}],
                    "reasons": [f"Direct match in local vector store (Similarity: {similarity:.0%})"],
                    "reason_codes": list(set(reason_codes + ["matched_database"])),
                    "low_confidence": confidence < 60,
                    "deep_analysis_recommended": confidence < 65
                }
                self._cache_set(cache_key, result)
                return result

        fact_result, news_result, gnews_result = await asyncio.gather(
            self._safe_provider_call(
                "fact_check",
                lambda: asyncio.wait_for(self.fact_check.get_verdict(primary_claim), timeout=4.5),
                reason_codes
            ),
            self._safe_provider_call(
                "news_api",
                lambda: asyncio.wait_for(self.news_api.verify_claim_with_news(primary_claim), timeout=4.5),
                reason_codes
            ),
            self._safe_provider_call(
                "gnews_api",
                lambda: asyncio.wait_for(self.gnews_api.verify_claim_with_news(primary_claim), timeout=4.5),
                reason_codes
            )
        )

        trusted_news_hits = 0
        top_articles: List[str] = []
        news_verdicts = []
        for item in [news_result, gnews_result]:
            if item and item.get("found_in_news"):
                trusted_news_hits += int(item.get("credible_sources", 0))
                news_verdicts.append(item.get("verdict", "MIXED"))
                top_articles.extend(item.get("top_articles", []))

        if fact_result and fact_result.get("found") and fact_result.get("verdict") != "UNKNOWN":
            verdict = str(fact_result.get("verdict"))
            confidence = self._calibrate_confidence(
                verdict=verdict,
                base_confidence=int(fact_result.get("confidence", 50)),
                similarity=similarity,
                trusted_news_hits=trusted_news_hits,
                ai_only=False
            )
            result = {
                "verdict": verdict,
                "confidence": confidence,
                "matched_hoax": None,
                "similarity": round(similarity, 2),
                "summary_one_liner": f"Verified via Google Fact Check ({verdict}).",
                "tl_dr_bullets": [
                    "Matched against Google Fact Check claims",
                    f"Sources: {', '.join(fact_result.get('sources', [])[:2]) or 'N/A'}",
                    f"Trusted news support score: {trusted_news_hits}"
                ],
                "evidence": [{"type": "fact_check", "sources": fact_result.get("sources")}],
                "reasons": [f"Fact-check consensus: {verdict}"],
                "reason_codes": list(set(reason_codes + ["factcheck_hit"])),
                "low_confidence": confidence < 60,
                "deep_analysis_recommended": confidence < 65
            }
            self._cache_set(cache_key, result)
            return result

        if trusted_news_hits > 0:
            verdict = "VERIFIED" if trusted_news_hits >= 3 else "MIXED"
            if news_verdicts.count("SUSPECT") >= 1 and trusted_news_hits < 2:
                verdict = "SUSPECT"
            confidence = self._calibrate_confidence(
                verdict=verdict,
                base_confidence=min(88, 45 + trusted_news_hits * 12),
                similarity=similarity,
                trusted_news_hits=trusted_news_hits,
                ai_only=False
            )
            result = {
                "verdict": verdict,
                "confidence": confidence,
                "matched_hoax": None,
                "similarity": round(similarity, 2),
                "summary_one_liner": "Cross-referenced with recent news coverage.",
                "tl_dr_bullets": [
                    f"Trusted-source hits across NewsAPI/GNews: {trusted_news_hits}",
                    f"Related articles found: {len(top_articles)}",
                    "Confidence adjusted by source credibility weighting"
                ],
                "evidence": [{"type": "news_check", "articles": top_articles[:3]}],
                "reasons": ["Detected in recent trusted news cycle"],
                "reason_codes": list(set(reason_codes + ["news_consensus"])),
                "low_confidence": confidence < 60,
                "deep_analysis_recommended": confidence < 65
            }
            self._cache_set(cache_key, result)
            return result

        if claims and "preliminary_verdict" in claims[0]:
            prelim = claims[0]
            verdict = str(prelim.get("preliminary_verdict", "SUSPECT")).upper()
            confidence = self._calibrate_confidence(
                verdict=verdict,
                base_confidence=58 if verdict != "SUSPECT" else 50,
                similarity=similarity,
                trusted_news_hits=trusted_news_hits,
                ai_only=True
            )
            result = {
                "verdict": verdict if verdict in {"FAKE", "VERIFIED", "SUSPECT", "MIXED"} else "SUSPECT",
                "confidence": confidence,
                "matched_hoax": None,
                "similarity": round(similarity, 2),
                "summary_one_liner": f"AI preliminary assessment: {verdict}",
                "tl_dr_bullets": [
                    prelim.get("preliminary_reasoning", "Speculative claim detected"),
                    "No strong public-database match found",
                    "Confidence capped for AI-only verdict"
                ],
                "evidence": [{"type": "ai_assessment", "reasoning": prelim.get("preliminary_reasoning")}],
                "reasons": ["AI preliminary claim evaluation"],
                "reason_codes": list(set(reason_codes + ["ai_preliminary_only", "low_confidence"])),
                "low_confidence": True,
                "deep_analysis_recommended": True
            }
            self._cache_set(cache_key, result)
            return result

        result = {
            "verdict": "MIXED",
            "confidence": 40,
            "matched_hoax": None,
            "similarity": round(similarity, 2),
            "summary_one_liner": "No rapid conclusive evidence found.",
            "tl_dr_bullets": [
                "No direct hoax-vector match above confidence threshold",
                "No strong fact-check or trusted-news consensus",
                "Run deep analysis for stronger multi-agent verification"
            ],
            "evidence": [],
            "reasons": ["Inconclusive rapid scan"],
            "reason_codes": list(set(reason_codes + ["inconclusive_scan", "low_confidence"])),
            "low_confidence": True,
            "deep_analysis_recommended": True
        }
        self._cache_set(cache_key, result)
        return result

    async def analyze_image(self, image_data: str) -> Dict:
        if self.forensics is None:
            from app.core.forensics import get_forensics

            self.forensics = get_forensics()
        forensics_result = await asyncio.to_thread(self.forensics.analyze_image, image_data)

        verdict = forensics_result.get("verdict", "UNKNOWN")
        manipulation_score = forensics_result.get("manipulation_score", 0.0)

        verdict_map = {
            "MANIPULATED": "FAKE",
            "AUTHENTIC": "VERIFIED",
            "SUSPECT": "SUSPECT",
            "UNKNOWN": "MIXED"
        }
        verdict = verdict_map.get(verdict, "MIXED")
        confidence = int(manipulation_score * 100) if verdict == "FAKE" else 85 if verdict == "VERIFIED" else 50

        return {
            "verdict": verdict,
            "confidence": confidence,
            "summary_one_liner": f"{verdict}: Image forensics analysis completed",
            "tl_dr_bullets": ["Digital manipulation check", f"Manipulation Score: {manipulation_score:.0%}"],
            "evidence": [{"type": "image_forensics", "manipulation_score": manipulation_score}],
            "reasons": ["Forensics checks completed"],
            "reason_codes": ["image_forensics"],
            "low_confidence": confidence < 60,
            "deep_analysis_recommended": confidence < 65
        }

# Global instance
_quick_analyzer = None

def get_quick_analyzer():
    global _quick_analyzer
    if _quick_analyzer is None:
        _quick_analyzer = QuickAnalyzer()
    return _quick_analyzer
