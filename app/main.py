from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Message(BaseModel):
    content: str
    author: str
    metadata: Optional[dict] = None

class ChatRequest(BaseModel):
    message: str
    history: List[Message]

class ChatResponse(BaseModel):
    content: str
    metadata: Optional[dict] = None

# Authentication
class User(BaseModel):
    username: str
    password: str

@app.post("/login")
async def login(user: User):
    # Implement your authentication logic here
    if user.username == "test" and user.password == "test":
        return {"token": "dummy_token"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Import your existing chat logic
        from service.store_chatbot import gen_answer
        
        # Generate response using your existing logic
        response = gen_answer(
            user_id=uuid.uuid4(),  # Generate temporary ID
            thread_id=uuid.uuid4(),
            history=request.history
        )
        
        return ChatResponse(
            content=response.content,
            metadata=response.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 