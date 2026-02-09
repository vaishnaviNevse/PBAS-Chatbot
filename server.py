from fastapi import FastAPI
from pydantic import BaseModel
from rag_pipeline import ask_pbas_bot
import uuid

app = FastAPI(title="VERO PBAS AI Assistant")


# ---------------- REQUEST MODEL ----------------
class ChatRequest(BaseModel):
    message: str
    user_id: int
    session_id: str | None = None


# ---------------- HEALTH CHECK ----------------
@app.get("/")
def home():
    return {"status": "VERO PBAS AI Backend Running"}


# ---------------- CHAT ENDPOINT ----------------
@app.post("/chat")
def chat(req: ChatRequest):

    # ✅ Always ensure session_id exists
    session_id = req.session_id or str(uuid.uuid4())

    # ✅ Call chatbot pipeline
    reply = ask_pbas_bot(
        question=req.message,
        user_id=req.user_id,
        session_id=session_id
    )

    # ✅ Send response + session id back
    return {
        "reply": reply,
        "session_id": session_id
    }
