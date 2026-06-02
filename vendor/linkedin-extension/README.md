# LinkedIn Control Suite (Chrome extension + MCP server)

Replaces the old `vendor/linkedin-selenium` headless-browser server. Instead of
logging into a separate Chrome with stored credentials and fighting bot
detection, this drives the user's **already-logged-in** LinkedIn tab through a
small Chrome extension, controlled over a localhost WebSocket by a Python
FastMCP server.

```
Claude ──stdio──> MCP server (server/main.py, FastMCP)
                      │  WebSocket SERVER on ws://localhost:8765 (bridge.py)
                      ▲
                      │  extension service worker = WS CLIENT (dials in, auto-reconnect)
        Chrome extension (extension/)
                      │  chrome.tabs.sendMessage / chrome.scripting
                      ▼
              content.js on www.linkedin.com  ──>  DOM read/write  ──>  JSON
```

## Tools

| Tool | Params | Returns |
| --- | --- | --- |
| `linkedin_status` | — | `{connected, logged_in, active_tab_url}` |
| `linkedin_get_connections` | `max_count=100` | `{connections[], total_fetched}` |
| `linkedin_get_conversations` | `limit=20` | `{threads[]}` |
| `linkedin_get_thread_messages` | `thread_id, limit=50` | `{messages[], thread_id}` |
| `linkedin_send_message` | `profile_url, message, attachment_path=""` | `{success, error}` |
| `linkedin_search_posts` | `keywords, date_filter="past-week", limit=15` | `{posts[], query}` |
| `linkedin_open_jobs` | `keywords, location="", easy_apply_only=true, date_posted=""` | `{url, opened}` |
| `linkedin_read_jobs` | `limit=25` | `{jobs[]}` |
| `linkedin_open_job` | `job_id` | `{job_id, title, company, location, description, easy_apply, apply_url}` |

Every tool returns `{"success": false, "error": "..."}` on failure (extension
not connected, timeout, selector miss).

## Setup

1. **Install Python deps**

   ```bash
   pip3 install -r vendor/linkedin-extension/server/requirements.txt
   ```

2. **Load the extension** in Chrome

   - Open `chrome://extensions`, enable **Developer mode**.
   - **Load unpacked** → select `vendor/linkedin-extension/extension/`.
   - Open the extension's **service worker** console; you should see
     `[LI-SW] WS connecting` then `WS connected` once the server is running.

3. **Register the MCP server** — already wired in the repo-root `.mcp.json`:

   ```json
   {
     "mcpServers": {
       "linkedin-extension": {
         "command": "python3",
         "args": ["vendor/linkedin-extension/server/main.py"]
       }
     }
   }
   ```

   The MCP server starts the WebSocket bridge lazily on the first tool call.

4. **Be logged into LinkedIn** in any Chrome tab (or none — the extension opens a
   `linkedin.com/feed/` tab on demand).

### Standalone test (without an MCP client)

```bash
python3 vendor/linkedin-extension/server/main.py
```

This starts the FastMCP stdio server; the WS bridge comes up on the first tool
call. Watch the extension SW console for `WS connected`.

## Notes / limitations

- **No credentials.** Uses the live Chrome session. The old
  `LINKEDIN_EMAIL` / `LINKEDIN_PASSWORD` `.env` keys are no longer used (safe to
  leave or remove).
- **Attachments on DMs**: Chrome blocks programmatic file selection from
  extensions. `linkedin_send_message` with `attachment_path` still sends the text
  and returns `error="attachment_unsupported"`; attach the PDF via
  claude-in-chrome if needed.
- **Selector drift**: all LinkedIn CSS lives in `extension/selectors.js`
  (`SELECTOR_VERSION`). Fix DOM changes there in one place.
- **Skills unchanged**: `skills/linkedin` and `skills/networking` still use
  claude-in-chrome. Rewiring them to these tools is a separate follow-up.

## Troubleshooting

- `Extension not connected` → confirm the extension is loaded and a Chrome
  window is open; check the SW console for `WS connected`. The SW reconnects with
  backoff and a 30s keepalive alarm.
- `Timed out waiting for '<action>'` → LinkedIn DOM likely changed or the page
  was mid-navigation; re-run, and if persistent update `selectors.js`.
- `Navigation loop for <action>` → the page never reached the expected URL;
  ensure you're logged in and the URL isn't being redirected (e.g. checkpoint).
