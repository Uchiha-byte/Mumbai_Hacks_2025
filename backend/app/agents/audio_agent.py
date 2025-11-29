from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from langchain_core.tools import Tool
from app.core.llm import get_llm
from app.core.huggingface import hf_client, MODELS
import base64

async def detect_deepfake_audio(audio_data: str) -> str:
    """
    Detects if audio is a deepfake using HuggingFace model.
    Input: Base64 string of the audio.
    """
    try:
        # Remove header if present
        if "," in audio_data:
            audio_data = audio_data.split(",")[1]
            
        # For audio models, HF often expects the binary file or base64
        result = await hf_client.query(
            MODELS["audio_detection"], 
            {"inputs": audio_data}
        )
        
        if "error" in result:
            return f"Error|0.0"
            
        # Parse result
        if isinstance(result, list):
            top_result = sorted(result, key=lambda x: x['score'], reverse=True)[0]
            return f"{top_result['label']}|{top_result['score']:.2f}"
            
        return "Unknown|0.5"
    except Exception as e:
        return f"Error|0.0"

def get_audio_agent():
    """
    Creates the Audio Verification Agent.
    """
    llm = get_llm(temperature=0.2)
    
    tools = [
        Tool(
            name="Deepfake_Audio_Detector",
            func=detect_deepfake_audio,
            description="Detects if audio is AI-generated (voice cloning). Returns 'label|confidence'."
        )
    ]
    
    # Create the agent with enhanced output format
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="""You are an audio authenticity detector. Analyze using the Deepfake_Audio_Detector tool.

The detector returns: "Label|Score" (e.g., "Real|0.85" or "Fake|0.72")

Output in this EXACT format:

**🎵 Audio Authenticity Analysis**

**Result:** [Authentic / AI-Generated / Voice-Cloned]  
**Confidence:** [XX%]  
**Risk Level:** [Low / Medium / High]

**Audio Analysis:**
• [Observation 1 - e.g., "Natural voice patterns detected" or "Robotic artifacts present"]
• [Observation 2 - e.g., "Consistent vocal tone" or "Unnatural breathing patterns"]

**Technical Notes:** [Brief mention of any audio quality issues or limitations]

**⚠️ Note:** Free detection models have limited accuracy. For critical voice verification, use professional audio forensics.

RULES:
- If confidence > 80%: Risk = Low
- If confidence 50-80%: Risk = Medium  
- If confidence < 50%: Risk = High
- Keep observations brief and relevant"""
    )
    
    return agent
