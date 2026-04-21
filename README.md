# AI Chef Assistant: Architecture Evolution

---

## The "Infinite Array" (Old Code)

In the initial version, the conversation state was managed using a basic Python list (`chatHistory`). While this works for a quick terminal test, it is a dangerous anti-pattern for a backend application.



---


```

### The Old Code (The "Infinite Array")

This code manually appends data to a simple Python list. It is prone to context window limits, token cost inflation, and memory loss if the script closes.

```python
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


chefSystemPrompt = (
    "You are a Chef. Guide the user step by step through making a meal decision. "
    "Never skip steps. Be human-like and speak like a real, passionate chef. "
    f"{length_instruction}"
)

model = init_chat_model("gpt-5-nano", temperature=temperature_setting)

chatHistory = [
    SystemMessage(content=chefSystemPrompt)
]

while True:
    userInput = input("YOU: ")

    chatHistory.append(HumanMessage(content=userInput))

    result = model.invoke(chatHistory)

    chatHistory.append(result)

    print(f"Chef: {result.content}\n")
```

---

### The Refactored Code (LangGraph State Machine)

This code introduces strict data contracts (`MessagesState`), routing logic (Nodes and Edges), and a "database" concept (`checkpointer`) with session tracking (`thread_id`).

```python
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
s
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.checkpoint.memory import InMemorySaver


def main():
    load_dotenv()
    temperature_setting, length_instruction = getUserConfig()

    chefSystemPrompt = (
        # ... [Prompt definition] ...
    )

    model = init_chat_model("gpt-5-nano", temperature=temperature_setting)

    def callModel(state: MessagesState):
        messages = [SystemMessage(content=chefSystemPrompt)] + state["messages"]
        result = model.invoke(messages)
        return {"messages": [result]}
)
    checkpointer = InMemorySaver()
    builder = StateGraph(MessagesState)
    builder.add_node("chef_node", callModel)
    builder.add_edge(START, "chef_node")
    graph = builder.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "table_1"}}

    while True:
        try:
            user_input = input("\nYOU: ").strip()

            events = graph.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                config
            )

            ai_response = events["messages"][-1].content
            print(f"Chef: {ai_response}")

        except Exception as e:
            print(f"\n[System Error]: {e}")
            break

if __name__ == "__main__":
    main()
```
