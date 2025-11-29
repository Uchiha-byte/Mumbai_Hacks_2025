from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

def get_llm(temperature: float = 0.0):
    """
    Get the Gemini LLM instance.
    """
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not set in environment variables.")
        
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-001",  # Latest stable Gemini 2.0
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=temperature,
        convert_system_message_to_human=True
    )
    return llm

def get_vision_llm(temperature: float = 0.0):
    """
    Get the Gemini Vision LLM instance for image/video analysis.
    """
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not set in environment variables.")
        
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-001",  # Latest stable Gemini 2.0 with vision support
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=temperature,
        convert_system_message_to_human=True
    )
    return llm
