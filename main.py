import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Contact, Message, Campaign, Template, Flow, ChatSession

app = FastAPI(title="Zapgen API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class IdModel(BaseModel):
    id: str


def oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


@app.get("/")
def read_root():
    return {"message": "Zapgen Backend Running"}


# Health & DB test
@app.get("/test")
def test_database():
    resp = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "collections": [],
    }
    try:
        if db is not None:
            resp["database"] = "✅ Connected"
            resp["collections"] = db.list_collection_names()
    except Exception as e:
        resp["database"] = f"⚠️ {str(e)[:80]}"
    return resp


# Contacts
@app.post("/api/contacts", response_model=IdModel)
def create_contact(contact: Contact):
    new_id = create_document("contact", contact)
    return {"id": new_id}


@app.get("/api/contacts")
def list_contacts(tag: Optional[str] = None):
    q: Dict[str, Any] = {}
    if tag:
        q = {"tags": tag}
    docs = get_documents("contact", q, limit=100)
    for d in docs:
        d["id"] = str(d.get("_id"))
        d.pop("_id", None)
    return docs


# Templates
@app.post("/api/templates", response_model=IdModel)
def create_template(tpl: Template):
    new_id = create_document("template", tpl)
    return {"id": new_id}


@app.get("/api/templates")
def list_templates():
    docs = get_documents("template", {}, limit=100)
    for d in docs:
        d["id"] = str(d.get("_id"))
        d.pop("_id", None)
    return docs


# Campaigns (basic scheduling and status tracking only)
@app.post("/api/campaigns", response_model=IdModel)
def create_campaign(c: Campaign):
    new_id = create_document("campaign", c)
    return {"id": new_id}


@app.get("/api/campaigns")
def list_campaigns():
    docs = get_documents("campaign", {}, limit=100)
    for d in docs:
        d["id"] = str(d.get("_id"))
        d.pop("_id", None)
    return docs


# Flows
@app.post("/api/flows", response_model=IdModel)
def create_flow(flow: Flow):
    new_id = create_document("flow", flow)
    return {"id": new_id}


@app.get("/api/flows")
def list_flows():
    docs = get_documents("flow", {}, limit=100)
    for d in docs:
        d["id"] = str(d.get("_id"))
        d.pop("_id", None)
    return docs


# Messages (store chat history, simulate send)
@app.post("/api/messages", response_model=IdModel)
def send_message(msg: Message):
    # TODO: integrate actual WhatsApp API here. For now, store as outbound.
    new_id = create_document("message", msg)
    # upsert chat session last message
    db["chatsession"].update_one(
        {"contact_id": msg.contact_id},
        {"$set": {"contact_id": msg.contact_id, "last_message": msg.text, "updated_at": msg.text}},
        upsert=True,
    )
    return {"id": new_id}


@app.get("/api/messages")
def list_messages(contact_id: Optional[str] = None):
    q: Dict[str, Any] = {}
    if contact_id:
        q["contact_id"] = contact_id
    docs = get_documents("message", q, limit=200)
    for d in docs:
        d["id"] = str(d.get("_id"))
        d.pop("_id", None)
    return docs


# AI integration (simple: suggest reply)
class AIRequest(BaseModel):
    history: List[Dict[str, str]]
    instruction: Optional[str] = None


@app.post("/api/ai/suggest-reply")
def ai_suggest(req: AIRequest):
    # Local simple heuristic as a placeholder (no external deps)
    last_user = ""
    for m in reversed(req.history):
        if m.get("role") == "user":
            last_user = m.get("content", "")
            break
    suggestion = "Thanks for reaching out! Could you please share more details?"
    if any(word in last_user.lower() for word in ["price", "cost"]):
        suggestion = "Our pricing starts at $49/month. Would you like a quick demo?"
    elif any(word in last_user.lower() for word in ["trial", "demo"]):
        suggestion = "Happy to set up a demo. What time works best for you?"
    return {"suggestion": suggestion}


# WhatsApp API integration stubs
class WhatsAppSend(BaseModel):
    to: str
    text: str


@app.post("/api/whatsapp/send")
def whatsapp_send(payload: WhatsAppSend):
    # Placeholder: here you would call WhatsApp Cloud API using a token
    # Store as outbound message too
    msg = Message(contact_id=payload.to, direction="outbound", text=payload.text)
    _ = create_document("message", msg)
    return {"status": "queued"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
