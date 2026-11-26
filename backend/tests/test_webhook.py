"""Webhook tests against Postgres.

DATABASE_URL must point at an empty-able deala database. CI and local dev
both use postgresql://deala:deala@127.0.0.1:5432/deala.
"""

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://deala:deala@127.0.0.1:5432/deala",
)

from app.db import connect  # noqa: E402
from app.main import app  # noqa: E402

WTS = {
    "text": "WTS 126610LN full set 2024 $14.2k",
    "chat_id": "120363000000000000@g.us",
    "sender": "Ada",
    "timestamp": "2026-11-26T12:00:00Z",
    "message_id": "SAMPLE-WTS-1",
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_tables(client):
    _truncate()
    yield
    _truncate()


def _truncate() -> None:
    with connect() as conn:
        conn.execute("TRUNCATE TABLE drafts, receipts")
        conn.commit()


def _counts() -> tuple[int, int]:
    with connect() as conn:
        drafts = conn.execute("SELECT count(*) AS n FROM drafts").fetchone()["n"]
        receipts = conn.execute("SELECT count(*) AS n FROM receipts").fetchone()["n"]
    return drafts, receipts


def test_wts_event_creates_draft_and_unsigned_receipt(client):
    response = client.post("/whatsapp/event", json=WTS)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "created"
    assert body["receipt_status"] == "unsigned"
    assert body["receipt_id"]
    assert body["draft_id"]

    with connect() as conn:
        row = conn.execute(
            """
            SELECT d.intent, d.reference, d.price_usd, d.set_completeness,
                   d.draft_text, d.source_group, d.message_id, d.sender,
                   r.id AS receipt_id, r.status, r.signature
            FROM drafts d
            JOIN receipts r ON r.id = d.receipt_id
            WHERE d.message_id = %s
            """,
            (WTS["message_id"],),
        ).fetchone()
    assert row["intent"] == "WTS"
    assert row["reference"] == "126610LN"
    assert row["price_usd"] == 14200
    assert row["set_completeness"] == "full set"
    assert row["draft_text"] == "WTS 126610LN | full set | $14,200"
    assert row["source_group"] == WTS["chat_id"]
    assert row["sender"] == "Ada"
    assert str(row["receipt_id"]) == body["receipt_id"]
    assert row["status"] == "unsigned"
    assert row["signature"] is None


def test_duplicate_event_returns_the_same_receipt(client):
    first = client.post("/whatsapp/event", json=WTS).json()
    second = client.post("/whatsapp/event", json=WTS)
    assert second.status_code == 200
    body = second.json()
    assert body["status"] == "duplicate"
    assert body["receipt_id"] == first["receipt_id"]
    assert _counts() == (1, 1)


def test_unknown_intent_is_acknowledged_without_rows(client):
    response = client.post(
        "/whatsapp/event",
        json={
            **WTS,
            "text": "offset 126610LN full set $14.2k",
            "message_id": "SAMPLE-OFFSET",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}
    assert _counts() == (0, 0)


def test_write_failure_is_non_2xx_and_rolls_back(client, monkeypatch):
    import app.db as db

    original = db.connect

    class Proxy:
        def __init__(self, conn):
            self._conn = conn

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return self._conn.__exit__(exc_type, exc, tb)

        def transaction(self):
            return self._conn.transaction()

        def execute(self, query, params=None, **kwargs):
            sql = query if isinstance(query, str) else str(query)
            if "INTO drafts" in sql:
                raise RuntimeError("forced write failure")
            return self._conn.execute(query, params, **kwargs)

    monkeypatch.setattr(db, "connect", lambda: Proxy(original()))

    response = client.post(
        "/whatsapp/event",
        json={**WTS, "message_id": "SAMPLE-FAIL"},
    )
    assert response.status_code >= 400
    assert response.status_code < 600
    assert "receipt_id" not in response.json()
    # The receipt insert is in the same transaction as the draft insert,
    # so a failure on the draft leaves neither row.
    assert _counts() == (0, 0)
