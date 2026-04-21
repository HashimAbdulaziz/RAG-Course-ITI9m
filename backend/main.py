import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.checkpoint.memory import InMemorySaver



load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


checkpointer = InMemorySaver()

class ChatPayload(BaseModel):
    user_input: str
    thread_id: str
    temperature_setting: float
    length_instruction: str

@app.post("/api/chat")
async def chat_endpoint(payload: ChatPayload):
    temperature_setting = payload.temperature_setting
    length_instruction = payload.length_instruction

    chefSystemPrompt = (
      "You are a Chef. Guide the user step by step through making a meal decision. "
      "Never skip steps. Be human-like and speak like a real, passionate chef. "
      f"{length_instruction}"
    )

    model = init_chat_model("gpt-5-nano", temperature=temperature_setting)

    def callModel(state: MessagesState):
      messages = [SystemMessage(content=chefSystemPrompt)] + state["messages"]
      result = model.invoke(messages)
      return {"messages": [result]}
   
    builder = StateGraph(MessagesState)
    builder.add_node("chef_node", callModel)
    builder.add_edge(START, "chef_node")   
    
    graph = builder.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": payload.thread_id}}

    events = graph.invoke(
        {"messages": [HumanMessage(content=payload.user_input)]}, 
        config
    )

    ai_response = events["messages"][-1].content
    
    return {"response": ai_response}