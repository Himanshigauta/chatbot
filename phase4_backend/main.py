import os
import sys
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# Add the project root to sys.path to import from other phases
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from phase3_rag_core.rag_query import query_rag

app = FastAPI(title="Mutual Fund RAG Chatbot API")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]

@app.get("/")
async def root():
    return {"message": "Mutual Fund RAG Chatbot API is running"}

@app.get("/status")
async def status():
    try:
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "last_updated.json"))
        with open(path, "r") as f:
            data = json.load(f)
        return data
    except Exception:
        return {"last_updated": "Unknown"}

@app.get("/suggestions")
async def get_suggestions():
    # These are 100% verified scheme names and questions from our search index
    return [
        "What is the expense ratio of Groww Liquid Fund Direct Growth?",
        "What is the risk profile of Groww Overnight Fund Direct Growth?",
        "Tell me the pros and cons of Groww Value Fund Direct Growth",
        "What is the category of Groww Large Cap Fund Direct Growth?",
        "What is the benchmark of Groww Multicap Fund Direct Growth?"
    ]

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        answer, sources = query_rag(request.message)
        if answer.startswith("ERROR:"):
            raise HTTPException(status_code=500, detail=answer)
        return ChatResponse(answer=answer, sources=sources or [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
