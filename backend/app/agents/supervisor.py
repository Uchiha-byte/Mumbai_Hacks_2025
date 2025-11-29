from langchain.agents import create_agent
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from app.core.llm import get_llm
from app.agents.text_agent import get_text_agent
from app.agents.image_agent import get_image_agent
from app.agents.audio_agent import get_audio_agent
from app.agents.video_agent import get_video_agent

# Initialize Sub-Agents
text_agent = get_text_agent()
image_agent = get_image_agent()
audio_agent = get_audio_agent()
video_agent = get_video_agent()

def route_text_analysis(input_text: str) -> str:
    """Routes to Text Agent"""
    result = text_agent.invoke({"messages": [HumanMessage(content=input_text)]})
    return result["messages"][-1].content

def route_image_analysis(input_image: str) -> str:
    """Routes to Image Agent"""
    result = image_agent.invoke({"messages": [HumanMessage(content=input_image)]})
    return result["messages"][-1].content

def route_audio_analysis(input_audio: str) -> str:
    """Routes to Audio Agent"""
    result = audio_agent.invoke({"messages": [HumanMessage(content=input_audio)]})
    return result["messages"][-1].content

def route_video_analysis(input_video: str) -> str:
    """Routes to Video Agent"""
    result = video_agent.invoke({"messages": [HumanMessage(content=input_video)]})
    return result["messages"][-1].content

def get_supervisor_agent():
    """
    Creates the Supervisor Agent that routes requests.
    """
    llm = get_llm(temperature=0)
    
    tools = [
        Tool(
            name="Text_Analysis_Specialist",
            func=route_text_analysis,
            description="Use this for analyzing text content, articles, or claims."
        ),
        Tool(
            name="Image_Forensics_Specialist",
            func=route_image_analysis,
            description="Use this for analyzing images, photos, or screenshots."
        ),
        Tool(
            name="Audio_Verification_Specialist",
            func=route_audio_analysis,
            description="Use this for analyzing audio clips, voice recordings, or speech."
        ),
        Tool(
            name="Video_Analysis_Specialist",
            func=route_video_analysis,
            description="Use this for analyzing video files or clips."
        )
    ]
    
    # Create the agent using create_agent (LangChain 1.0.8+)
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="""You are the Supervisor of the TruthScan AI System. Your job is to route the user's request to the correct specialist agent based on the content type.

Tools available:
{tools}

Use the following format:

Question: the input question you must answer
Thought: I need to determine the content type (Text, Image, Audio, or Video) and route it to the correct specialist.
Action: the action to take, should be one of [{tool_names}]
Action Input: the content to analyze
Observation: the result of the action
Thought: I have the analysis from the specialist.
Final Answer: the final report

Begin!"""
    )
    
    return agent
