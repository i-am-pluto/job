// content.js — injected on www.linkedin.com.
// Implements every LinkedIn action against the live DOM and returns plain JSON.
// Dispatched by the service worker via chrome.tabs.sendMessage({action, params}).
//
// Relies on window.LI_SEL (selectors.js, loaded first).

(() => {
  const S = window.LI_SEL;

  // ----------------------------------------------------------------- //
  // DOM helpers (analogues of selenium page_helpers.py)
  // ----------------------------------------------------------------- //
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  // CLAUDE.md rule #8: get_page_text lies about visibility. Use offsetParent.
  const isVisible = (el) => !!el && el.offsetParent !== null;

  const text = (root, sel, def = "") => {
    const el = root.querySelector(sel);
    return el ? el.textContent.trim().replace(/\s+/g, " ") : def;
  };

  const attr = (root, sel, name, def = "") => {
    const el = root.querySelector(sel);
    return el ? el.getAttribute(name) || def : def;
  };

  const stripQuery = (url) => (url ? url.split("?")[0] : url);

  // Wait until selector appears (or timeout). Returns the element or null.
  async function waitFor(sel, timeout = 12000) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      const el = document.querySelector(sel);
      if (el) return el;
      await sleep(250);
    }
    return null;
  }

  // Incrementally scroll the page (or a container) to trigger lazy-load,
  // collecting unique cards until target count or no growth.
  async function scrollCollect(cardSel, target, scrollEl = null, maxRounds = 25) {
    let seen = 0;
    let stale = 0;
    for (let i = 0; i < maxRounds; i++) {
      const count = document.querySelectorAll(cardSel).length;
      if (count >= target) break;
      if (count === seen) {
        stale++;
        if (stale >= 3) break;
      } else {
        stale = 0;
        seen = count;
      }
      if (scrollEl) {
        scrollEl.scrollTop = scrollEl.scrollHeight;
      } else {
        window.scrollTo(0, document.body.scrollHeight);
      }
      await sleep(900 + Math.random() * 800);
    }
    return [...document.querySelectorAll(cardSel)];
  }

  // Fire realistic events so LinkedIn's React enables Send.
  function setContentEditable(el, value) {
    el.focus();
    el.textContent = "";
    // execCommand keeps React's listeners happy on the contenteditable.
    document.execCommand && document.execCommand("insertText", false, value);
    if (!el.textContent) el.textContent = value;
    el.dispatchEvent(new InputEvent("input", { bubbles: true, data: value }));
    el.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true }));
  }

  const checkRateLimit = () => {
    const body = document.body ? document.body.innerText : "";
    return S.RATE_LIMIT_STRINGS.some((s) => body.includes(s));
  };

  // Profile/action buttons use hashed classes and often no aria-label — the only
  // stable signal is the visible TEXT. Match buttons by exact/regex text.
  const visibleButtons = (root = document) =>
    [...root.querySelectorAll("button")].filter(isVisible);
  const btnByText = (re, root = document) =>
    visibleButtons(root).find((b) => re.test(b.textContent.trim()));
  const btnByLabel = (label, root = document) =>
    [...root.querySelectorAll(`button[aria-label='${label}']`)].find(isVisible);

  const onMessaging = () => location.pathname.startsWith("/messaging");

  // ----------------------------------------------------------------- //
  // Actions
  // ----------------------------------------------------------------- //
  const actions = {
    async status() {
      // LinkedIn migrated to CSS modules — old .global-nav__me* classes are gone.
      // Use data-testid="primary-nav" (stable) + nav element + URL pattern as signals.
      const onLogin =
        location.pathname.startsWith("/login") ||
        location.pathname.startsWith("/checkpoint") ||
        !!document.querySelector("#username, input[name='session_key']");
      const authed =
        !!document.querySelector(S.NAV_ME) ||
        /linkedin\.com\/(feed|in|jobs|messaging|mynetwork)/.test(location.href);
      return {
        logged_in: authed && !onLogin,
        active_tab_url: location.href,
        selector_version: S.SELECTOR_VERSION,
      };
    },

    async getConnections({ max_count = 100 } = {}) {
      if (!location.href.startsWith(S.CONNECTIONS)) {
        return { _navigate: S.CONNECTIONS };
      }
      // New structure: cards are direct [data-display-contents] children of lazy-column.
      await scrollCollect(S.CONNECTION_CARD, max_count);
      const seen = new Set();
      const connections = [];
      for (const card of document.querySelectorAll(S.CONNECTION_CARD)) {
        // Each card has two a[href*="/in/"] links: photo (has img) and name (no img).
        const nameLink = [...card.querySelectorAll('a[href*="/in/"]')]
          .find((a) => !a.querySelector("img"));
        if (!nameLink) continue;
        const url = stripQuery(nameLink.href);
        if (seen.has(url)) continue;
        seen.add(url);
        const innerDiv = nameLink.querySelector("div");
        const name = innerDiv?.querySelector("p")?.textContent?.trim() ||
          nameLink.textContent.trim().split(/[\n•]/)[0].trim();
        const headline = innerDiv?.querySelector("div")?.textContent?.trim() || "";
        const connected_at = nameLink.nextElementSibling?.textContent?.trim() || "";
        connections.push({ name, profile_url: url, headline, connected_at });
        if (connections.length >= max_count) break;
      }
      return { connections, total_fetched: connections.length };
    },

    async getConversations({ limit = 20 } = {}) {
      if (!onMessaging()) return { _navigate: S.MESSAGING };
      await waitFor(S.MSG_THREAD, 10000);
      const items = [...document.querySelectorAll(S.MSG_THREAD)].slice(0, limit);
      const threads = items.map((t) => {
        // LinkedIn removed anchor tags from thread list items — no href-based thread_id.
        // Use participant name slug as fallback; callers needing thread nav should get
        // the thread_id from the URL after clicking into a conversation.
        const participants = [...t.querySelectorAll(S.MSG_PARTICIPANTS)]
          .map((p) => p.textContent.trim())
          .filter(Boolean);
        const thread_id =
          t.getAttribute("data-control-name") ||
          (participants[0] ? participants[0].toLowerCase().replace(/\s+/g, "-") : "") ||
          t.id ||
          "";
        return {
          thread_id,
          participants,
          last_message_preview: text(t, S.MSG_SNIPPET),
          last_message_time: text(t, S.MSG_TIME),
          unread: t.className.includes(S.MSG_UNREAD_CLASS),
        };
      });
      return { threads };
    },

    async getThreadMessages({ thread_id, limit = 50 } = {}) {
      const target = `${S.MESSAGING}thread/${thread_id}/`;
      if (!location.href.startsWith(target)) return { _navigate: target };
      await waitFor(S.MSG_BUBBLE, 10000);
      const bubbles = [...document.querySelectorAll(S.MSG_BUBBLE)].slice(-limit);
      const messages = bubbles.map((b) => ({
        sender: text(b, S.MSG_BUBBLE_SENDER),
        body: [...b.querySelectorAll(S.MSG_BUBBLE_BODY)]
          .map((p) => p.textContent.trim())
          .join(" ")
          .trim(),
        timestamp: text(b, S.MSG_BUBBLE_TIME),
      }));
      return { messages, thread_id };
    },

    async sendMessage({ profile_url, message, attachment_path = "" } = {}) {
      const clean = stripQuery(profile_url);
      if (!location.href.startsWith(clean)) return { _navigate: clean };

      // Message button is text-only ("Message"), no stable class/aria-label.
      const msgBtn =
        btnByText(/^Message$/) || document.querySelector(S.PROFILE_MESSAGE_BTN);
      if (!isVisible(msgBtn)) {
        return {
          success: false,
          error:
            "Message button not found — likely not a 1st-degree connection or Premium-gated.",
        };
      }
      msgBtn.click();
      const box = await waitFor(S.MSG_COMPOSE, 8000);
      if (!box) return { success: false, error: "Compose box did not open." };

      let attachmentWarning = null;
      if (attachment_path) {
        // Programmatic file selection is blocked by Chrome for security.
        attachmentWarning = "attachment_unsupported";
      }

      setContentEditable(box, message);
      await sleep(400);
      const send = document.querySelector(S.MSG_SEND_BTN);
      if (!send || send.disabled) {
        return { success: false, error: "Send button disabled after fill." };
      }
      send.click();
      await sleep(800);
      return { success: true, error: attachmentWarning };
    },

    async connect({ profile_url, note = "" } = {}) {
      const clean = stripQuery(profile_url);
      if (!location.href.startsWith(clean)) return { _navigate: clean };

      // Already pending? (text-based — "Pending" appears on the button/label)
      if (btnByText(/^Pending$/)) {
        return { success: false, status: "pending", error: "Invite already pending." };
      }

      // Connect is usually a top-card button by text, else inside the More dropdown.
      let connectBtn = btnByText(/^Connect$/);
      if (!connectBtn) {
        const more = btnByLabel("More") || btnByLabel("More actions") ||
          btnByText(/^More$/);
        if (more) {
          more.click();
          await sleep(700);
          // Dropdown items: role=menuitem or buttons/divs whose text starts "Connect".
          const items = [
            ...document.querySelectorAll(
              "[role='menuitem'], .artdeco-dropdown__content button, " +
              ".artdeco-dropdown__content [role='button'], div[role='button']"
            ),
          ];
          connectBtn = items.find(
            (el) => isVisible(el) && /^Connect\b/.test(el.textContent.trim())
          );
        }
      }
      if (!connectBtn) {
        return {
          success: false,
          error:
            "Connect not found (already connected, Follow-only profile, blocked, or DOM changed).",
        };
      }
      connectBtn.click();
      await sleep(1100);

      // The "Send without a note?" / invite modal. Scope all lookups to the dialog
      // when present. LinkedIn now defaults to note-free invites; the primary CTA is
      // usually labelled "Send" (sometimes "Send without a note" / "Send now").
      const dialog =
        [...document.querySelectorAll("div[role='dialog'], [class*='artdeco-modal']")]
          .find(isVisible) || document;

      if (note) {
        const addNote =
          btnByLabel("Add a note", dialog) || btnByText(/^Add a note$/, dialog);
        if (addNote) {
          addNote.click();
          const ta = await waitFor(S.NOTE_TEXTAREA, 5000);
          if (ta) {
            ta.focus();
            ta.value = note.slice(0, 300);
            ta.dispatchEvent(new InputEvent("input", { bubbles: true }));
            await sleep(300);
          }
        }
      }

      // Find the Send button: aria-label variants first, then any visible button in
      // the dialog whose text is a Send variant ("Send", "Send without a note", etc.).
      const sendByLabel =
        btnByLabel("Send invitation", dialog) ||
        btnByLabel("Send without a note", dialog) ||
        btnByLabel("Send now", dialog) ||
        btnByLabel("Send", dialog);
      const sendByText = [...dialog.querySelectorAll("button")]
        .filter(isVisible)
        .find((b) => /^send( without a note| now| invitation)?$/i.test(b.textContent.trim()));
      const send = sendByLabel || sendByText;

      if (send && isVisible(send)) {
        send.click();
        await sleep(700);
        return { success: true, status: "invite_sent", error: null };
      }

      // No Send button and no modal — LinkedIn sometimes fires the invite immediately
      // on the Connect click (note-free quick-invite). Treat a now-Pending state as sent.
      if (btnByText(/^Pending$/)) {
        return { success: true, status: "invite_sent", error: null };
      }
      return { success: false, error: "Send invitation button not found." };
    },

    async getSentInvites() {
      if (!location.href.startsWith(S.SENT_INVITES)) return { _navigate: S.SENT_INVITES };
      await waitFor(S.SENT_INVITE_ITEM, 10000);
      const items = [...document.querySelectorAll(S.SENT_INVITE_ITEM)];
      const pending = items
        .map((it) => {
          const name = text(it, S.SENT_INVITE_NAME);
          const profile_url = stripQuery(attr(it, "a[href*='/in/']", "href"));
          return name ? { name, profile_url } : null;
        })
        .filter(Boolean);
      return { pending, total: pending.length };
    },

    async searchPosts({ keywords, date_filter = "past-week", limit = 15 } = {}) {
      const code = S.DATE_CODES[date_filter] || S.DATE_CODES["past-week"];
      const target = `${S.SEARCH_CONTENT}?keywords=${encodeURIComponent(
        keywords
      )}&sortBy=%22date_posted%22&datePosted=%22${code}%22`;
      if (!location.href.startsWith(S.SEARCH_CONTENT)) return { _navigate: target };

      if (checkRateLimit()) {
        return { success: false, error: "Rate limit detected on search page." };
      }
      // New structure: lazy-column direct children with data-display-contents.
      const cards = await scrollCollect(S.POST_CARD, limit);
      const posts = cards
        .slice(0, limit)
        .map((c) => {
          // Name link has visible text; photo link has img child.
          const authorLink = [...c.querySelectorAll('a[href*="/in/"]')]
            .find((a) => a.textContent.trim().length > 0 && !a.querySelector("img"));
          if (!authorLink) return null;
          const rawName = authorLink.textContent.trim();
          const author_name = rawName.split(/\s*[•·]\s*/)[0].trim();
          if (!author_name) return null;
          const author_url = stripQuery(authorLink.href);
          const degreeMatch = rawName.match(/[•·]\s*([\w+]+)\s*$/);
          const author_degree = degreeMatch ? degreeMatch[1] : "";
          // Body: prefer expandable-text-box, fall back to POST_BODY selector.
          const bodyEl = c.querySelector(S.POST_BODY);
          const body = bodyEl ? bodyEl.textContent.trim() : "";
          // Time: first span/p matching "1m •", "2h •", "3d •" pattern.
          const timeEl = [...c.querySelectorAll("span, p")]
            .find((el) => /^\d+[mhd]\s*[•·]/.test(el.textContent.trim()));
          const posted_at = timeEl ? timeEl.textContent.trim() : "";
          return {
            author_name,
            author_url,
            author_degree,
            author_title: "",
            body,
            post_url: stripQuery(attr(c, "a[href*='/feed/update/']", "href") || ""),
            posted_at,
          };
        })
        .filter(Boolean);
      return { posts, query: keywords };
    },

    async openJobs({
      keywords,
      location: loc = "",
      easy_apply_only = true,
      date_posted = "",
    } = {}) {
      const p = new URLSearchParams();
      p.set("keywords", keywords);
      if (loc) p.set("location", loc);
      if (easy_apply_only) p.set("f_AL", "true");
      if (date_posted && S.DATE_CODES[date_posted])
        p.set("f_TPR", S.DATE_CODES[date_posted]);
      const target = `${S.JOBS_SEARCH}?${p.toString()}`;
      return { _navigate: target, url: target, opened: true };
    },

    async readJobs({ limit = 25 } = {}) {
      await waitFor(S.JOB_CARD, 10000);
      // Job list scrolls its own container.
      const listCol =
        document.querySelector(".jobs-search-results-list") ||
        document.querySelector(".scaffold-layout__list");
      const cards = await scrollCollect(S.JOB_CARD, limit, listCol);
      // JOB_CARD is now li[data-occludable-job-id] only — no div.job-card-container
      // duplicate. Deduplicate by job_id as a safety net.
      // LinkedIn renamed "Easy Apply" to "LinkedIn Apply" and removed the badge text
      // from card footers. Infer easy_apply from f_AL=true in the page URL instead.
      const pageEasyApply = /[?&]f_AL=true/.test(location.href);
      const seen = new Set();
      const jobs = cards
        .map((c) => {
          const job_id =
            c.getAttribute("data-occludable-job-id") ||
            c.getAttribute("data-job-id") ||
            (attr(c, "a", "href").match(/\/jobs\/view\/(\d+)/) || [])[1] ||
            "";
          if (!job_id || seen.has(job_id)) return null;
          seen.add(job_id);
          const footer = text(c, S.JOB_FOOTER);
          return {
            job_id,
            title: text(c, S.JOB_TITLE),
            company: text(c, S.JOB_COMPANY),
            location: text(c, S.JOB_LOCATION),
            easy_apply: pageEasyApply || /LinkedIn Apply|Easy Apply/i.test(footer) || /LinkedIn Apply|Easy Apply/i.test(c.innerText),
            promoted: /Promoted/i.test(footer),
            url: job_id ? `${S.BASE}/jobs/view/${job_id}/` : "",
          };
        })
        .filter((j) => j && j.title)
        .slice(0, limit);
      return { jobs };
    },

    async openJob({ job_id } = {}) {
      const target = `${S.BASE}/jobs/view/${job_id}/`;
      if (!location.href.startsWith(target)) return { _navigate: target };
      // The JD page migrated to hashed CSS modules — no stable #job-details / h1.
      // Wait for <main> to hold the rendered JD, then pull text + title/company from
      // document.title ("Title | Company | LinkedIn") and the company link.
      let main = null;
      for (let i = 0; i < 40; i++) {
        main = document.querySelector("main");
        if (main && main.innerText && main.innerText.length > 400) break;
        await sleep(300);
      }
      const parts = (document.title || "")
        .replace(/^\(\d+\)\s*/, "") // strip "(3) " notification prefix
        .split(" | ")
        .map((s) => s.trim());
      const docTitle = parts[0] || "";
      const docCompany = parts.length >= 3 ? parts[1] : "";
      const companyEl = document.querySelector("a[href*='/company/']");
      const company = (companyEl ? companyEl.textContent.trim() : "") || docCompany;
      const description = main
        ? main.innerText.trim().replace(/\n{3,}/g, "\n\n")
        : "";
      return {
        job_id,
        title: docTitle,
        company,
        location: "",
        description,
        // SDUI flow: Easy Apply is an <a href=".../apply/?openSDUIApplyFlow=true">
        // labelled "LinkedIn Apply to this job"; external apply opens a new tab / offsite.
        easy_apply: !!(
          [...document.querySelectorAll(
            "a[href*='openSDUIApplyFlow'], a[href*='/jobs/view/'][href*='/apply/'], " +
            "[aria-label*='LinkedIn Apply'], [aria-label*='Easy Apply']"
          )].find(isVisible) || btnByText(/Easy Apply/)
        ),
        apply_url: target,
      };
    },

    // --------------------------------------------------------------- //
    // Easy Apply — hybrid approach (extension handles all except file input)
    // --------------------------------------------------------------- //

    // Phase 1 of Easy Apply: click button, dismiss interstitial, fill contact step,
    // advance to resume step. Returns state so the caller can use file_upload for the
    // resume input (Chrome MV3 blocks programmatic file selection from extensions).
    async startEasyApply({ job_id } = {}) {
      // LinkedIn migrated to the SDUI apply flow (2026-06). The Easy Apply control is an
      // <a href=".../jobs/view/<id>/apply/?openSDUIApplyFlow=true">. Verified 2026-06-03
      // that this flow CANNOT be opened programmatically: synthetic .click() and real CDP
      // clicks are no-ops, and navigating directly to the apply URL redirects back to
      // /jobs/view/<id>/. The overlay only opens from a genuine, trusted user gesture the
      // SPA router intercepts. We still detect the button (so callers can score/route),
      // attempt a best-effort click, and report honestly if the surface never opens.
      const target = `${S.BASE}/jobs/view/${job_id}/`;
      if (!location.href.startsWith(target)) return { _navigate: target };

      const eaBtn =
        [...document.querySelectorAll(
          "a[href*='openSDUIApplyFlow'], a[href*='/apply/'], " +
          "[aria-label*='LinkedIn Apply'], [aria-label*='Easy Apply']"
        )].find(isVisible) ||
        btnByText(/Easy Apply|LinkedIn Apply/i);
      if (!eaBtn || !isVisible(eaBtn)) {
        return { success: false, error: "Easy Apply button not found on this job page." };
      }
      eaBtn.click();
      await sleep(1600);

      // Dismiss "Save this application?" interstitial if it appeared.
      // The × close icon keeps the underlying form open; Discard closes both.
      const dismissBtn =
        btnByLabel("Dismiss") ||
        [...document.querySelectorAll("button")].find(
          (b) => isVisible(b) && /^[×x✕]$/.test(b.textContent.trim())
        );
      if (dismissBtn && isVisible(dismissBtn)) {
        dismissBtn.click();
        await sleep(900);
      }

      // Locate the genuine apply surface — a dialog/modal or an explicit easy-apply
      // form. Do NOT fall back to <main> or generic <form>: those always exist on the
      // job page and would produce a FALSE success when the apply overlay never opened
      // (SDUI gate). The surface must be a real apply container with apply-specific
      // signals (a Submit/Review/Next control or a resume file input inside it).
      const candidates = [...document.querySelectorAll(
        "div[role='dialog'], [class*='artdeco-modal'], [class*='jobs-easy-apply'], " +
        "form[class*='apply'], form[id*='apply'], div[data-test*='apply']"
      )].filter(isVisible);
      const modal = candidates.find((c) =>
        c.querySelector("input[type='file']") ||
        [...c.querySelectorAll("button")].some((b) =>
          isVisible(b) && /^(submit application|review|next|continue)\b/i.test(b.textContent.trim())
        )
      ) || candidates.find(isVisible);
      if (!modal || !isVisible(modal)) {
        // Return diagnostics so the apply surface can be characterised on a live run.
        return {
          success: false,
          sdui_gated: true,
          error:
            "SDUI apply overlay did not open. LinkedIn's new apply flow only opens from a " +
            "genuine user click; programmatic clicks and direct apply-URL navigation are " +
            "blocked (verified 2026-06-03). Apply to this job manually.",
          url: location.href,
          visible_buttons: [...document.querySelectorAll("button")]
            .filter(isVisible).map((b) => b.textContent.trim()).filter(Boolean).slice(0, 25),
        };
      }

      // Advance through Contact step (pre-filled) by clicking Next.
      const nextBtn =
        btnByText(/^Next$/i, modal) ||
        btnByLabel("Continue to next step", modal);
      if (nextBtn && isVisible(nextBtn)) {
        nextBtn.click();
        await sleep(1200);
      }

      // Detect resume step: look for a visible file input or "Upload resume" button.
      const fileInput = document.querySelector("input[type='file']");
      const fileInputVisible = !!(fileInput && isVisible(fileInput));
      const hasExistingResume = !!(
        btnByText(/Change resume|Select a resume/i, modal) ||
        document.querySelector("[class*='resume-picker']")
      );

      return {
        success: true,
        modal_open: true,
        step: fileInputVisible ? "resume_upload" : (hasExistingResume ? "resume_select" : "questions"),
        file_input_visible: fileInputVisible,
        file_input_selector: fileInputVisible ? "input[type='file']" : null,
        has_existing_resume: hasExistingResume,
      };
    },

    // Phase 2 of Easy Apply: call AFTER the caller has handled file upload via
    // claude-in-chrome file_upload. Fills additional question fields, clicks Next
    // through remaining steps, and submits. answers = {labelSubstring: value}.
    async continueEasyApply({ answers = {}, submit = true } = {}) {
      const modal =
        document.querySelector("div[role='dialog']") ||
        document.querySelector("[class*='artdeco-modal']");
      if (!modal || !isVisible(modal)) {
        return { success: false, error: "Easy Apply modal not found." };
      }

      // If we're still on the resume step, click Next first.
      const resumeNext =
        btnByText(/^Next$/i, modal) ||
        btnByLabel("Continue to next step", modal);
      if (resumeNext && isVisible(resumeNext)) {
        resumeNext.click();
        await sleep(1000);
      }

      // Fill any visible answer fields.
      for (const [labelFragment, value] of Object.entries(answers)) {
        const inputs = [...modal.querySelectorAll("input, select, textarea")].filter(isVisible);
        for (const inp of inputs) {
          const id = inp.id;
          const labelEl = id ? modal.querySelector(`label[for='${CSS.escape(id)}']`) : null;
          const parentText = inp.closest("[class]")?.textContent || "";
          const matches =
            (labelEl && labelEl.textContent.toLowerCase().includes(labelFragment.toLowerCase())) ||
            parentText.toLowerCase().includes(labelFragment.toLowerCase());
          if (!matches) continue;
          if (inp.tagName === "SELECT") {
            inp.value = value;
            inp.dispatchEvent(new Event("change", { bubbles: true }));
          } else {
            inp.focus();
            inp.value = "";
            document.execCommand && document.execCommand("insertText", false, String(value));
            if (!inp.value) inp.value = String(value);
            inp.dispatchEvent(new InputEvent("input", { bubbles: true }));
          }
          await sleep(200);
          break;
        }
      }

      // Navigate through remaining steps and submit.
      let steps = 0;
      while (steps < 10) {
        const submitBtn = btnByText(/^Submit application$/i, modal);
        const reviewBtn = btnByText(/^Review$/i, modal);
        const nextBtn =
          btnByText(/^Next$/i, modal) || btnByLabel("Continue to next step", modal);

        if (submit && submitBtn && isVisible(submitBtn)) {
          submitBtn.click();
          await sleep(1500);
          // Dismiss post-submit confirmation dialog if it appears.
          const doneBtn = btnByText(/^Done$/i) || btnByLabel("Dismiss", document);
          if (doneBtn && isVisible(doneBtn)) doneBtn.click();
          return { success: true, submitted: true, steps_traversed: steps };
        } else if (reviewBtn && isVisible(reviewBtn)) {
          reviewBtn.click();
          await sleep(1000);
        } else if (nextBtn && isVisible(nextBtn)) {
          nextBtn.click();
          await sleep(1000);
        } else {
          break;
        }
        steps++;
      }

      return { success: true, submitted: false, steps_traversed: steps };
    },

    // --------------------------------------------------------------- //
    // Debug / selector-repair tooling
    // --------------------------------------------------------------- //

    // Navigate the active LinkedIn tab to an arbitrary URL (then audit/probe it).
    async goto({ url } = {}) {
      if (!url) return { success: false, error: "url required" };
      if (!location.href.startsWith(stripQuery(url))) return { _navigate: url };
      return { success: true, url: location.href };
    },

    // Audit every selector in window.LI_SEL against the current page: report match
    // count + a sample for each, so we can see which selectors are stale (count 0).
    async auditSelectors() {
      const results = {};
      for (const [key, val] of Object.entries(S)) {
        if (typeof val !== "string") continue; // skip arrays/objects/version
        if (val.startsWith("http")) continue; // skip URL constants
        let count = -1;
        let sample = "";
        let valid = true;
        try {
          const els = document.querySelectorAll(val);
          count = els.length;
          if (els[0]) {
            sample = (els[0].textContent || "").trim().replace(/\s+/g, " ").slice(0, 80);
          }
        } catch {
          valid = false; // not a valid CSS selector (e.g. a class-name string)
        }
        results[key] = { selector: val, count, sample, valid };
      }
      return { url: location.href, title: document.title, results };
    },

    // Test one or more candidate selectors and return match counts + samples,
    // for iterating toward a working replacement.
    async probe({ selectors = [], limit = 3, attr: attrName = null } = {}) {
      const list = Array.isArray(selectors) ? selectors : [selectors];
      const out = {};
      for (const sel of list) {
        try {
          const els = [...document.querySelectorAll(sel)].slice(0, limit);
          out[sel] = {
            count: document.querySelectorAll(sel).length,
            samples: els.map((el) => ({
              tag: el.tagName.toLowerCase(),
              text: (el.textContent || "").trim().replace(/\s+/g, " ").slice(0, 120),
              attr: attrName ? el.getAttribute(attrName) : undefined,
              html: el.outerHTML.slice(0, 200),
            })),
          };
        } catch (e) {
          out[sel] = { error: String((e && e.message) || e) };
        }
      }
      return { url: location.href, results: out };
    },

  };

  // ----------------------------------------------------------------- //
  // Dispatcher
  // ----------------------------------------------------------------- //
  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    const fn = actions[msg.action];
    if (!fn) {
      sendResponse({ ok: false, error: `Unknown action: ${msg.action}` });
      return false;
    }
    Promise.resolve(fn(msg.params || {}))
      .then((data) => sendResponse({ ok: true, data }))
      .catch((e) => sendResponse({ ok: false, error: String(e && e.message || e) }));
    return true; // async response
  });
})();
