import httpx
from app.core.config import settings
from typing import Dict, Any, Optional

class HuggingFaceClient:
    def __init__(self):
        if not settings.HUGGINGFACE_API_TOKEN:
            raise ValueError("HUGGINGFACE_API_TOKEN is not set")
        
        self.api_url = "https://api-inference.huggingface.co/models"
        self.headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}"}

    async def query(self, model_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the HuggingFace Inference API.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/{model_id}",
                headers=self.headers,
                json=payload,
                timeout=30.0  # Increased timeout for larger models
            )
            
            if response.status_code != 200:
                # Handle model loading state
                if "estimated_time" in response.json():
                    return {"error": "Model is loading", "estimated_time": response.json()["estimated_time"]}
                raise Exception(f"HuggingFace API Error: {response.text}")
                
            return response.json()

# Models Configuration
MODELS = {
    "text_detection": "desklib/ai-text-detector-v1.01",
    "image_detection": "prithivMLmods/Deep-Fake-Detector-v2-Model",
    "audio_detection": "MelodyMachine/Deepfake-audio-detection-V2",
    "video_detection": "Naman712/Deep-fake-detection"
}

hf_client = HuggingFaceClient()
