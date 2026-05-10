import os
import pathlib
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# The modern, dedicated imports!
from langchain_tavily import TavilySearch 
from langchain_chroma import Chroma
from langchain.agents import create_agent

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()


embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
db_dir = './chroma_db'

print("Checking vector database...")

if not os.path.exists(db_dir):
   print("Building new Chroma DB from PDFs...")

   pathes = list(pathlib.Path('./data').glob('**/*.pdf'))
   
   load_docs = []
   for path in pathes:
      loader = PyPDFLoader(str(path)) 
      load_docs.extend(loader.load())

   spiltter = RecursiveCharacterTextSplitter(
      chunk_size=400,
      chunk_overlap=80,
      separators=['\n\n', '\n', ' ', '']
   )
   chunks = spiltter.split_documents(load_docs)

   db = Chroma.from_documents(
      documents=chunks,
      embedding=embeddings,
      collection_name='Lab3_collection',
      persist_directory=db_dir
   )
else:
   print("Loading existing Chroma DB...")
   db = Chroma(
      collection_name='Lab3_collection',
      embedding_function=embeddings,
      persist_directory=db_dir
   )


@tool
def rag_search(prompt: str) -> str:
   """Use this tool to search the local document database for specific data."""
   ragResult = db.similarity_search_with_score(prompt, k=8)
   context = "\n".join([doc.page_content for doc, score in ragResult])
   
   if not context:
      return "I don't know."
   return context


llm = ChatOpenAI(model="gpt-4o-mini")

# Back to your original, correct tool!
tavily_tool = TavilySearch(max_results=3)

# Using the modern create_agent with the hallucination-proof prompt
agent = create_agent(
   model = llm,
   tools = [tavily_tool, rag_search],
   system_prompt = (
        "You are a strict data assistant. You must answer the user's question relying ONLY on the context provided by your tools. "
        "1. ALWAYS use the rag_search tool first. "
        "2. If the rag_search tool provides context, you must summarize ONLY what is explicitly written in that text. DO NOT add your own outside knowledge, definitions, or explanations. "
        "3. If the rag_search tool's context does not contain the answer to the user's question, you must say exactly: 'I don't know based on my documents.' Do not attempt to guess or use your internal knowledge. "
        "4. Use the TavilySearch tool ONLY if the user explicitly asks for updated internet data."
   ),
)

print("\n--- Agent Ready. Type 'quit' to exit. ---")
while True:
   user_input = input("\nYou: ")

   if user_input.lower() in ['quit', 'exit', 'q']:
      print("Ending session.")
      break
      
   inputs = {"messages": [HumanMessage(content=user_input)]}
   
   for chunk in agent.stream(inputs, stream_mode="updates"):
      for node_name, node_state in chunk.items():
         if "messages" in node_state:
               for msg in node_state["messages"]:
                  msg.pretty_print()