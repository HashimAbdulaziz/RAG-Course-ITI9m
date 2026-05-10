# Agentic System Course - ITI

Complete course materials covering agents, message management, and retrieval-augmented generation with LangChain.

---

# Day 2: AI Chef Assistant - Architecture Evolution

## The "Infinite Array" (Old Code)

In the initial version, the conversation state was managed using a basic Python list (`chatHistory`). While this works for a quick terminal test, it is a dangerous anti-pattern for a backend application.

---

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

---

# Day 3: RAG System with LangChain

Retrieval-Augmented Generation (RAG) implementation using LangChain, OpenAI embeddings, and Chroma vector database.

## Overview

This project demonstrates a complete RAG pipeline that:

- Loads PDF documents from a data directory
- Splits documents into manageable chunks
- Creates embeddings using OpenAI's text-embedding-3-small model
- Stores embeddings in a Chroma vector database
- Performs similarity search on user queries
- Generates answers using an LLM with retrieved context

## Installation

### Prerequisites

- Python 3.8+
- OpenAI API key
- Environment variables configured (see `.env` setup below)

### Required Packages

```bash
pip install langchain langchain_openai python-dotenv
pip install langchain-community pypdf
pip install langchain-chroma
pip install langchain-text-splitters
```

### Environment Setup

Create a `.env` file in your working directory:

```
OPENAI_API_KEY=your_openai_api_key_here
```

Load environment variables at the start of your script:

```python
from dotenv import load_dotenv
load_dotenv()
```

## Architecture

### 1. Embeddings

Generate vectorial representations of text using OpenAI's embedding model:

```python
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
```

Output: Vector of 1536 dimensions for each text query.

### 2. Document Loaders

Load PDF files from the data directory:

```python
from langchain_community.document_loaders import PyPDFLoader
import pathlib

paths = list(pathlib.Path('./data').glob('**/*.pdf'))
loaded_docs = []
for path in paths:
    loader = PyPDFLoader(path)
    loaded_docs.extend(loader.load())
```

### 3. Document Splitting

Split documents into smaller chunks for better retrieval:

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=80,
    separators=['\n\n', '\n', ' ', '']
)
chunks = splitter.split_documents(loaded_docs)
```

**Configuration:**

- Chunk size: 400 characters
- Overlap: 80 characters (prevents losing context between chunks)
- Separators: Preserve document structure

### 4. Vector Store

Create and persist a Chroma vector database:

```python
from langchain_community.vectorstores import Chroma

db = Chroma.from_documents(
    chunks,
    embeddings,
    collection_name='my_collection',
    persist_directory='./chroma_db'
)
```

### 5. Similarity Search

Retrieve relevant documents based on query similarity:

```python
prompt = 'what is the capital of iran'
chunks = db.similarity_search(prompt, k=3)
```

Parameters:

- `k=3`: Return top 3 most relevant chunks
- Supports `similarity_search_with_score()` for relevance scores

### 6. RAG Implementation

Combine retrieved context with LLM for answer generation:

```python
from langchain_core.prompts import PromptTemplate
from langchain.chat_models import init_chat_model

# Initialize LLM
llm = init_chat_model("gpt-4.1", temperature=0.2)

# Define RAG prompt template
rag_template = PromptTemplate(
    template="""Use the context to answer the question. If the context does not contain the answer, say 'I do not know'.
context: {context}
question: {question}""",
    input_variables=['context', 'question']
)

# Execute RAG query
context = "\n".join([chunk.page_content for chunk in chunks])
response = llm.invoke(rag_template.format(context=context, question=prompt))
print(response.content)
```

## Workflow

1. **Setup**: Load environment variables and initialize embeddings
2. **Load**: Retrieve PDF files from data directory
3. **Split**: Chunk documents with overlap for context preservation
4. **Index**: Create and persist vector embeddings in Chroma
5. **Query**: Search for relevant chunks using similarity matching
6. **Generate**: Combine context with LLM for intelligent responses

## Key Components

- **Embeddings Model**: OpenAI text-embedding-3-small (1536 dimensions)
- **LLM**: GPT-4.1 with temperature 0.2 (deterministic responses)
- **Vector Database**: Chroma with local persistence
- **Text Splitter**: Recursive character-based splitting with overlap

## Database Management

Chroma database is persisted in `./chroma_db/` directory. To clear and rebuild:

```bash
rm -rf ./chroma_db/
```

Then reinitialize by running the database creation cell.

## Limitations & Future Enhancements

- Current implementation uses manual similarity search
- Can be extended with conversation memory for multi-turn interactions
- Support for different LLMs (Claude, Llama, etc.)
- Advanced prompt engineering for better answer quality
- Integration with agents for tool-based actions

## Notes

- Adjustable parameters: chunk_size, chunk_overlap, temperature, k (number of retrieved documents)
- For production, consider streaming responses and batch processing
- Monitor API costs when using OpenAI services
