import logging
import asyncio
from typing import List, Dict, Optional
import httpx
from newsapi import NewsApiClient
import google.generativeai as genai
from openai import AsyncOpenAI
import json

from app.core.config import settings

logger = logging.getLogger(__name__)

class GoogleFactCheckAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

    async def search_claims(self, query: str, language: str = "en") -> List[Dict]:
        if not self.api_key:
            logger.warning("Google FactCheck API Key missing. Returning empty claims.")
            return []
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.base_url,
                    params={
                        "query": query,
                        "languageCode": language,
                        "key": self.api_key
                    },
                    timeout=5.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("claims", [])
            except Exception as e:
                logger.error(f"Error calling Google FactCheck API: {e}")
                return []

    async def get_verdict(self, query: str) -> Dict:
        claims = await self.search_claims(query)
        if not claims:
            return {"found": False, "verdict": "UNKNOWN", "confidence": 0, "sources": []}
            
        ratings_mapping = {
            "false": "FAKE",
            "pants on fire": "FAKE",
            "mostly false": "FAKE",
            "falso": "FAKE",
            "untrue": "FAKE",
            "fake": "FAKE",
            "true": "VERIFIED",
            "mostly true": "VERIFIED",
            "verda": "VERIFIED",
            "correct": "VERIFIED",
            "mixed": "MIXED",
            "half true": "MIXED",
            "partially true": "MIXED",
            "disputed": "MIXED",
        }
        
        verdicts = []
        sources = []
        
        for claim in claims:
            review = claim.get("claimReview", [])
            if review:
                rating = review[0].get("textualRating", "").lower()
                publisher = review[0].get("publisher", {}).get("name", "Unknown")
                sources.append(publisher)
                normalized = ratings_mapping.get(rating, "UNKNOWN")
                if normalized != "UNKNOWN":
                    verdicts.append(normalized)

        if not verdicts:
            return {"found": True, "verdict": "UNKNOWN", "confidence": 0, "sources": sources}
            
        # Consensus
        fake_count = verdicts.count("FAKE")
        verified_count = verdicts.count("VERIFIED")
        mixed_count = verdicts.count("MIXED")
        
        total = len(verdicts)
        if fake_count > verified_count and fake_count > mixed_count:
            return {"found": True, "verdict": "FAKE", "confidence": int((fake_count/total)*100), "sources": list(set(sources))}
        elif verified_count > fake_count and verified_count > mixed_count:
            return {"found": True, "verdict": "VERIFIED", "confidence": int((verified_count/total)*100), "sources": list(set(sources))}
        else:
            return {"found": True, "verdict": "MIXED", "confidence": int(max(mixed_count, fake_count, verified_count)/total*100), "sources": list(set(sources))}


class ClaimDetector:
    def __init__(self):
        self.model = None
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel("gemini-2.5-flash")

    async def _extract_claims_with_openai(self, text: str) -> Optional[Dict]:
        if not self.openai_client:
            return None
        prompt = """Extract verifiable factual claims only. Ignore opinions.
Return strict JSON with this format:
{
  "has_claims": true,
  "claims": [
    {
      "text": "...",
      "check_worthiness_score": 0.0,
      "category": "general",
      "preliminary_verdict": "FAKE" | "VERIFIED" | "SUSPECT",
      "preliminary_reasoning": "..."
    }
  ]
}"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.2
            )
            content = (response.choices[0].message.content or "").strip()
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "claims" in parsed:
                return parsed
        except Exception as error:
            logger.error("OpenAI fallback claim extraction failed: %s", error)
        return None

    async def extract_claims(self, text: str) -> Dict:
        """Extract verifiable factual claims using Gemini."""
        if not self.model:
            logger.warning("No Gemini key. Using dummy fallback.")
            return {"has_claims": True, "claims": [{"text": text, "check_worthiness_score": 1.0, "category": "general"}]}

        system_prompt = """Extract verifiable factual claims only. Ignore opinions. 
Also provide a preliminary AI assessment of the claim's likelihood based on known world facts (as of your training).

