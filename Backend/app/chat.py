# app/chat.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Any, List, Dict
import sqlite3
import os
import json
import re
from difflib import SequenceMatcher
import logging
from app.auth import get_current_user  # requires your existing auth
from app.config import CHAT_DB_PATH  # add CHAT_DB_PATH = DATA_DIR / "chat.db" in config.py
from datetime import datetime

# optional: load env
from dotenv import load_dotenv
load_dotenv()

# Optional LLM config (OpenAI)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").lower()  # set to "openai" to enable
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger("pulsebot")
logger.setLevel(logging.INFO)

# ----------------------------
# Intents + improved matcher
# ----------------------------
INTENTS = [
    {
        "name": "greet",
        "examples": ["hi", "hello", "hey", "good morning", "good evening", "hiya"],
        "responses": ["Hi! I'm PulseBot — I can help with donation, matching or uploads. How can I help you today?"]
    },
    {
        "name": "how_to_donate",
        "examples": [
            "how to donate", "how do i donate", "i want to donate", "donate", "donation",
            "donating", "how do i give blood", "steps to donate", "donation steps"
        ],
        "responses": [
            "Steps to donate:\n1) Sign up or login → Donate tab\n2) Fill your contact & location\n3) Mark availability\n4) Hospital can contact you via phone. Need more details?"
        ]
    },
    {
        "name": "upload_csv_format",
        "examples": [
            "csv format", "donors csv format", "columns required", "what columns", "csv headers",
            "donors csv", "requests csv format", "hospitals csv format"
        ],
        "responses": [
            "Donors CSV should contain headers: donor_id,name,blood_group,phone,lat,lon,availability,last_donation_date\nExample row: D100,John Doe,O+,9999999999,12.9716,77.5946,yes,2025-08-01"
        ]
    },
    {
        "name": "match_help",
        "examples": [
            "how does matching work", "what is distance score", "explain matching algorithm",
            "how matching works", "how to match", "matching", "match", "how matching work"
        ],
        # friendly user-focused default response (not formula)
        "responses": [
            "To find matching donors quickly, you can either: (1) enter your location (or allow the browser to use your current location) and the required blood group, or (2) ask the hospital admin to upload datasets. Select a topic below to learn more."
        ]
    },
]

# Quick map for single-word inputs
KEYWORD_INTENT_MAP = {
    "donate": "how_to_donate",
    "donation": "how_to_donate",
    "donating": "how_to_donate",
    "csv": "upload_csv_format",
    "columns": "upload_csv_format",
    "headers": "upload_csv_format",
    "match": "match_help",
    "matching": "match_help",
    "distance": "match_help",
}

FALLBACK_MESSAGE = "Sorry, I didn't understand. Try: 'How to donate', 'CSV format', or 'How matching works'."

# match_help subtopics (frontend can render these as dropdown/quick options)
MATCH_HELP_OPTIONS = [
    "How to search for matches (step-by-step)",
    "Map view — what pins mean",
    "Interpreting distance & score",
    "Urgency levels and priority",
    "How hospitals upload data"
]

# ----------------------------
# Utilities: DB helpers
# ----------------------------
def ensure_chat_db():
    CHAT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CHAT_DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        role TEXT,
        message TEXT,
        response TEXT,
        source TEXT,
        intent TEXT,
        options TEXT,
        meta TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def store_conversation(user_id: str, role: str, message: str, response: str,
                       source: str = "rule", intent: Optional[str] = None,
                       options: Optional[List[str]] = None, meta: Optional[dict] = None):
    try:
        conn = sqlite3.connect(CHAT_DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO conversations (user_id, role, message, response, source, intent, options, meta) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, role, message, response, source, intent, json.dumps(options) if options else None, json.dumps(meta) if meta else None)
        )
        conn.commit()
    except Exception as e:
        logger.exception("Failed to store conversation: %s", e)
    finally:
        conn.close()

ensure_chat_db()

