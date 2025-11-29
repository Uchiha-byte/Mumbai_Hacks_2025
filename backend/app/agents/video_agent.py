from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from langchain_core.tools import Tool
from app.core.llm import get_vision_llm
from app.core.huggingface import hf_client, MODELS
import base64
import cv2
import numpy as np

async def detect_deepfake_video(video_data: str) -> str:
    """
    Detects if a video contains deepfakes by analyzing frames.
    Input: Base64 string of the video.
    """
    try:
        # Remove header if present
        if "," in video_data:
            video_data = video_data.split(",")[1]
            
        # For video, we might need to extract frames and analyze them
        result = await hf_client.query(
            MODELS["video_detection"], 
            {"inputs": video_data}
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

def analyze_video_frames(video_data: str) -> str:
    """
    Extracts and analyzes key frames from the video.
    """
    try:
        # This is a placeholder. Real implementation would:
        # 1. Decode base64 to video file
        # 2. Use cv2 to extract frames
        # 3. Analyze frames for inconsistencies
        return "Frame analysis not yet fully implemented."
    except Exception as e:
        return f"Error in frame analysis: {str(e)}"

def get_video_agent():
    """
    Creates the Video Analysis Agent.
    """
    llm = get_vision_llm(temperature=0.2)
    
    tools = [
        Tool(
            name="Deepfake_Video_Detector",
            func=detect_deepfake_video,
            description="Detects if a video contains deepfake content. Returns 'label|confidence'."
        ),
        Tool(
            name="Frame_Analyzer",
            func=analyze_video_frames,
            description="Provides basic frame analysis information."
        )
    ]
    
    # Create the agent with enhanced output format
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="""You are a video authenticity detector. Analyze using the Deepfake_Video_Detector tool.

The detector returns: "Label|Score" (e.g., "Real|0.85" or "Fake|0.72")

Output in this EXACT format:

**🎬 Video Authenticity Analysis**

**Result:** [Authentic / Deepfake / AI-Generated]  
**Confidence:** [XX%]  
**Risk Level:** [Low / Medium / High]

**Visual Analysis:**
• [Observation 1 - e.g., "Natural facial movements" or "Inconsistent lip-sync detected"]
• [Observation 2 - e.g., "Consistent lighting" or "Face boundary artifacts"]
• [Observation 3 - e.g., "Smooth transitions" or "Temporal inconsistencies"]

**Frame Analysis:** [Optionally use Frame_Analyzer for technical details]

**⚠️ Note:** Free detection models have limited accuracy. For critical deepfake verification, use professional forensic analysis.

RULES:
- If confidence > 80%: Risk = Low
- If confidence 50-80%: Risk = Medium  
- If confidence < 50%: Risk = High
- Focus on facial/movement consistency
- Keep observations brief"""
    )
    
    return agent
