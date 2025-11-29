"""
Quick Analysis Agent - Fast misinformation checker using embeddings
Provides rapid analysis with verdict, confidence, and brief summary
"""
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from langchain_core.tools import Tool
from app.core.llm import get_llm
from app.core.embeddings import get_embeddings_manager
from app.core.forensics import get_forensics
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class QuickAnalyzer:
    """Fast analysis using similarity search and forensics"""
    
    def __init__(self):
        self.llm = get_llm(temperature=0.2)
        self.embeddings = get_embeddings_manager()
        self.forensics = get_forensics()
    
    def analyze_text(self, text: str) -> Dict:
        """Quick text analysis using similarity search"""
        # Search for similar known hoaxes
        similar_hoaxes = self.embeddings.search_similar(text, k=3, threshold=0.7)
        
        # Determine verdict based on similarity
        if similar_hoaxes:
            top_match = similar_hoaxes[0]
            confidence = int(top_match["similarity"] * 100)
            verdict = top_match["match"].get("verdict", "SUSPECT")
            
            evidence = [{
                "type": "similarity_match",
                "score": top_match["similarity"],
                "matched_text": top_match["match"]["text"],
                "category": top_match["match"].get("category", "unknown")
            }]
            
            reasons = [
                f"High similarity ({confidence}%) to known {verdict.lower()} claim",
                f"Matches debunked content in category: {evidence[0]['category']}"
            ]
        else:
            # No strong matches - needs verification
            confidence = 50
            verdict = "MIXED"
            evidence = []
            reasons = ["No clear matches to known hoaxes or verified claims"]
        
        # Generate summary using LLM
        summary = self._generate_summary(text, verdict, similar_hoaxes)
        
        return {
            "verdict": verdict,
            "confidence": confidence,
            "summary_one_liner": summary["one_liner"],
            "tl_dr_bullets": summary["bullets"],
            "evidence": evidence,
            "reasons": reasons
        }
    
    def analyze_image(self, image_data: str) -> Dict:
        """Quick image analysis using forensics"""
        forensics_result = self.forensics.analyze_image(image_data)
        
        # Determine verdict from forensics
        verdict = forensics_result.get("verdict", "UNKNOWN")
        manipulation_score = forensics_result.get("manipulation_score", 0.0)
        
        # Map verdict to standardized format
        verdict_map = {
            "MANIPULATED": "FAKE",
            "AUTHENTIC": "VERIFIED",
            "SUSPECT": "SUSPECT",
            "UNKNOWN": "MIXED"
        }
        verdict = verdict_map.get(verdict, "MIXED")
        
        # Calculate confidence
        if verdict == "FAKE":
            confidence = int(manipulation_score * 100)
        elif verdict == "VERIFIED":
            confidence = 85
        else:
            confidence = 50
        
        # Build evidence
        evidence = [{
            "type": "image_forensics",
            "exif_data": forensics_result.get("exif", {}),
            "hashes": forensics_result.get("hashes", {}),
            "manipulation_score": manipulation_score
        }]
        
        # Build reasons
        reasons = []
        metadata_flags = forensics_result.get("metadata_flags", {})
        if metadata_flags.get("missing_exif"):
            reasons.append("No EXIF metadata found (suspicious)")
        if metadata_flags.get("edited_software"):
            reasons.append("Image shows signs of editing software")
        if manipulation_score > 0.5:
            reasons.append(f"High manipulation score: {manipulation_score:.0%}")
        if not reasons:
            reasons.append("Basic forensics checks passed")
        
        # Generate summary
        summary = self._generate_image_summary(verdict, forensics_result)
        
        return {
            "verdict": verdict,
            "confidence": confidence,
            "summary_one_liner": summary["one_liner"],
            "tl_dr_bullets": summary["bullets"],
            "evidence": evidence,
            "reasons": reasons
        }
    
    def _generate_summary(self, text: str, verdict: str, matches: list) -> Dict:
        """Generate concise summary using LLM"""
        try:
            prompt = f"""Analyze this claim and provide a brief summary.

Claim: "{text[:200]}"
Verdict: {verdict}
Similar known claims: {len(matches)}

Provide:
1. One-liner summary (max 100 chars)
2. Three bullet points explaining the verdict

Be concise and factual."""
            
            response = self.llm.invoke(prompt)
            
            # Parse response (simplified - in production, use structured output)
            lines = response.content.strip().split('\n')
            one_liner = lines[0] if lines else "Analysis pending"
            bullets = [line.strip('- •').strip() for line in lines[1:4] if line.strip()]
            
            return {
                "one_liner": one_liner[:150],
                "bullets": bullets[:3] if bullets else ["No additional details"]
            }
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                "one_liner": f"{verdict}: Claim requires verification",
                "bullets": ["Analysis completed", "Review evidence for details", "Manual verification recommended"]
            }
    
    def _generate_image_summary(self, verdict: str, forensics: Dict) -> Dict:
        """Generate summary for image analysis"""
        has_exif = forensics.get("exif", {}).get("has_exif", False)
        manipulation_score = forensics.get("manipulation_score", 0.0)
        
        one_liner = f"{verdict}: Image forensics analysis completed"
        
        bullets = []
        if manipulation_score > 0.7:
            bullets.append("High likelihood of digital manipulation detected")
        elif manipulation_score > 0.3:
            bullets.append("Some manipulation indicators present")
        else:
            bullets.append("No clear manipulation detected")
        
        if has_exif:
            bullets.append ("EXIF metadata present and analyzed")
        else:
            bullets.append("No EXIF metadata found")
        
        bullets.append(f"Forensics confidence: {int(manipulation_score * 100)}%")
        
        return {
            "one_liner": one_liner,
            "bullets": bullets[:3]
        }

# Global instance
_quick_analyzer = None

def get_quick_analyzer():
    """Get or create global quick analyzer instance"""
    global _quick_analyzer
    if _quick_analyzer is None:
        _quick_analyzer = QuickAnalyzer()
    return _quick_analyzer
