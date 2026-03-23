import os
import sys
from dotenv import load_dotenv

# Ensure UTF-8 output and Load Environment
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

# Configuration
CHROMA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "phase2_indexing", "chroma_db_full"))

# Singleton objects for caching
_embeddings = None
_db = None
_llm = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings

def get_db():
    global _db
    if _db is None:
        _db = Chroma(persist_directory=CHROMA_PATH, embedding_function=get_embeddings())
    return _db

def query_rag(query_text: str):
    """Query the vector database and generate a response using Groq LLM."""
    global _llm
    
    # Check for Groq API Key
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        return "ERROR: GROQ_API_KEY not found in environment variables. Please set it to proceed.", None

    # Load Vector Store (Cached)
    db = get_db()
    
    # Search for similar documents
    results = db.similarity_search_with_relevance_scores(query_text, k=4)
    
    if len(results) == 0:
        return "I am sorry, I couldn't find any specific information about that fund or metric in the current database.", []

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    source_links = list(set([doc.metadata.get("source") for doc, _score in results if doc.metadata.get("source")]))

    # System Prompt (Enforcing Factual, No Advice, No Personal Info, Source Citation)
    PROMPT_TEMPLATE = """
    You are a factual mutual fund assistant. Your goal is to answer questions about mutual fund schemes using ONLY the provided context.
    
    STRICT RULES:
    1. Do NOT use any internal knowledge. If the provided context doesn't have the answer, say "I don't have that information."
    2. Do NOT provide any investment advice, recommendations, or personal financial opinions.
    3. PRIVACY: If the user asks for personal information (e.g., "my balance", "my PAN", "my folio", "my name"), state that "Personal information queries are out of scope for this chatbot."
    4. CITE SOURCE: Mention the source link provided in the context for every technical fact.

    Context:
    {context}

    Question:
    {question}

    Answer:
    """

    # Initialize Groq LLM (Cached)
    if _llm is None:
        _llm = ChatGroq(
            temperature=0,
            model_name="llama-3.1-8b-instant", # Updated model
            groq_api_key=groq_api_key
        )
    llm = _llm

    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    
    response = llm.invoke(prompt)
    
    return response.content, source_links

if __name__ == "__main__":
    # Test query
    query = "What is the expense ratio and risk of Groww Liquid Fund?"
    context, sources = query_rag(query)
    print(f"QUERY: {query}\n")
    print(f"CONTEXT FOUND:\n{context}\n")
    print(f"SOURCE LINKS: {sources}")
