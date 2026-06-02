# ATS Control Suite (Chrome extension + MCP server)

Same architecture as `vendor/linkedin-extension/`. A Chrome extension inside your
**already-logged-in** browser session drives ATS forms (Workday, Greenhouse) with
DOM-native reads and writes — no screenshots, no coordinate clicks, no
bot-detection fight.

```
Claude ──stdio──> MCP server (server/main.py, FastMCP)
                      │  WebSocket SERVER on ws://localhost:8766 (bridge.py)
                      ▲
                      │  extension service worker = WS CLIENT (dials in, auto-reconnect)
        Chrome extension (extension/)
                      │  chrome.tabs.sendMessage / chrome.scripting
                      ▼
              content.js on myworkdayjobs.com  ──>  DOM read/write  ──>  JSON
```

## Tools

| Tool | Params | Returns |
| --- | --- | --- |
| `ats_status` | — | `{connected, ats, logged_in, active_tab_url, selector_version}` |
| `ats_detect` | — | `{ats, step, url}` |
| `ats_read_form` | — | `{ats, step, fields: [{label, type, value, required, options}]}` |
| `ats_fill_form` | `answers: {label: value}` | `{filled, notFound, step}` |
| `ats_upload_resume` | `file_path=""` | `{success, native_file_dialog, selector}` |
| `ats_next_step` | — | `{success, step_before, step_after, has_errors}` |
| `ats_submit` | — | `{success, submitted}` |
| `ats_audit_selectors` | — | selector drift detection |
| `ats_probe` | `selectors, limit, attr` | candidate selector tester |

## Setup

1. **Install Python deps**

   ```bash
   pip3 install -r vendor/ats-extension/server/requirements.txt
   ```

2. **Load the extension** in Chrome

   - Open `chrome://extensions`, enable **Developer mode**.
   - **Load unpacked** → select `vendor/ats-extension/extension/`.
   - Open the extension's **service worker** console; you should see
     `[ATS-SW] WS connecting` then `WS connected` once the server is running.

3. **Register the MCP server** — already wired in the repo-root `.mcp.json`:

   ```json
   {
     "mcpServers": {
       "ats-extension": {
         "command": "python3",
         "args": ["vendor/ats-extension/server/main.py"]
       }
     }
   }
   ```

4. **Log into each Workday tenant once by hand.** The extension reuses your
   persisted session. Do NOT automate Workday account creation or email
   verification — that is precisely what fails (pipeline evidence: Motorola,
   Sabre, BlackLine, Amadeus, Qualys, GE Vernova).

## Login policy (critical)

The extension runs in your already-logged-in Chrome session. For each Workday
tenant (`foo.wd1.myworkdayjobs.com`):
- Log in once manually in Chrome.
- The session persists (cookie/localStorage) for all future applies.
- `ats_status` returns `logged_in: false` if it detects a login wall.
- If the session expires after ~30 days, re-login manually.

## Notes

- **File upload**: Chrome extensions cannot set file input values programmatically.
  `ats_upload_resume` returns the file input selector; use claude-in-chrome's
  `file_upload` tool with that selector.
- **Selector drift**: Workday uses `[data-automation-id]` attributes which are
  stable across most tenants. Run `ats_audit_selectors` on a live form to detect
  drift; fix count=0 selectors in `selectors/workday.js` and bump the version.
- **Verification scripts** (run with the extension loaded + a Workday tab open):
  - `python3 server/verify.py` — smoke test: status, detect, read_form, audit.
  - `python3 server/audit.py` — audit every selector against the current step
    (XX=invalid CSS, !!=count 0, OK=matched). Step through the form and re-run.
- **Multi-ATS design**: `selectors/` dir supports per-ATS selector files
  (workday.js, greenhouse.js, lever.js). The content script dispatches by URL
  pattern. Currently only Workday is shipped.
