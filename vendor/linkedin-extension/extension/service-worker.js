// service-worker.js (MV3, module) — bridges the local WebSocket to LinkedIn tabs.
//
// MV3 SWs cannot listen on a port, but can dial out. The Python MCP server owns
// the WS server on localhost:8765; we connect as a client and auto-reconnect.
//
// Protocol:
//   server -> ext : {id, action, params}
//   ext -> server : {id, ok: true, data} | {id, ok: false, error}

const WS_URL = "ws://localhost:8765";
const LINKEDIN_MATCH = "https://www.linkedin.com/*";

let ws = null;
let backoff = 1000; // ms, exponential up to 30s
const MAX_BACKOFF = 30000;

function log(...a) {
  console.log("[LI-SW]", ...a);
}

function connect() {
  log("WS connecting", WS_URL);
  try {
    ws = new WebSocket(WS_URL);
  } catch (e) {
    scheduleReconnect();
    return;
  }

  ws.onopen = () => {
    log("WS connected");
    backoff = 1000;
    ws.send(JSON.stringify({ type: "hello", role: "linkedin-extension" }));
  };

  ws.onmessage = async (ev) => {
    let req;
    try {
      req = JSON.parse(ev.data);
    } catch {
      return;
    }
    if (!req || !req.id || !req.action) return;
    const reply = await handle(req).catch((e) => ({
      ok: false,
      error: String((e && e.message) || e),
    }));
    ws.send(JSON.stringify({ id: req.id, ...reply }));
  };

  ws.onclose = () => {
    log("WS closed");
    scheduleReconnect();
  };
  ws.onerror = () => {
    try {
      ws.close();
    } catch {}
  };
}

function scheduleReconnect() {
  setTimeout(connect, backoff);
  backoff = Math.min(backoff * 2, MAX_BACKOFF);
}

// ------------------------------------------------------------------ //
// Tab management
// ------------------------------------------------------------------ //
async function getLinkedInTab() {
  const tabs = await chrome.tabs.query({ url: LINKEDIN_MATCH });
  if (tabs.length) {
    // Prefer the most recently active LinkedIn tab.
    tabs.sort((a, b) => (b.lastAccessed || 0) - (a.lastAccessed || 0));
    return tabs[0];
  }
  return await chrome.tabs.create({ url: "https://www.linkedin.com/feed/", active: false });
}

function waitForTabComplete(tabId, timeout = 20000) {
  return new Promise((resolve) => {
    const start = Date.now();
    const check = async () => {
      try {
        const t = await chrome.tabs.get(tabId);
        if (t.status === "complete") return resolve(true);
      } catch {
        return resolve(false);
      }
      if (Date.now() - start > timeout) return resolve(false);
      setTimeout(check, 400);
    };
    check();
  });
}

// Send a message to the content script; reinject if not present.
async function sendToTab(tabId, payload) {
  try {
    return await chrome.tabs.sendMessage(tabId, payload);
  } catch (e) {
    // Content script not loaded yet (e.g. fresh tab) — inject and retry.
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["selectors.js", "content.js"],
    });
    return await chrome.tabs.sendMessage(tabId, payload);
  }
}

// ------------------------------------------------------------------ //
// Command handler with navigate-then-retry
// ------------------------------------------------------------------ //
async function handle(req) {
  const tab = await getLinkedInTab();
  await waitForTabComplete(tab.id);

  const payload = { action: req.action, params: req.params || {} };
  let res = await sendToTab(tab.id, payload);

  // Content script asked us to navigate first, then re-run the same action.
  if (res && res.ok && res.data && res.data._navigate) {
    const url = res.data._navigate;
    // openJobs is satisfied by navigation alone.
    if (req.action === "openJobs") {
      await chrome.tabs.update(tab.id, { url });
      await waitForTabComplete(tab.id);
      return { ok: true, data: { url: res.data.url, opened: true } };
    }
    await chrome.tabs.update(tab.id, { url });
    await waitForTabComplete(tab.id);
    // Give SPA content a moment to render after load.
    await new Promise((r) => setTimeout(r, 1500));
    res = await sendToTab(tab.id, payload);
    if (res && res.data && res.data._navigate) {
      return { ok: false, error: `Navigation loop for ${req.action}` };
    }
  }
  return res || { ok: false, error: "No response from content script" };
}

// Keepalive: MV3 terminates idle SWs and setTimeout dies with them. A periodic
// alarm wakes the SW and ensures the socket is (re)connected.
chrome.alarms.create("li-keepalive", { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener((a) => {
  if (a.name !== "li-keepalive") return;
  if (!ws || ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
    connect();
  }
});

connect();
