from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from langchain_core.tools import Tool
from app.core.llm import get_vision_llm
from app.core.huggingface import hf_client, MODELS
from PIL import Image
import io
import base64

async def detect_deepfake_image(image_data: str) -> str:
    """
    Detects if an image is a deepfake using HuggingFace model.
    Input: Base64 string of the image.
    """
    try:
        # Remove header if present (data:image/jpeg;base64,...)
        if "," in image_data:
            image_data = image_data.split(",")[1]
            
        # Decode to bytes
        image_bytes = base64.b64decode(image_data)
        
        result = await hf_client.query(
            MODELS["image_detection"], 
            {"inputs": image_data} 
        )
        
        if "error" in result:
            return f"Error|0.0"
            
        # Parse result - usually a list of classifications
        if isinstance(result, list):
            top_result = sorted(result, key=lambda x: x['score'], reverse=True)[0]
            return f"{top_result['label']}|{top_result['score']:.2f}"
            
        return "Unknown|0.5"
    except Exception as e:
        return f"Error|0.0"

def extract_metadata(image_data: str) -> str:
    """
    Extracts EXIF metadata from the image.
    """
    try:
        if "," in image_data:
            image_data = image_data.split(",")[1]
        image_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(image_bytes))
        
        # Basic metadata summary
        info = f"Format: {img.format}, Size: {img.size}, Mode: {img.mode}"
        return info
    except Exception as e:
        return f"Error extracting metadata: {str(e)}"

def get_image_agent():
    """
    Creates the Image Forensics Agent.
    """
    llm = get_vision_llm(temperature=0.2)
    
    tools = [
        Tool(
            name="Deepfake_Image_Detector",
            func=detect_deepfake_image,
            description="Detects if an image is AI-generated or manipulated. Returns 'label|confidence'."
        ),
        Tool(
            name="Metadata_Extractor",
            func=extract_metadata,
            description="Extracts image metadata (format, size, mode)."
        )
    ]
    
    # Create the agent with enhanced output format
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="""You are an image authenticity detector. Analyze using the Deepfake_Image_Detector tool.

The detector returns: "Label|Score" (e.g., "Real|0.85" or "Fake|0.72")

Output in this EXACT format:

**🖼️ Image Authenticity Analysis**

**Result:** [Authentic / AI-Generated / Manipulated]  
**Confidence:** [XX%]  
**Risk Level:** [Low / Medium / High]

**Visual Analysis:**
• [Observation 1 - e.g., "Natural lighting patterns" or "Unusual artifacts detected"]
• [Observation 2 - e.g., "Consistent shadows" or "Inconsistent facial features"]

**Metadata:** [Use Metadata_Extractor - show format, dimensions]

**⚠️ Note:** Free detection models have limited accuracy. For critical verification, use professional forensic tools.

RULES:
- If confidence > 80%: Risk = Low
- If confidence 50-80%: Risk = Medium  
- If confidence < 50%: Risk = High
- Keep observations brief"""
    )
    
    return agent
