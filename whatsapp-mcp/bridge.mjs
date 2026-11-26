#!/usr/bin/env node
/**
 * Forwards inbound WhatsApp group messages to the Deala webhook.
 *
 * wawatch already speaks Streamable HTTP and SSE, but its built-in webhook
 * omits the WhatsApp message id and only fires for chats someone marked
 * watched. This process:
 *   - marks every group (@g.us) watched
 *   - keeps May reply off, so wawatch will refuse sends
 *   - POSTs the SSE message, which includes the Baileys message id
 *
 * It never calls send_message or POST /api/send.
 */

const base = process.env.WAWATCH_BASE || "http://127.0.0.1:3001";
const webhook = process.env.DEALA_WEBHOOK_URL || "http://backend:8000/whatsapp/event";
const seen = new Set();

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForWawatch() {
  for (let attempt = 1; attempt <= 60; attempt++) {
    try {
      const res = await fetch(`${base}/api/state`);
      if (res.ok) return;
    } catch {
      // process still booting
    }
    await sleep(500);
  }
  throw new Error("wawatch HTTP server did not become ready");
}

async function watchGroups() {
  let res;
  try {
    res = await fetch(`${base}/api/state`);
  } catch (err) {
    console.error(`state read failed: ${err.message}`);
    return;
  }
  if (!res.ok) return;
  const state = await res.json();
  for (const chat of state.chats ?? []) {
    if (typeof chat?.id !== "string" || !chat.id.endsWith("@g.us")) continue;
    if (chat.watched && chat.mayReply !== true) continue;
    const patch = await fetch(`${base}/api/chats/${encodeURIComponent(chat.id)}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ watched: true, mayReply: false }),
    });
    if (!patch.ok) {
      console.error(`watch ${chat.id} failed: HTTP ${patch.status}`);
      continue;
    }
    console.log(`watching group ${chat.id} (${chat.name || "unnamed"}); may reply stays off`);
  }
}

function isoTime(timestamp) {
  const millis = typeof timestamp === "number" ? timestamp : Date.parse(timestamp);
  const when = Number.isFinite(millis) && millis > 0 ? millis : Date.now();
  return new Date(when).toISOString();
}

async function postEvent(message) {
  if (!message || message.fromAgent || message.fromMe || message.history) return;
  if (typeof message.chatId !== "string" || !message.chatId.endsWith("@g.us")) return;
  if (!message.id || !message.text) return;
  if (seen.has(message.id)) return;

  const body = JSON.stringify({
    text: message.text,
    chat_id: message.chatId,
    sender: message.sender || "unknown",
    timestamp: isoTime(message.timestamp),
    message_id: message.id,
  });
  const delays = [0, 1000, 4000, 16000];
  for (let i = 0; i < delays.length; i++) {
    if (delays[i]) await sleep(delays[i]);
    try {
      const res = await fetch(webhook, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body,
      });
      if (res.ok || (res.status < 500 && res.status !== 429)) {
        // 2xx is stored. Other 4xx will not succeed on retry, so stop.
        seen.add(message.id);
        if (!res.ok) console.error(`webhook HTTP ${res.status} for ${message.id}`);
        return;
      }
      console.error(`webhook HTTP ${res.status} for ${message.id}`);
    } catch (err) {
      console.error(`webhook error for ${message.id}: ${err.message}`);
    }
  }
}

async function readSse(stream) {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let split;
    while ((split = buf.indexOf("\n\n")) >= 0) {
      const raw = buf.slice(0, split);
      buf = buf.slice(split + 2);
      let event = "message";
      const data = [];
      for (const line of raw.split("\n")) {
        if (line.startsWith(":")) continue;
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data.push(line.slice(5).trim());
      }
      if (event === "state") {
        await watchGroups();
        continue;
      }
      if (event !== "message" || data.length === 0) continue;
      try {
        await postEvent(JSON.parse(data.join("\n")));
      } catch (err) {
        console.error(`bad SSE payload: ${err.message}`);
      }
    }
  }
}

async function streamForever() {
  while (true) {
    try {
      await watchGroups();
      const res = await fetch(`${base}/api/events`, { headers: { accept: "text/event-stream" } });
      if (!res.ok || !res.body) {
        console.error(`SSE HTTP ${res.status}; retrying`);
        await sleep(2000);
        continue;
      }
      console.log("SSE connected");
      await readSse(res.body);
      console.error("SSE closed; reconnecting");
    } catch (err) {
      console.error(`SSE error: ${err.message}`);
    }
    await sleep(2000);
  }
}

console.log(`deala bridge -> ${webhook}`);
console.log("send_message and POST /api/send are not used; group May reply stays off");
await waitForWawatch();
await streamForever();
