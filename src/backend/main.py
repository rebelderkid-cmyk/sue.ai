import os
import json
import datetime
from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Internal imports
from database import engine, Base, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User, AuditLog, Conversation, Message
from auth import get_current_user_claims
from rag_core import chat_workflow_stream

app = FastAPI(
    title="Sue.AI Enterprise API",
    description="Legal Research AI Backend powered by Vertex AI & Gemini",
    version="2.0.0"
)

# --- CORS Configuration ---
# Allow all origins for dev; restrict in prod
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Startup ---
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Create tables (for development mainly)
        # In prod, use Alembic migrations!
        await conn.run_sync(Base.metadata.create_all)

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    question: str
    filters: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, str]]] = []

# --- Routes ---

@app.get("/")
async def root():
    return {"message": "Sue.AI Enterprise API is Running! 🚀 (FastAPI)"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/auth/sync")
async def sync_user(
    claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db)
):
    """
    Syncs Firebase User to Postgres Database.
    Call this after Firebase Login on frontend.
    """
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid token")

    uid = claims.get("uid")
    email = claims.get("email")
    picture = claims.get("picture")
    name = claims.get("name")

    # Check if user exists
    result = await db.execute(select(User).where(User.firebase_uid == uid))
    user = result.scalars().first()

    if user:
        # Update existing
        user.last_login_at = datetime.datetime.now(datetime.timezone.utc)
        user.avatar_url = picture
        user.full_name = name
        # email might change? unlikely with same uid usually, but let's sync
        user.email = email 
    else:
        # Create new
        user = User(
            firebase_uid=uid,
            email=email,
            full_name=name,
            avatar_url=picture,
            last_login_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(user)
    
    await db.commit()
    await db.refresh(user)

    return {
        "status": "synced",
        "user_id": user.id,
        "firebase_uid": user.firebase_uid,
        "email": user.email,
        "role": "MEMBER" # Placeholder until we implement roles lookup
    }

@app.post("/api/chat")
async def chat_endpoint(
    request: ChatRequest, 
    user_claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream chat response using Server-Sent Events (SSE).
    Autosaves history if user is logged in.
    """
    if not request.question:
        raise HTTPException(status_code=400, detail="No question provided")

    user_id = user_claims.get("uid") if user_claims else None
    
    # --- Conversation Handling ---
    conversation_id = request.history[0].get("conversation_id") if request.history and "conversation_id" in request.history[0] else None
    
    if user_id:
        # Check database user
        result = await db.execute(select(User).where(User.firebase_uid == user_id))
        db_user = result.scalars().first()
        
        if db_user:
            if not conversation_id:
                # Create NEW Conversation
                new_conv = Conversation(
                    user_id=db_user.id,
                    title=request.question[:50] # Simple title from first question
                )
                db.add(new_conv)
                await db.commit()
                await db.refresh(new_conv)
                conversation_id = new_conv.id
            
            # Save USER Message
            user_msg = Message(
                conversation_id=conversation_id,
                role="user",
                content=request.question
            )
            db.add(user_msg)
            await db.commit()

    # Reuse the existing Logic from rag_core.py
    try:
        sources, generator = chat_workflow_stream(
            request.question, 
            filters=request.filters, 
            history=request.history
        )
        
        async def response_generator():
            full_ai_response = ""
            
            # 1. Yield Answer Chunks
            for chunk in generator:
                 full_ai_response += chunk
                 yield f"data: {json.dumps({'type': 'chunk', 'text': chunk}, ensure_ascii=False)}\n\n"
            
            # 2. Yield Sources (Already computed)
            yield f"data: {json.dumps({'type': 'sources', 'data': sources}, ensure_ascii=False)}\n\n"
            
            # 3. Yield Conversation ID (New feature)
            if conversation_id:
                yield f"data: {json.dumps({'type': 'conversation_id', 'id': conversation_id}, ensure_ascii=False)}\n\n"

            # 4. Save AI Message to DB (Post-Stream)
            if user_id and conversation_id:
                 # We need a new session context here or use the existing one? 
                 # Since this is async generator inside route, 'db' session from 'Depends' *should* still be valid until response closes.
                 # Let's try utilizing the captured 'db'. 
                 # Note: Concurrency safety - db session is not thread safe but we are in async await sequence.
                 try:
                     ai_msg = Message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=full_ai_response
                     )
                     db.add(ai_msg)
                     await db.commit()
                 except Exception as e:
                     print(f"❌ Failed to save history: {e}")

            # 5. Done
            yield "data: [DONE]\n\n"

        return StreamingResponse(response_generator(), media_type="text/event-stream")

    except Exception as e:
        print(f"❌ API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- History Endpoints ---

@app.get("/api/history")
async def get_history(
    user_claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db)
):
    """
    List all conversations for the current user.
    """
    if not user_claims:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    uid = user_claims.get("uid")
    # Get DB user ID first
    result = await db.execute(select(User).where(User.firebase_uid == uid))
    db_user = result.scalars().first()
    
    if not db_user:
        return []

    # Get conversations
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == db_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    convs = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "title": c.title,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        }
        for c in convs
    ]

@app.get("/api/history/{conversation_id}")
async def get_conversation_messages(
    conversation_id: str,
    user_claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all messages for a specific conversation.
    """
    if not user_claims:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    uid = user_claims.get("uid")
    result = await db.execute(select(User).where(User.firebase_uid == uid))
    db_user = result.scalars().first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get conversation and verify ownership
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == db_user.id)
    )
    conv = result.scalars().first()
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    msgs = result.scalars().all()
    
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in msgs
    ]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Sue.AI Cloud Server starting on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
