"""
Unified JSON Storage - Single file with different data classes
All data stored in one JSON file with organized structure
Cross-platform file locking (Windows compatible)
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging
import threading

logger = logging.getLogger(__name__)

# Thread-safe file lock using threading.Lock instead of fcntl (cross-platform)
_file_lock = threading.Lock()

class UnifiedJSONStorage:
    """Single JSON file storage with organized data classes"""
    
    def __init__(self, data_file: str = "data/truthscan_data.json"):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(exist_ok=True)
        
        # Initialize unified data structure
        self.data_structure = {
            "analyses": [],
            "feedback": [],
            "users": [],
            "known_hoaxes": [],
            "statistics": {
                "total_analyses": 0,
                "total_feedback": 0,
                "last_updated": None
            }
        }
        
        self._init_file()
    
    def _init_file(self):
        """Initialize JSON file if it doesn't exist"""
        if not self.data_file.exists():
            self._write_data(self.data_structure)
    
    def _read_data(self) -> Dict:
        """Read entire JSON file with thread lock"""
        with _file_lock:
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
            except Exception as e:
                logger.error(f"Error reading data file: {e}")
                return self.data_structure.copy()
    
    def _write_data(self, data: Dict):
        """Write entire JSON file with thread lock"""
        with _file_lock:
            try:
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Error writing data file: {e}")
    
    # ========== ANALYSES ==========
    def save_analysis(self, analysis: Dict) -> str:
        """Save analysis result"""
        data = self._read_data()
        
        timestamp = datetime.utcnow().isoformat()
        analysis_id = f"analysis_{timestamp.replace(':', '').replace('.', '_')}"
        
        record = {
            "id": analysis_id,
            "timestamp": timestamp,
            **analysis
        }
        
        data["analyses"].append(record)
        data["statistics"]["total_analyses"] = len(data["analyses"])
        data["statistics"]["last_updated"] = timestamp
        
        self._write_data(data)
        logger.info(f"Saved analysis: {analysis_id}")
        return analysis_id
    
    def get_recent_analyses(self, limit: int = 10) -> List[Dict]:
        """Get most recent analyses"""
        data = self._read_data()
        analyses = sorted(
            data.get("analyses", []), 
            key=lambda x: x.get("timestamp", ""), 
            reverse=True
        )
        return analyses[:limit]
    
    def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict]:
        """Get specific analysis by ID"""
        data = self._read_data()
        for analysis in data.get("analyses", []):
            if analysis.get("id") == analysis_id:
                return analysis
        return None
    
    # ========== FEEDBACK ==========
    def save_feedback(self, feedback: Dict) -> str:
        """Save user feedback"""
        data = self._read_data()
        
        timestamp = datetime.utcnow().isoformat()
        feedback_id = f"fb_{timestamp.replace(':', '').replace('.', '_')}"
        
        record = {
            "id": feedback_id,
            "timestamp": timestamp,
            **feedback
        }
        
        data["feedback"].append(record)
        data["statistics"]["total_feedback"] = len(data["feedback"])
        data["statistics"]["last_updated"] = timestamp
        
        self._write_data(data)
        logger.info(f"Saved feedback: {feedback_id}")
        return feedback_id
    
    def get_all_feedback(self) -> List[Dict]:
        """Get all feedback"""
        data = self._read_data()
        return data.get("feedback", [])
    
    # ========== KNOWN HOAXES ==========
    def add_known_hoax(self, hoax: Dict) -> str:
        """Add a known hoax to the database"""
        data = self._read_data()
        
        timestamp = datetime.utcnow().isoformat()
        hoax_id = f"hoax_{timestamp.replace(':', '').replace('.', '_')}"
        
        record = {
            "id": hoax_id,
            "timestamp": timestamp,
            **hoax
        }
        
        data["known_hoaxes"].append(record)
        data["statistics"]["last_updated"] = timestamp
        
        self._write_data(data)
        logger.info(f"Added known hoax: {hoax_id}")
        return hoax_id
    
    def get_known_hoaxes(self) -> List[Dict]:
        """Get all known hoaxes"""
        data = self._read_data()
        return data.get("known_hoaxes", [])
    
    # ========== USERS (for future use) ==========
    def save_user(self, user: Dict) -> str:
        """Save user data"""
        data = self._read_data()
        
        timestamp = datetime.utcnow().isoformat()
        user_id = user.get("id") or f"user_{timestamp.replace(':', '').replace('.', '_')}"
        
        # Check if user exists
        user_index = next((i for i, u in enumerate(data["users"]) if u.get("id") == user_id), None)
        
        record = {
            "id": user_id,
            "last_updated": timestamp,
            **user
        }
        
        if user_index is not None:
            data["users"][user_index] = record
        else:
            data["users"].append(record)
        
        data["statistics"]["last_updated"] = timestamp
        self._write_data(data)
        return user_id
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        data = self._read_data()
        for user in data.get("users", []):
            if user.get("id") == user_id:
                return user
        return None
    
    # ========== STATISTICS ==========
    def get_stats(self) -> Dict:
        """Get storage statistics"""
        data = self._read_data()
        stats = data.get("statistics", {})
        
        # Add detailed stats
        stats["total_analyses"] = len(data.get("analyses", []))
        stats["total_feedback"] = len(data.get("feedback", []))
        stats["total_known_hoaxes"] = len(data.get("known_hoaxes", []))
        stats["total_users"] = len(data.get("users", []))
        stats["storage_file"] = str(self.data_file)
        
        return stats
    
    def clear_all_data(self, confirm: bool = False):
        """DANGEROUS: Clear all data (use with caution)"""
        if not confirm:
            raise ValueError("Must confirm data clearing with confirm=True")
        
        logger.warning("CLEARING ALL DATA!")
        self._write_data(self.data_structure)

# Global instance
_unified_storage = None

def get_unified_storage():
    """Get or create global unified storage instance"""
    global _unified_storage
    if _unified_storage is None:
        _unified_storage = UnifiedJSONStorage()
    return _unified_storage

# Backward compatibility aliases
def get_storage():
    """Alias for get_unified_storage"""
    return get_unified_storage()
