from fastapi import FastAPI
from pydantic import BaseModel
from SmartBudgetAI.chat_engine import handle_user_message

app = FastAPI(
    title="SmartBudgetAI",
    description="AI-powered personal finance & loan assistant",
    version="1.0.0"
)

# -----------------------------
# Request / Response models
# -----------------------------
class ChatRequest(BaseModel):
    user_id: int = 1
    message: str

class ChatResponse(BaseModel):
    reply: str


# -----------------------------
# Health check
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "SmartBudgetAI API is running"}


# -----------------------------
# Chat endpoint
# -----------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    reply = handle_user_message(
        text=req.message,
        user_id=req.user_id
    )
    return {"reply": reply}
