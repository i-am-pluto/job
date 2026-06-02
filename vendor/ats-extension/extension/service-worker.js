// service-worker.js (MV3, module) — bridges local WebSocket to ATS tabs.
//
// Dials out to the Python MCP server's WS server on localhost:8766.
// Auto-reconnects with exponential backoff.
//
// Protocol:
//   server -> ext : {id, action, params}
//   ext -> server : {id, ok: true, data} | {id, ok: false, error}

const WS_URL = "ws://localhost:8766";
const ATS_URL_MATCHES = [
  "https://*.myworkdayjobs.com/*",
  "https://*.wd1.myworkdayjobs.com/*",
  "https://*.wd5.myworkdayjobs.com/*",
  "https://boards.greenhouse.io/*",
  "https://job-boards.greenhouse.io/*",
];

let ws = null;
let backoff = 1000;
const MAX_BACKOFF = 30000;

function log(...a) { console.log("[ATS-SW]", ...a); }

function connect() {
  log("WS connecting", WS_URL);
  try { ws = new WebSocket(WS_URL); } catch (e) { scheduleReconnect(); return; }

  ws.onopen = () => {
    log("WS connected");
    backoff = 1000;
    ws.send(JSON.stringify({ type: "hello", role: "ats-extension" }));
  };

  ws.onmessage = async (ev) => {
    let req;
    try { req = JSON.parse(ev.data); } catch { return; }
    if (!req || !req.id || !req.action) return;
    const reply = await handle(req).catch((e) => ({
      ok: false, error: String((e && e.message) || e),
    }));
    ws.send(JSON.stringify({ id: req.id, ...reply }));
  };

  ws.onclose = () => { log("WS closed"); scheduleReconnect(); };
  ws.onerror = () => { try { ws.close(); } catch {}; };
}

function scheduleReconnect() {
  setTimeout(connect, backoff);
  backoff = Math.min(backoff * 2, MAX_BACKOFF);
}

async function getATSTab() {
  const tabs = await chrome.tabs.query({ url: ATS_URL_MATCHES });
  if (tabs.length) {
    tabs.sort((a, b) => (b.lastAccessed || 0) - (a.lastAccessed || 0));
    return tabs[0];
  }
  // Fallback: search broader patterns
  const all = await chrome.tabs.query({});
  const atsTab = all.find(t =>
    t.url && (t.url.includes("myworkdayjobs") || t.url.includes("greenhouse.io"))
  );
  if (atsTab) return atsTab;
  // No existing ATS tab — create one pointing to a known Workday tenant doc page.
  // User should navigate to a real job form manually.
  throw new Error("No ATS tab open. Open a Workday/Greenhouse job application page first.");
}

function waitForTabComplete(tabId, timeout = 20000) {
  return new Promise((resolve) => {
    const start = Date.now();
    const check = async () => {
      try {
        const t = await chrome.tabs.get(tabId);
        if (t.status === "complete") return resolve(true);
      } catch { return resolve(false); }
      if (Date.now() - start > timeout) return resolve(false);
      setTimeout(check, 400);
    };
    check();
  });
}

async function sendToTab(tabId, payload) {
  try {
    return await chrome.tabs.sendMessage(tabId, payload);
  } catch (e) {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["selectors/workday.js", "content.js"],
    });
    return await chrome.tabs.sendMessage(tabId, payload);
  }
}

async function handle(req) {
  const tab = await getATSTab();
  await waitForTabComplete(tab.id);

  const payload = { action: req.action, params: req.params || {} };
  let res = await sendToTab(tab.id, payload);

  if (res && res.ok && res.data && res.data._navigate) {
    const url = res.data._navigate;
    await chrome.tabs.update(tab.id, { url });
    await waitForTabComplete(tab.id);
    await new Promise((r) => setTimeout(r, 1500));
    res = await sendToTab(tab.id, payload);
    if (res && res.data && res.data._navigate) {
      return { ok: false, error: `Navigation loop for ${req.action}` };
    }
  }
  return res || { ok: false, error: "No response from content script" };
}

chrome.alarms.create("ats-keepalive", { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener((a) => {
  if (a.name !== "ats-keepalive") return;
  if (!ws || ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
    connect();
  }
});

connect();
