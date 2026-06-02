// content.js — injected on myworkdayjobs.com (and future ATS domains).
// Implements every ATS action against the live DOM and returns plain JSON.
// Dispatched by the service worker via chrome.tabs.sendMessage({action, params}).
//
// Relies on window.ATS_SEL (selectors/workday.js, loaded first).

(() => {
  const S = window.ATS_SEL;

  // ----------------------------------------------------------------- //
  // DOM helpers
  // ----------------------------------------------------------------- //
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  const isVisible = (el) => !!el && el.offsetParent !== null;

  const text = (root, sel, def = "") => {
    const el = root.querySelector(sel);
    return el ? el.textContent.trim().replace(/\s+/g, " ") : def;
  };

  const attr = (root, sel, name, def = "") => {
    const el = root.querySelector(sel);
    return el ? el.getAttribute(name) || def : def;
  };

  async function waitFor(sel, timeout = 12000) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      const el = document.querySelector(sel);
      if (el) return el;
      await sleep(250);
    }
    return null;
  }

  const visibleButtons = (root = document) =>
    [...root.querySelectorAll("button")].filter(isVisible);

  const btnByText = (re, root = document) =>
    visibleButtons(root).find((b) => re.test(b.textContent.trim()));

  async function waitForStepChange(currentStep, timeout = 15000) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      await sleep(500);
      const newStep = detectStep();
      if (newStep && newStep !== currentStep) return newStep;
    }
    return null;
  }

  // ----------------------------------------------------------------- //
  // ATS detection
  // ----------------------------------------------------------------- //
  function detectATS() {
    const url = location.href.toLowerCase();
    if (url.includes("myworkdayjobs") || url.includes("wd1.") || url.includes("wd5."))
      return "workday";
    if (url.includes("greenhouse.io")) return "greenhouse";
    return "unknown";
  }

  function detectStep() {
    const ats = detectATS();
    if (ats === "workday") {
      const stepEl =
        document.querySelector(S.workday.STEP_HEADER) ||
        document.querySelector(S.workday.CURRENT_STEP) ||
        document.querySelector("[data-automation-id*='step']");
      if (stepEl) return stepEl.textContent.trim().replace(/\s+/g, " ");
      // Fallback: detect by visible field presence
      if (document.querySelector(S.workday.FILE_UPLOAD)) return "resume_upload";
      if (btnByText(/Submit Application/i)) return "review_submit";
      if (btnByText(/Next|Save and Continue/i)) return "form_filling";
      if (document.querySelector(S.workday.SUCCESS_MESSAGE)) return "submitted";
      return "unknown";
    }
    return "unknown";
  }

  // ----------------------------------------------------------------- //
  // Field extraction
  // ----------------------------------------------------------------- //
  function getFieldInfo(el) {
    const tag = el.tagName.toLowerCase();
    const type = el.getAttribute("type") || tag;
    // Find label: look for aria-labelledby, preceding label, or wrapper
    let labelText = "";
    const labelledBy = el.getAttribute("aria-labelledby");
    if (labelledBy) {
      const labelEl = document.getElementById(labelledBy);
      if (labelEl) labelText = labelEl.textContent.trim();
    }
    if (!labelText) {
      const labelFor = document.querySelector(`label[for='${CSS.escape(el.id)}']`);
      if (labelFor) labelText = labelFor.textContent.trim();
    }
    if (!labelText) {
      const wrapper = el.closest(S.workday.FIELD_WRAPPER);
      if (wrapper) {
        const label = wrapper.querySelector(S.workday.FIELD_LABEL);
        if (label) labelText = label.textContent.trim();
      }
    }
    const required = el.hasAttribute("required") || el.getAttribute("aria-required") === "true";
    const value = tag === "select" ? el.value : el.value || "";
    const placeholder = el.getAttribute("placeholder") || "";

    let options = [];
    if (tag === "select") {
      options = [...el.options].map((o) => ({ value: o.value, text: o.textContent.trim() }));
    }
    if (type === "radio") {
      const name = el.getAttribute("name");
      if (name) {
        options = [...document.querySelectorAll(`input[name='${CSS.escape(name)}']`)].map((r) => ({
          value: r.value,
          text: r.closest("label")?.textContent?.trim() || r.value,
          checked: r.checked,
        }));
      }
    }

    return { label: labelText, type, value, required, placeholder, options, id: el.id };
  }

  function readForm() {
    const ats = detectATS();
    const container = document.querySelector(S.workday.FORM_CONTAINER) || document.body;
    const fields = [];

    // Text inputs
    for (const el of container.querySelectorAll(S.workday.TEXT_INPUT)) {
      if (isVisible(el)) fields.push(getFieldInfo(el));
    }
    // Textareas
    for (const el of container.querySelectorAll(S.workday.TEXTAREA)) {
      if (isVisible(el)) fields.push(getFieldInfo(el));
    }
    // Selects
    for (const el of container.querySelectorAll(S.workday.SELECT)) {
      if (isVisible(el)) fields.push(getFieldInfo(el));
    }
    // Checkboxes
    for (const el of container.querySelectorAll(S.workday.CHECKBOX)) {
      if (isVisible(el)) fields.push(getFieldInfo(el));
    }
    // Radio groups — sample one per group
    const seenNames = new Set();
    for (const el of container.querySelectorAll("input[type='radio']")) {
      if (isVisible(el) && !seenNames.has(el.name)) {
        seenNames.add(el.name);
        fields.push(getFieldInfo(el));
      }
    }

    return { ats, step: detectStep(), fields };
  }

  // ----------------------------------------------------------------- //
  // Actions
  // ----------------------------------------------------------------- //
  const actions = {
    async status() {
      const ats = detectATS();
      const loggedIn =
        ats === "workday"
          ? !document.querySelector(S.workday.LOGIN_FORM)
          : true;
      return {
        connected: true,
        ats,
        logged_in: loggedIn,
        active_tab_url: location.href,
        selector_version: S.SELECTOR_VERSION,
      };
    },

    async detect() {
      return {
        ats: detectATS(),
        step: detectStep(),
        url: location.href,
      };
    },

    async readForm() {
      return readForm();
    },

    async fillForm({ answers = {} } = {}) {
      const form = readForm();
      let filled = 0;
      let notFound = [];

      for (const [labelFragment, value] of Object.entries(answers)) {
        const match = form.fields.find(
          (f) => f.label.toLowerCase().includes(labelFragment.toLowerCase())
        );
        if (!match) {
          notFound.push(labelFragment);
          continue;
        }
        const el = document.getElementById(match.id);
        if (!el) { notFound.push(labelFragment); continue; }

        el.focus();
        if (el.tagName === "SELECT") {
          const opt = [...el.options].find(
            (o) => o.value === value || o.textContent.trim() === value
          );
          if (opt) {
            el.value = opt.value;
            el.dispatchEvent(new Event("change", { bubbles: true }));
          }
        } else if (el.type === "checkbox") {
          el.checked = value === true || value === "true" || value === "Yes";
          el.dispatchEvent(new Event("change", { bubbles: true }));
        } else if (el.type === "radio") {
          const radio = document.querySelector(
            `input[name='${CSS.escape(el.name)}'][value='${CSS.escape(value)}']`
          );
          if (radio) {
            radio.checked = true;
            radio.dispatchEvent(new Event("change", { bubbles: true }));
          }
        } else {
          el.value = "";
          document.execCommand && document.execCommand("insertText", false, String(value));
          if (!el.value) el.value = String(value);
          el.dispatchEvent(new InputEvent("input", { bubbles: true }));
        }
        await sleep(150);
        filled++;
      }

      return { filled, notFound, step: detectStep() };
    },

    async uploadResume({ filePath } = {}) {
      const fileInput = document.querySelector(S.workday.FILE_UPLOAD);
      if (!fileInput || !isVisible(fileInput)) {
        // Workday sometimes auto-fills the resume from the profile — check
        if (document.querySelector("[data-automation-id*='resume'] [class*='uploaded']")) {
          return { success: true, uploaded: false, reason: "resume_already_present" };
        }
        // Maybe it's in a collapsed section
        const hiddenInput = document.querySelector("input[type='file']");
        if (hiddenInput) {
          return { success: true, native_file_dialog: true, selector: "input[type='file']" };
        }
        return { success: false, error: "No file input found." };
      }
      // Content scripts cannot set file input values programmatically for security.
      // Signal the caller to use claude-in-chrome file_upload tool.
      return { success: true, native_file_dialog: true, selector: "input[type='file']" };
    },

    async nextStep() {
      const stepBefore = detectStep();
      const nextBtn =
        btnByText(/^Next$/i) ||
        btnByText(/Save and Continue/i) ||
        document.querySelector(S.workday.NEXT_BTN) ||
        document.querySelector(S.workday.SAVE_NEXT_BTN);
      if (!nextBtn || !isVisible(nextBtn)) {
        return { success: false, error: "Next/Save and Continue button not visible.", step: stepBefore };
      }
      // Scroll into view before clicking (Workday panels cut off below fold)
      nextBtn.scrollIntoView({ behavior: "instant", block: "center" });
      await sleep(300);
      nextBtn.click();
      await sleep(1000);

      // Wait for the next step to render
      const stepAfter = await waitForStepChange(stepBefore);
      return {
        success: true,
        step_before: stepBefore,
        step_after: stepAfter || detectStep(),
        has_errors: !!document.querySelector(S.workday.ERROR_SUMMARY),
      };
    },

    async submit() {
      const submitBtn =
        btnByText(/Submit Application/i) ||
        document.querySelector(S.workday.SUBMIT_BTN);
      if (!submitBtn || !isVisible(submitBtn)) {
        return { success: false, error: "Submit button not found." };
      }
      submitBtn.scrollIntoView({ behavior: "instant", block: "center" });
      await sleep(300);
      submitBtn.click();
      await sleep(2500);

      const confirmed =
        !!document.querySelector(S.workday.SUCCESS_MESSAGE) ||
        btnByText(/Application Submitted/i) ||
        /application.submitted/i.test(document.body?.innerText || "");
      return { success: true, submitted: confirmed };
    },

    async goto({ url } = {}) {
      if (!url) return { success: false, error: "url required" };
      const cleanUrl = url.split("?")[0];
      if (!location.href.startsWith(cleanUrl)) return { _navigate: url };
      return { success: true, url: location.href };
    },

    async auditSelectors() {
      const ats = detectATS();
      const selSet = S[ats] || {};
      const results = {};
      for (const [key, val] of Object.entries(selSet)) {
        if (typeof val !== "string") continue;
        if (val.startsWith("http")) continue;
        let count = -1;
        let sample = "";
        let valid = true;
        try {
          const els = document.querySelectorAll(val);
          count = els.length;
          if (els[0]) {
            sample = (els[0].textContent || "").trim().replace(/\s+/g, " ").slice(0, 80);
          }
        } catch { valid = false; }
        results[key] = { selector: val, count, sample, valid };
      }
      return { url: location.href, ats, selector_version: S.SELECTOR_VERSION, results };
    },

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
    return true;
  });
})();
