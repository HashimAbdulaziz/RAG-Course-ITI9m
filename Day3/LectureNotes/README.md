# RAG System with LangChain

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
