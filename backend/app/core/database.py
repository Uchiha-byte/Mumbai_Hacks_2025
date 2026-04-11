import logging
from typing import Dict, List, Optional
from supabase import create_client, Client
from app.core.config import settings
import asyncio

logger = logging.getLogger(__name__)

class SupabaseDB:
    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            logger.warning("Supabase URL or Key is not set in environment variables.")
            self.client: Optional[Client] = None
        else:
            self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
            
    async def save_analysis(self, data: Dict) -> Optional[Dict]:
        if not self.client: return None
        try:
            res = await asyncio.to_thread(
                lambda: self.client.table("analyses").insert(data).execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            return None

    async def save_feedback(self, data: Dict) -> Optional[Dict]:
        if not self.client: return None
        try:
            res = await asyncio.to_thread(
                lambda: self.client.table("feedback").insert(data).execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            return None

    async def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict]:
        if not self.client: return None
        try:
            res = await asyncio.to_thread(
                lambda: self.client.table("analyses").select("*").eq("id", analysis_id).execute()
            )
            data = res.data
            return data[0] if data else None
        except Exception as e:
            logger.error(f"Error getting analysis: {e}")
            return None

    async def search_similar_hoaxes(self, embedding_vector: List[float], threshold: float = 0.8, count: int = 5) -> List[Dict]:
        if not self.client: return []
        try:
            res = await asyncio.to_thread(
                lambda: self.client.rpc(
                    "match_hoaxes",
                    {"query_embedding": embedding_vector, "match_threshold": threshold, "match_count": count}
                ).execute()
            )
            return res.data or []
        except Exception as e:
            logger.error(f"Error searching similar hoaxes: {e}")
            return []

    async def add_known_hoax(self, data: Dict) -> Optional[Dict]:
        if not self.client: return None
        try:
            res = await asyncio.to_thread(
                lambda: self.client.table("known_hoaxes").insert(data).execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error adding known hoax: {e}")
            return None
            
    async def get_stats(self) -> Dict:
        if not self.client: return {}
        try:
            analyses_count = await asyncio.to_thread(lambda: self.client.table("analyses").select("id", count="exact").execute())
            feedback_count = await asyncio.to_thread(lambda: self.client.table("feedback").select("id", count="exact").execute())
            hoaxes_count = await asyncio.to_thread(lambda: self.client.table("known_hoaxes").select("id", count="exact").execute())
            
            return {
                "total_analyses": analyses_count.count if analyses_count else 0,
                "total_feedback": feedback_count.count if feedback_count else 0,
                "total_known_hoaxes": hoaxes_count.count if hoaxes_count else 0
            }
        except Exception as e:
            logger.error(f"Error getting DB stats: {e}")
            return {}

# Global instance
supabase_db = SupabaseDB()

def get_db():
    """Returns the global SupabaseDB manager."""
    return supabase_db