Return strictly in JSON format:
{
  "has_claims": true,
  "claims": [
    {
      "text": "...",
      "check_worthiness_score": 0.9,
      "category": "science",
      "preliminary_verdict": "FAKE" | "VERIFIED" | "SUSPECT",
      "preliminary_reasoning": "..."
    }
  ]
}"""
        try:
            res = await self.model.generate_content_async(system_prompt + "\n\n" + text)
            text_resp = res.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text_resp)
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                logger.error("Gemini quota exhausted; switching to OpenAI fallback.")
                openai_fallback = await self._extract_claims_with_openai(text)
                if openai_fallback:
                    return openai_fallback
                return {
                    "has_claims": True, 
                    "claims": [{
                        "text": text, 
                        "check_worthiness_score": 0.5, 
                        "category": "unknown",
                        "preliminary_verdict": "SUSPECT",
                        "preliminary_reasoning": "AI Quota reached. Please wait 60s and try again."
                    }]
                }
            logger.error(f"Error in ClaimDetector: {e}")
            return {"has_claims": True, "claims": [{"text": text, "check_worthiness_score": 0.8, "category": "unknown"}]}


class NewsAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = NewsApiClient(api_key=api_key) if api_key else None
        self.credible_sources = ["bbc-news", "reuters", "associated-press", "the-new-york-times", "the-guardian-uk"]

    async def search_news(self, query: str, days_back: int = 7) -> Dict:
        if not self.client:
            return {"status": "error", "message": "NewsAPI not configured"}
            
        try:
            res = await asyncio.to_thread(
                lambda: self.client.get_everything(
                    q=query,
                    language='en',
                    sort_by='relevancy',
                    page_size=20
                )
            )
            return res
        except Exception as e:
            logger.error(f"Error searching news: {e}")
            return {"status": "error", "message": str(e)}

    async def verify_claim_with_news(self, claim: str) -> Dict:
        news_results = await self.search_news(claim)
        if news_results.get("status") != "ok":
            return {"found_in_news": False, "verdict": "UNKNOWN", "confidence": 0}

        articles = news_results.get("articles", [])
        if not articles:
             return {"found_in_news": False, "total_articles": 0, "credible_sources": 0, "confidence": 0, "verdict": "UNKNOWN", "top_articles": []}

        credible_count = 0
        top_articles = []
        for article in articles:
            source_id = article.get("source", {}).get("id")
            if source_id in self.credible_sources:
                credible_count += 1
            if len(top_articles) < 3:
                top_articles.append(article.get("title"))

        verdict = "VERIFIED" if credible_count >= 2 else "MIXED"
        confidence = min(100, credible_count * 25)

        return {
            "found_in_news": True,
            "total_articles": len(articles),
            "credible_sources": credible_count,
            "confidence": confidence,
            "verdict": verdict,
            "top_articles": top_articles
        }


class GNewsClient:
    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key
        self.base_url = "https://gnews.io/api/v4/search"
        # Domain fragments for source credibility weighting.
        self.credible_domains = {
             # 🌐 Global / Wire Services
            "reuters.com",
            "apnews.com",
            "afp.com",
            "bloomberg.com",
            "nytimes.com",
            "washingtonpost.com",
            "wsj.com",
            "latimes.com",
            "npr.org",
            "usatoday.com",
            "bbc.com",
            "theguardian.com",
            "ft.com",
            "economist.com",
            "independent.co.uk",
            "thehindu.com",
            "indianexpress.com",
            "ndtv.com",
            "hindustantimes.com",
            "scroll.in",
            "thewire.in",
            "newslaundry.com",

    # 🇪🇺 Europe
            "dw.com",
            "france24.com",
            "euronews.com",
            "elpais.com",

    # 🔍 Fact-checking orgs (VERY IMPORTANT)
            "snopes.com",
            "factcheck.org",
            "politifact.com",
            "altnews.in",
            "boomlive.in"
        }

    def _is_credible_url(self, url: str) -> bool:
        if not url:
            return False
        return any(domain in url for domain in self.credible_domains)

    async def verify_claim_with_news(self, claim: str) -> Dict:
        if not self.api_key:
            return {"found_in_news": False, "verdict": "UNKNOWN", "confidence": 0, "source": "gnews"}

        params = {
            "q": claim,
            "lang": "en",
            "max": 10,
            "token": self.api_key
        }
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception as error:
            logger.error("Error calling GNews API: %s", error)
            return {
                "found_in_news": False,
                "verdict": "UNKNOWN",
                "confidence": 0,
                "source": "gnews",
                "error": str(error)
            }

        articles = payload.get("articles", [])
        if not articles:
            return {"found_in_news": False, "verdict": "UNKNOWN", "confidence": 0, "source": "gnews"}

        credible_sources = sum(1 for article in articles if self._is_credible_url(article.get("url", "")))
        total = len(articles)
        confidence = min(95, int(((credible_sources / total) * 100) if total else 0))
        top_articles = [a.get("title") for a in articles[:3] if a.get("title")]

        if credible_sources >= 3:
            verdict = "VERIFIED"
        elif credible_sources == 0:
            verdict = "MIXED"
        else:
            verdict = "SUSPECT"

        return {
            "found_in_news": True,
            "source": "gnews",
            "verdict": verdict,
            "confidence": confidence,
            "credible_sources": credible_sources,
            "total_articles": total,
            "top_articles": top_articles
        }

class EnsembleAnalyzer:
    def __init__(self):
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.gemini = genai.GenerativeModel("gemini-2.5-flash")
        else:
            self.gemini = None
        self.gpt = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

    async def _analyze(self, model, text: str, name: str) -> Dict:
        if not model:
             return {"model": name, "verdict": "UNKNOWN", "confidence": 0}
        prompt = f"Analyze the following claim and return strictly JSON without markdown blocks with: verdict (FAKE, VERIFIED, MIXED) and confidence (0-100).\nClaim: {text}"
        try:
            if name == "Gemini":
                res = await model.generate_content_async(prompt)
                content = res.text.replace("```json", "").replace("```", "").strip()
            else:
                # OpenAI path
                res = await model.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}]
                )
                content = res.choices[0].message.content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            return {"model": name, "verdict": data.get("verdict", "UNKNOWN"), "confidence": data.get("confidence", 0)}
        except Exception as e:
            logger.error(f"Error in {name} analysis: {e}")
            return {"model": name, "verdict": "UNKNOWN", "confidence": 0}

    async def analyze_with_gemini(self, text: str) -> Dict:
        return await self._analyze(self.gemini, text, "Gemini")

    async def analyze_with_gpt(self, text: str) -> Dict:
        return await self._analyze(self.gpt, text, "GPT-3.5")

    async def analyze_with_huggingface(self, text: str) -> Dict:
        from app.core.huggingface import hf_client, MODELS
        try:
            # Using evidence-types model as a proxy for verification
            res = await hf_client.query(MODELS["text_detection"], {"inputs": text[:500]})
            if isinstance(res, list) and len(res) > 0:
                scores = res[0]
                top = sorted(scores, key=lambda x: x['score'], reverse=True)[0]
                # Map detection labels to verdicts loosely if appropriate, 
                # but for now we'll just check if it's AI or deepfake related
                return {"model": "HuggingFace", "verdict": "SUSPECT", "confidence": int(top['score']*100)}
            return {"model": "HuggingFace", "verdict": "UNKNOWN", "confidence": 0}
        except Exception:
            return {"model": "HuggingFace", "verdict": "UNKNOWN", "confidence": 0}

    async def ensemble_verdict(self, text: str) -> Dict:
        results = await asyncio.gather(
            self.analyze_with_gemini(text),
            self.analyze_with_gpt(text),
            self.analyze_with_huggingface(text),
            return_exceptions=True
        )

        valid_results = [r for r in results if isinstance(r, dict) and r["verdict"] != "UNKNOWN"]
        
        if not valid_results:
            return {"verdict": "UNKNOWN", "confidence": 0, "vote_distribution": {}, "model_results": []}

        # Weights: Gemini 0.4, GPT 0.35, HF 0.25
        weights = {"Gemini": 0.4, "GPT-3.5": 0.35, "HuggingFace": 0.25}
        
        votes = {"FAKE": 0.0, "VERIFIED": 0.0, "MIXED": 0.0}
        total_weight = 0.0
        
        for r in valid_results:
            w = weights.get(r["model"], 0.33)
            verdict = r.get("verdict", "UNKNOWN")
            if verdict in votes:
                votes[verdict] += w
                total_weight += w

        if total_weight == 0:
            return {"verdict": "UNKNOWN", "confidence": 0, "vote_distribution": {}, "model_results": valid_results}

        # Normalize votes
        distribution = {k: v / total_weight for k, v in votes.items()}
        final_verdict = max(distribution, key=distribution.get)
        confidence = distribution[final_verdict] * 100

        return {
            "verdict": final_verdict,
            "confidence": int(confidence),
            "vote_distribution": distribution,
            "model_results": valid_results
        }
