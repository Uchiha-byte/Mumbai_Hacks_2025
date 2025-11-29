"""
Image Forensics - Enhanced image analysis tools
Provides EXIF extraction, perceptual hashing, and manipulation detection
"""
import imagehash
from PIL import Image
import exifread
import io
import base64
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ImageForensics:
    """Advanced image forensics analysis"""
    
    def __init__(self):
        self.known_hashes = {}  # Store of known manipulated image hashes
        self._load_known_hashes()
    
    def _load_known_hashes(self):
        """Load database of known manipulated images (placeholder for now)"""
        # In production, load from database
        self.known_hashes = {
            # Example: "hash_value": {"description": "Known deepfake", "source": "..."}
        }
    
    def analyze_image(self, image_data: str) -> Dict:
        """
        Comprehensive image analysis
        
        Args:
            image_data: Base64 data URL or raw base64 string
        
        Returns:
            Dictionary with forensics results
        """
        try:
            # Clean base64 data
            if "," in image_data:
                image_data = image_data.split(",")[1]
            
            image_bytes = base64.b64decode(image_data)
            
            # Run all forensics checks
            exif_data = self._extract_exif(image_bytes)
            hash_info = self._compute_hashes(image_bytes)
            manipulation_check = self._check_manipulation(hash_info)
            metadata_analysis = self._analyze_metadata(exif_data)
            
            return {
                "exif": exif_data,
                "hashes": hash_info,
                "manipulation_detected": manipulation_check["detected"],
                "manipulation_score": manipulation_check["score"],
                "metadata_flags": metadata_analysis,
                "verdict": self._determine_verdict(exif_data, manipulation_check)
            }
        except Exception as e:
            logger.error(f"Error in image forensics: {e}")
            return {
                "error": str(e),
                "verdict": "UNKNOWN"
            }
    
    def _extract_exif(self, image_bytes: bytes) -> Dict:
        """Extract EXIF metadata from image"""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            
            # Basic PIL metadata
            basic_info = {
                "format": img.format,
                "size": img.size,
                "mode": img.mode,
                "has_exif": False
            }
            
            # Try to extract detailed EXIF with exifread
            try:
                tags = exifread.process_file(io.BytesIO(image_bytes), details=False)
                if tags:
                    basic_info["has_exif"] = True
                    basic_info["camera"] = str(tags.get('Image Model', 'Unknown'))
                    basic_info["software"] = str(tags.get('Image Software', 'None'))
                    basic_info["datetime"] = str(tags.get('EXIF DateTimeOriginal', 'Unknown'))
                else:
                    basic_info["camera"] = None
                    basic_info["software"] = None
            except Exception as e:
                logger.debug(f"Could not extract detailed EXIF: {e}")
            
            return basic_info
        except Exception as e:
            logger.error(f"Error extracting EXIF: {e}")
            return {"error": str(e)}
    
    def _compute_hashes(self, image_bytes: bytes) -> Dict:
        """Compute perceptual hashes for image"""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            
            return {
                "average_hash": str(imagehash.average_hash(img)),
                "perceptual_hash": str(imagehash.phash(img)),
                "difference_hash": str(imagehash.dhash(img)),
                "wavelet_hash": str(imagehash.whash(img))
            }
        except Exception as e:
            logger.error(f"Error computing hashes: {e}")
            return {}
    
    def _check_manipulation(self, hash_info: Dict) -> Dict:
        """Check if image matches known manipulated images"""
        # Placeholder - in production, compare against database
        # For now, return basic analysis
        
        score = 0.0
        detected = False
        matches = []
        
        # Check against known manipulated hashes
        for hash_type in ["perceptual_hash", "average_hash"]:
            if hash_type in hash_info:
                img_hash = hash_info[hash_type]
                if img_hash in self.known_hashes:
                    detected = True
                    score = 0.95
                    matches.append(self.known_hashes[img_hash])
        
        return {
            "detected": detected,
            "score": score,
            "matches": matches
        }
    
    def _analyze_metadata(self, exif_data: Dict) -> Dict:
        """Analyze metadata for suspicious patterns"""
        flags = {
            "missing_exif": not exif_data.get("has_exif", False),
            "edited_software": False,
            "suspicious_camera": False
        }
        
        # Check for editing software
        software = exif_data.get("software", "").lower()
        editing_tools = ["photoshop", "gimp", "paint.net", "pixlr"]
        if any(tool in software for tool in editing_tools):
            flags["edited_software"] = True
        
        return flags
    
    def _determine_verdict(self, exif_data: Dict, manipulation_check: Dict) -> str:
        """Determine overall verdict based on forensics"""
        if manipulation_check["detected"]:
            return "MANIPULATED"
        elif exif_data.get("has_exif") and not manipulation_check["detected"]:
            return "AUTHENTIC"
        else:
            return "SUSPECT"  # Missing EXIF but no clear manipulation

# Global instance
_forensics = None

def get_forensics():
    """Get or create global forensics instance"""
    global _forensics
    if _forensics is None:
        _forensics = ImageForensics()
    return _forensics
