from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from app.core.llm import get_llm
from app.core.huggingface import hf_client, MODELS
from app.core.config import settings
import os

# Ensure TAVILY_API_KEY is set in environment for LangChain tool
if settings.TAVILY_API_KEY:
    os.environ["TAVILY_API_KEY"] = settings.TAVILY_API_KEY

async def detect_ai_text(text: str) -> str:
    """
    Detects if text is AI-generated using HuggingFace model.
    """
    try:
        # Truncate text if too long for the model
        truncated_text = text[:1000]
        result = await hf_client.query(
            MODELS["text_detection"], 
            {"inputs": truncated_text}
        )
        
        if "error" in result:
            return f"Error analyzing text: {result['error']}"
            
        # Parse result - usually returns a list of labels/scores
        if isinstance(result, list) and len(result) > 0:
            # Flatten if nested list
            scores = result[0] if isinstance(result[0], list) else result
            # Sort by score desc
            top_result = sorted(scores, key=lambda x: x['score'], reverse=True)[0]
            return f"{top_result['label']}|{top_result['score']:.2f}"
            
        return "Unknown|0.5"
    except Exception as e:
        return f"Error|0.0"

def get_text_agent():
    """
    Creates the Text Analysis Agent.
    """
    llm = get_llm(temperature=0.2)
    
    # Tools - ONLY AI detector
    tools = [
        Tool(
            name="AI_Text_Detector",
            func=detect_ai_text,
            description="Detects if text was written by AI or human. Returns result in format 'label|confidence'."
        )
    ]
    
    # Create the agent with enhanced output format
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="""You are an AI text detector. Analyze the text using the AI_Text_Detector tool.

The tool returns: "Label|Score" (e.g., "Human|0.85" or "AI|0.72")

Output in this EXACT format:

**🔍 AI Detection Analysis**

**Result:** [Human-Written / AI-Generated]  
**Confidence:** [XX%]  
**Risk Level:** [Low / Medium / High]

**Key Indicators:**
• [Indicator 1 - e.g., "Natural language patterns" or "Repetitive phrasing"]
• [Indicator 2 - e.g., "Varied sentence structure" or "Formulaic structure"]

**⚠️ Note:** Free detection models have limited accuracy. For production use, consider premium APIs like GPTZero or OpenAI.

RULES:
- If confidence > 80%: Risk = Low
- If confidence 50-80%: Risk = Medium  
- If confidence < 50%: Risk = High
- Keep indicators brief (1 line each)
- Be honest about uncertainty"""
    )

    return agent
