"""Postgres access. Draft and receipt are inserted in one transaction."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row

from app.agent.parser import WatchListing, render_draft

# Separate statements: psycopg rejects more than one command per execute.
_SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS receipts (
        id UUID PRIMARY KEY,
        status TEXT NOT NULL DEFAULT 'unsigned'
            CHECK (status IN ('unsigned', 'signed', 'rejected')),
        signature TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS drafts (
        id UUID PRIMARY KEY,
        receipt_id UUID NOT NULL UNIQUE REFERENCES receipts (id),
        intent TEXT NOT NULL CHECK (intent IN ('WTS', 'WTB')),
        reference TEXT NOT NULL,
        price_usd INTEGER,
        set_completeness TEXT,
        source_group TEXT NOT NULL,
        raw_text TEXT NOT NULL,
        draft_text TEXT NOT NULL,
        message_id TEXT NOT NULL UNIQUE,
        sender TEXT,
        message_timestamp TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
)


def connect() -> psycopg.Connection:
    url = os.environ["DATABASE_URL"]
    return psycopg.connect(url, row_factory=dict_row)


def init_db() -> None:
    with connect() as conn:
        for statement in _SCHEMA:
            conn.execute(statement)
        conn.commit()


def insert_draft_and_receipt(
    listing: WatchListing,
    *,
    message_id: str,
    sender: str,
    message_timestamp: datetime,
) -> dict[str, Any]:
    """Insert the unsigned receipt and the draft, or return the existing pair.

    Both rows are written in a single transaction. A failure rolls back and
    raises so the caller can refuse to acknowledge the event.
    """
    receipt_id = uuid4()
    draft_id = uuid4()
    with connect() as conn:
        try:
            with conn.transaction():
                existing = _existing(conn, message_id)
                if existing:
                    return _public(existing, duplicate=True)
                conn.execute(
                    "INSERT INTO receipts (id, status) VALUES (%s, 'unsigned')",
                    (receipt_id,),
                )
                conn.execute(
                    """
                    INSERT INTO drafts (
                        id, receipt_id, intent, reference, price_usd,
                        set_completeness, source_group, raw_text, draft_text,
                        message_id, sender, message_timestamp
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        draft_id,
                        receipt_id,
                        listing.intent,
                        listing.reference,
                        listing.price_usd,
                        listing.set_completeness,
                        listing.source_group,
                        listing.raw_text,
                        render_draft(listing),
                        message_id,
                        sender,
                        message_timestamp,
                    ),
                )
        except UniqueViolation:
            existing = _existing(conn, message_id)
            if existing:
                return _public(existing, duplicate=True)
            raise
    return {
        "status": "created",
        "receipt_id": str(receipt_id),
        "draft_id": str(draft_id),
        "receipt_status": "unsigned",
    }


def _existing(conn: psycopg.Connection, message_id: str) -> dict[str, Any] | None:
    return conn.execute(
        """
        SELECT d.id AS draft_id, d.receipt_id, r.status AS receipt_status
        FROM drafts d
        JOIN receipts r ON r.id = d.receipt_id
        WHERE d.message_id = %s
        """,
        (message_id,),
    ).fetchone()


def _public(row: dict[str, Any], *, duplicate: bool) -> dict[str, Any]:
    receipt_id: UUID = row["receipt_id"]
    draft_id: UUID = row["draft_id"]
    return {
        "status": "duplicate" if duplicate else "created",
        "receipt_id": str(receipt_id),
        "draft_id": str(draft_id),
        "receipt_status": row["receipt_status"],
    }
