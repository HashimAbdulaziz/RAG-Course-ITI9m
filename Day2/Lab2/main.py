import requests
import base64
import mimetypes
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langchain_tavily import TavilySearch

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI 

def encode_image(image_path):
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        mime_type = "image/jpeg"
    with open(image_path, "rb") as image_file:
        base64_str = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:{mime_type};base64,{base64_str}"
    
load_dotenv()

@tool
def get_user_location() -> str:
    """Use this tool to find the user's current city, region, and country based on their IP address."""
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        data = response.json()
        if data.get("status") == "success":
            return f"{data.get('city')}, {data.get('country')}"
        else:
            return "Error: IP API blocked the request. Ask the user for their city."
    except Exception as e:
        return f"Error connecting to location service: {str(e)}"

search_tool = TavilySearch(max_results=3)

llm = ChatOpenAI(model="gpt-4o-mini")

agent = create_react_agent(
   model=llm,
   tools=[search_tool, get_user_location], 
   system_prompt=(
       "You are a Medical AI Assistant Agent that analyzes patient cases. "
       "If the user asks for nearby facilities, ALWAYS use the get_user_location tool first to find where they are, "
       "and then use the Tavily search tool to find hospitals in that specific location."
   ),
   checkpointer=MemorySaver()
)


config = {"configurable": {"thread_id": "patient_case_002"}}


print("Uploading MRI and starting analysis...")
image_path = "image.png"
formatted_image = encode_image(image_path)

multimodal_message = HumanMessage(
    content=[
        {"type": "text", "text": "Analyze this MRI image and describe any anomalies. Then, use your tool to find hospitals near me that specialize in this."},
        {"type": "image_url", "image_url": {"url": formatted_image}}
    ]
)

for chunk in agent.stream({"messages": [multimodal_message]}, config, stream_mode="updates"):
    for node_name, node_state in chunk.items():
        if "messages" in node_state:
            for msg in node_state["messages"]:
                msg.pretty_print()


print("\n--- Chat Session Started. Type 'quit' to exit. ---")

while True:
    user_input = input("\nPatient: ")
    
    if user_input.lower() in ['quit', 'exit', 'q']:
        print("Ending session. Take care!")
        break
        
    new_message = {"messages": [HumanMessage(content=user_input)]}
    
    for chunk in agent.stream(new_message, config, stream_mode="updates"):
        for node_name, node_state in chunk.items():
            if "messages" in node_state:
                for msg in node_state["messages"]:
                    msg.pretty_print()