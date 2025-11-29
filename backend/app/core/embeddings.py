"""
Embeddings Manager - Fast similarity search using FAISS
Provides quick matching against known hoaxes and misinformation patterns
"""
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class EmbeddingsManager:
    """Manages text embeddings and FAISS similarity search for fast hoax detection"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Use lightweight model for fast embeddings
        logger.info("Loading sentence-transformers model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
        
        self.index_path = self.data_dir / "faiss_index.bin"
        self.metadata_path = self.data_dir / "faiss_metadata.json"
        
        self.index = None
        self.metadata = []
        
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create new one"""
        if self.index_path.exists() and self.metadata_path.exists():
            try:
                logger.info("Loading existing FAISS index...")
                self.index = faiss.read_index(str(self.index_path))
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded {len(self.metadata)} entries from FAISS index")
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create new FAISS index with sample hoaxes"""
        logger.info("Creating new FAISS index...")
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.metadata = []
        
        # Seed with sample known hoaxes
        self._seed_sample_hoaxes()
        self._save_index()
    
    def _seed_sample_hoaxes(self):
        """Add sample known hoaxes to the index"""
        sample_hoaxes = [
            {
                "text": "5G towers cause coronavirus spread and illness",
                "verdict": "FAKE",
                "source": "Debunked by WHO and scientific community",
                "category": "health_misinformation"
            },
            {
                "text": "Vaccines contain microchips for tracking people",
                "verdict": "FAKE",
                "source": "Conspiracy theory debunked by fact-checkers",
                "category": "vaccine_misinformation"
            },
            {
                "text": "Climate change is a hoax invented by governments",
                "verdict": "FAKE",
                "source": "Contradicts scientific consensus",
                "category": "climate_denial"
            },
            {
                "text": "Drinking bleach cures diseases and infections",
                "verdict": "FAKE",
                "source": "Dangerous myth debunked by medical experts",
                "category": "health_misinformation"
            },
            {
                "text": "Moon landing was faked in a studio",
                "verdict": "FAKE",
                "source": "Conspiracy theory debunked",
                "category": "conspiracy"
            }
        ]
        
        for hoax in sample_hoaxes:
            self.add_to_index(hoax["text"], hoax)
        
        logger.info(f"Seeded {len(sample_hoaxes)} sample hoaxes")
    
    def add_to_index(self, text: str, metadata: dict):
        """Add new entry to FAISS index"""
        try:
            # Generate embedding
            embedding = self.model.encode([text])[0]
            embedding = np.array([embedding], dtype=np.float32)
            
            # Add to FAISS index
            self.index.add(embedding)
            
            # Store metadata
            self.metadata.append({
                "text": text,
                **metadata
            })
            
            logger.debug(f"Added entry to index: {text[:50]}...")
        except Exception as e:
            logger.error(f"Error adding to index: {e}")
    
    def search_similar(self, text: str, k: int = 5, threshold: float = 0.8):
        """
        Search for similar entries in FAISS index
        
        Args:
            text: Query text to search
            k: Number of results to return
            threshold: Similarity threshold (0-1, higher = more similar)
        
        Returns:
            List of matches with scores and metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.model.encode([text])[0]
            query_embedding = np.array([query_embedding], dtype=np.float32)
            
            # Search FAISS index
            distances, indices = self.index.search(query_embedding, k)
            
            # Convert distances to similarity scores (L2 distance -> similarity)
            # Lower L2 distance = higher similarity
            max_distance = 2.0  # Typical max L2 distance for normalized embeddings
            similarities = 1 - (distances[0] / max_distance)
            
            # Filter by threshold and return results
            results = []
            for idx, (similarity, index) in enumerate(zip(similarities, indices[0])):
                if index < len(self.metadata) and similarity >= threshold:
                    results.append({
                        "similarity": float(similarity),
                        "match": self.metadata[index],
                        "rank": idx + 1
                    })
            
            return results
        except Exception as e:
            logger.error(f"Error searching index: {e}")
            return []
    
    def _save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            faiss.write_index(self.index, str(self.index_path))
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
            logger.info("FAISS index saved successfully")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")
    
    def get_stats(self):
        """Get statistics about the index"""
        return {
            "total_entries": len(self.metadata),
            "index_size": self.index.ntotal if self.index else 0,
            "embedding_dimension": self.embedding_dim
        }

# Global instance
_embeddings_manager = None

def get_embeddings_manager():
    """Get or create global embeddings manager instance"""
    global _embeddings_manager
    if _embeddings_manager is None:
        _embeddings_manager = EmbeddingsManager()
    return _embeddings_manager