# ----------------------------
# Simple improved matcher
# ----------------------------
def _clean_text(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s

def simple_intent_match(text: str):
    txt = _clean_text(text)
    if not txt:
        return None, None

    # 1) keyword quick check (word-level)
    for kw, intent_name in KEYWORD_INTENT_MAP.items():
        if kw in txt.split():
            for it in INTENTS:
                if it["name"] == intent_name:
                    return it["name"], it["responses"][0]

    # 2) token subset matching for example phrases
    tokens = set(txt.split())
    for it in INTENTS:
        for ex in it["examples"]:
            ex_clean = _clean_text(ex)
            ex_tokens = set(ex_clean.split())
            if ex_tokens and ex_tokens.issubset(tokens):
                return it["name"], it["responses"][0]

    # 3) fuzzy similarity across examples
    best_ratio = 0.0
    best_match = (None, None)
    for it in INTENTS:
        for ex in it["examples"]:
            ex_clean = _clean_text(ex)
            if not ex_clean:
                continue
            ratio = SequenceMatcher(None, ex_clean, txt).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = (it["name"], it["responses"][0])

    if best_ratio >= 0.6:
        return best_match

    return None, None

# ----------------------------
# Optional LLM fallback (OpenAI)
# ----------------------------
import requests

def call_openai_fallback(user_text: str) -> str:
    if not OPENAI_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": "You are PulseNet assistant. Be concise, helpful, and avoid direct medical advice. Refer users to hospitals when necessary."},
            {"role": "user", "content": user_text}
        ],
        "max_tokens": 300,
        "temperature": 0.2
    }
    r = requests.post(url, headers=headers, json=payload, timeout=15)
    r.raise_for_status()
    data = r.json()
    # defensive extraction
    choices = data.get("choices")
    if choices and len(choices) > 0:
        msg = choices[0].get("message", {}).get("content")
        if msg:
            return msg.strip()
    # fallback if weird response
    return FALLBACK_MESSAGE

# ----------------------------
# Request/Response models
# ----------------------------
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None  # optional override

class ChatResponse(BaseModel):
    response: str
    source: str
    intent: Optional[str] = None
    options: Optional[List[str]] = None  # new: frontend can render dropdown/buttons

# ----------------------------
# Endpoints
# ----------------------------
@router.post("/", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest, current_user: Any = Depends(get_current_user)):
    text = (req.message or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty message")

    user_id = req.user_id or (current_user["email"] if current_user else "anonymous")
    role = (current_user["role"] if current_user else "guest")

    # 1) rule-based
    intent, resp = simple_intent_match(text)
    if intent:
        # If match_help, return friendly guidance and options for subtopics instead of formula
        if intent == "match_help":
            friendly = resp  # the friendly text defined in INTENTS
            options = MATCH_HELP_OPTIONS
            store_conversation(user_id, role, text, friendly, source="rule", intent=intent, options=options)
            return {"response": friendly, "source": "rule", "intent": intent, "options": options}

        # default for other intents: simple text only
        store_conversation(user_id, role, text, resp, source="rule", intent=intent)
        return {"response": resp, "source": "rule", "intent": intent, "options": None}

    # 2) optional LLM fallback
    if LLM_PROVIDER == "openai" and OPENAI_KEY:
        try:
            llm_resp = call_openai_fallback(text)
            store_conversation(user_id, role, text, llm_resp, source="llm", intent=None)
            return {"response": llm_resp, "source": "llm", "intent": None, "options": None}
        except Exception as e:
            logger.exception("LLM fallback failed: %s", e)

    # 3) final fallback
    store_conversation(user_id, role, text, FALLBACK_MESSAGE, source="fallback", intent=None)
    return {"response": FALLBACK_MESSAGE, "source": "fallback", "intent": None, "options": None}

# History endpoint — hospital/admin only
@router.get("/history")
def chat_history(limit: int = 200, current_user: Any = Depends(get_current_user)):
    # only allow hospital role to view history
    role = current_user.get("role") if current_user else None
    if role != "hospital":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    conn = sqlite3.connect(CHAT_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, role, message, response, source, intent, options, meta, created_at FROM conversations ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"rows": rows}

# Optional endpoint to fetch recent unmatched queries (for tuning intents)
@router.get("/recent-unmatched")
def recent_unmatched(limit: int = 100, current_user: Any = Depends(get_current_user)):
    role = current_user.get("role") if current_user else None
    if role != "hospital":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    conn = sqlite3.connect(CHAT_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # unmatched = source == 'fallback'
    cur.execute("SELECT id, user_id, message, created_at FROM conversations WHERE source = 'fallback' ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"rows": rows}
