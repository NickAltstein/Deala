"""Inbound WhatsApp webhook.

The sidecar POSTs one raw group message here. This process does not start
WhatsApp, does not speak stdio to it, and has no code path that sends a message.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from app.agent.parser import extract_watch_details
from app.db import insert_draft_and_receipt

logger = logging.getLogger(__name__)

router = APIRouter()

_STORABLE = {"WTS", "WTB"}


class WhatsAppEvent(BaseModel):
    """Raw group message from the sidecar. Extra keys are ignored."""

    model_config = ConfigDict(extra="ignore")

    text: str
    chat_id: str
    sender: str
    timestamp: datetime
    message_id: str


@router.post("/whatsapp/event")
def whatsapp_event(event: WhatsAppEvent) -> dict:
    listing = extract_watch_details(event.text, source_group=event.chat_id)
    if listing is None or listing.intent not in _STORABLE:
        return {"status": "ignored"}

    timestamp = event.timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    try:
        # One transaction. Any error becomes a non-2xx response so the sidecar
        # does not treat the event as acknowledged.
        return insert_draft_and_receipt(
            listing,
            message_id=event.message_id,
            sender=event.sender,
            message_timestamp=timestamp,
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("failed to store draft for message %s", event.message_id)
        raise HTTPException(status_code=503, detail="failed to store draft") from None
