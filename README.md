# Deala

WhatsApp group posts (WTS/WTB) become a draft and an unsigned receipt. Nothing in this tree sends a WhatsApp message, signs a receipt, or approves one.

## Run

```bash
docker compose up --build
```

Services:

| Service | Role |
| --- | --- |
| `postgres` | drafts and unsigned receipts. Internal network, backend only. |
| `backend` | `POST /whatsapp/event` parses the post and writes both rows in one transaction. |
| `whatsapp-mcp` | [wawatch](https://github.com/tupe12334/wawatch) at `21cc35ebc83827173bcea51a971b9bcd4c9362f8`, HTTP/SSE on port 3001. A small bridge in the same container POSTs each inbound group message to the backend. |

The sidecar is on the `ingest` network only. It has no route to Postgres, no `DATABASE_URL`, and no signing key. Its only volume is `./wa-auth` (wawatch's data dir; Baileys session files land in `./wa-auth/auth`).

wawatch also exposes `send_message` and `POST /api/send`. Deala never calls them. The bridge watches group chats and forces **May reply** off, so wawatch rejects sends to those chats. Leave it off.

## Pair a dedicated number

Use a **dedicated WhatsApp number** for this Baileys session, never a personal one. Baileys is an unofficial linked-device client. If WhatsApp logs the session out, read access can be recovered by scanning a new QR. A ban that follows from sending is not recoverable. This build does not send; do not point a later sender at a personal number either.

1. `docker compose up --build`
2. `docker compose logs -f whatsapp-mcp`
3. On the dedicated phone: WhatsApp → Settings → Linked devices → Link a device.
4. Scan the QR printed in the logs. The first code is printed as soon as WhatsApp asks for one. If that code expires, the log says it refreshed; open `http://localhost:3001` and scan the code on the page.
5. Session keys stay in `./wa-auth`. The next start should not ask for a QR.

Post a WTS or WTB line in a **group** the linked account belongs to. The bridge ignores direct chats.

## Check that a row landed

```bash
docker compose exec postgres psql -U deala -d deala -c \
  "SELECT d.draft_text, d.reference, d.price_usd, r.id AS receipt_id, r.status
   FROM drafts d
   JOIN receipts r ON r.id = d.receipt_id
   ORDER BY d.created_at DESC
   LIMIT 5;"
```

`status` is `unsigned`. `signature` is null until a later change adds Ed25519.

Without a phone, the same write can be checked by posting a sample event (any 5xx means the row was not stored):

```bash
curl -s -X POST http://localhost:8000/whatsapp/event \
  -H 'content-type: application/json' \
  -d '{"text":"WTS 126610LN full set 2024 $14.2k","chat_id":"120363000000000000@g.us","sender":"Ada","timestamp":"2026-11-26T12:00:00Z","message_id":"SAMPLE1"}'
```

The response includes `receipt_id`. A repeat of the same `message_id` returns that same id.

## Tests

```bash
pip install -r backend/requirements-dev.txt
DATABASE_URL=postgresql://deala:deala@127.0.0.1:5432/deala pytest
```

CI runs the same tests against Postgres.

## Sidecar choice

FastAPI only accepts HTTP. It does not spawn the sidecar or speak MCP over stdio.

| Candidate | Why it was not used |
| --- | --- |
| `jlucaso1/whatsapp-mcp-ts` | stdio MCP. Base implementation, no inbound HTTP push. |
| `kahflane/whatsapp-mcp` | stdio only. Last release May 2026. QR is a tool call, not a log line. |
| `dcversus/wa-mcp` | HTTP MCP and SSE, and it is actively maintained, but inbound delivery is an agent inbox rather than a POST to our webhook. It needs Node 26 and ships a large send surface. |

`tupe12334/wawatch` is the one that already serves Streamable HTTP and SSE, prints the QR to the terminal, stores the Baileys auth directory on disk, and can POST inbound messages. Pinned to `21cc35ebc83827173bcea51a971b9bcd4c9362f8` (13 Nov 2026). Its native webhook drops the WhatsApp message id and skips unwatched chats, so the image adds a thin bridge instead of using that webhook.
