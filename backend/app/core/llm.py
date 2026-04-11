import google.generativeai as genai
from app.core.config import settings

def get_llm():
    """
    Get the Gemini LLM instance using the native google.generativeai SDK.
    """
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not set in environment variables.")

    genai.configure(api_key=settings.GOOGLE_API_KEY)
    return genai.GenerativeModel("gemini-2.5-flash")

def get_vision_llm():
    """
    Get the Gemini Vision LLM instance for image/video analysis.
    Gemini 2.5 Flash handles vision natively.
    """
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not set in environment variables.")

    genai.configure(api_key=settings.GOOGLE_API_KEY)
    return genai.GenerativeModel("gemini-2.5-flash")
