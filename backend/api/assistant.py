"""Admission Assistant chatbot API.

Every endpoint requires a signed-in user (the existing session auth). What the
assistant may reveal follows the existing roles: lead-level scores and SHAP
explanations only for admission and marketing managers (the same rule as the
/leads router), a student's own enquiries only for that student.
"""
from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from api.auth import current_user
from database.connection import get_db
from database.models import AssistantMessage, User
from services.assistant import engine, llm

log = logging.getLogger("assistant.api")
router = APIRouter(prefix="/assistant", tags=["admission assistant"])

MAX_MESSAGE = 1000
HISTORY_KEEP = 200            # messages kept per user
RATE_LIMIT = 20               # messages ...
RATE_WINDOW = 60.0            # ... per this many seconds, per user
_recent: dict[str, deque] = defaultdict(deque)
_rate_lock = threading.Lock()


class ChatContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str | None = Field(default=None, max_length=200)
    lead_id: str | None = Field(default=None, max_length=64, pattern=r"^[A-Za-z0-9-]+$")


class ChatInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    message: str = Field(min_length=1, max_length=MAX_MESSAGE)
    context: ChatContext | None = None

    @field_validator("message")
    @classmethod
    def not_blank(cls, value: str) -> str:
        cleaned = "".join(ch for ch in value if ch.isprintable() or ch in "\n\t").strip()
        if not cleaned:
            raise ValueError("Message cannot be empty")
        return cleaned


def _check_rate(user_id: str) -> None:
    now = time.monotonic()
    with _rate_lock:
        window = _recent[user_id]
        while window and now - window[0] > RATE_WINDOW:
            window.popleft()
        if len(window) >= RATE_LIMIT:
            raise HTTPException(429, "You're sending messages too quickly. Please wait a moment and try again.")
        window.append(now)


def _serialize(item: AssistantMessage) -> dict:
    payload = item.payload or {}
    return {"id": item.id, "role": item.role, "text": item.content, "created_at": item.created_at, **payload}


def _save(db: Session, user_id: str, role: str, content: str, payload: dict | None, at: float) -> AssistantMessage:
    item = AssistantMessage(id=str(uuid.uuid4()), user_id=user_id, role=role, content=content,
                            payload=payload, created_at=at)
    db.add(item)
    return item


def _trim_history(db: Session, user_id: str) -> None:
    stale = (db.query(AssistantMessage.id).filter_by(user_id=user_id)
             .order_by(AssistantMessage.created_at.desc()).offset(HISTORY_KEEP).all())
    if stale:
        db.query(AssistantMessage).filter(AssistantMessage.id.in_([row.id for row in stale])) \
            .delete(synchronize_session=False)


@router.get("/welcome")
def welcome(lead_id: str | None = Query(default=None, max_length=64), user: User = Depends(current_user)):
    data = engine.welcome(user.role, user.name, has_lead=bool(lead_id) and user.role in ("admission_manager", "marketing_manager"))
    return {**data, "role": user.role, "llm_enabled": llm.enabled()}


@router.post("/chat")
def chat(data: ChatInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _check_rate(user.id)
    context = data.context.model_dump() if data.context else {}
    try:
        reply = engine.answer(data.message, user, db, context)
        reply = llm.polish(data.message, reply)
    except HTTPException:
        raise
    except Exception:
        log.exception("Assistant failed to answer")
        raise HTTPException(500, "The assistant couldn't answer just now. Please try again.")

    result = reply.to_dict()
    payload = {key: result[key] for key in ("kind", "suggestions", "links", "card", "notice", "sources", "engine", "confidence")}
    now = time.time()
    _save(db, user.id, "user", data.message, {"context": context} if context else None, now)
    saved = _save(db, user.id, "assistant", reply.text, payload, now + 0.001)
    _trim_history(db, user.id)
    db.commit()
    return _serialize(saved)


@router.get("/history")
def history(limit: int = Query(default=50, ge=1, le=HISTORY_KEEP), user: User = Depends(current_user),
            db: Session = Depends(get_db)):
    rows = (db.query(AssistantMessage).filter_by(user_id=user.id)
            .order_by(AssistantMessage.created_at.desc()).limit(limit).all())
    return [_serialize(row) for row in reversed(rows)]


@router.delete("/history")
def clear_history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    deleted = db.query(AssistantMessage).filter_by(user_id=user.id).delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted}
