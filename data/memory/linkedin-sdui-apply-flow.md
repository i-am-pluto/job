---
name: linkedin-sdui-apply-flow
description: LinkedIn rolled out SDUI apply flow — Easy Apply is now an <a> link, not a button; broke extension detection
metadata:
  type: project
---

As of 2026-06-03, LinkedIn migrated job pages to a Server-Driven UI (SDUI) apply flow. The Easy Apply control is now an anchor, not a button:

- Tag: `<a>` (role=link), visible text just **"Apply"** + the LinkedIn logo (no "Easy Apply" text).
- `aria-label="LinkedIn Apply to this job"`.
- `href` contains `/jobs/view/<id>/apply/?openSDUIApplyFlow=true`.

This broke `vendor/linkedin-extension/extension/content.js` detection, which scanned only `<button>` elements for the literal text "Easy Apply". Symptom: every job returned `easy_apply:false` (openJob) and `"Easy Apply button not found"` (startEasyApply), even for genuine Easy Apply jobs (e.g. Atomicwork 4419856434). Also `read_jobs` `easy_apply` flag is unreliable — it returns true for everything, including external-apply promoted jobs; only `openJob`/`startEasyApply` give truth.

**Fix applied (2026-06-03):** updated `startEasyApply` and `openJob` to match anchors via `a[href*='openSDUIApplyFlow']`, `a[href*='/apply/']`, `[aria-label*='LinkedIn Apply']`, `[aria-label*='Easy Apply']`, then fall back to legacy button text. **Requires extension reload to take effect.**

**Detection fix VERIFIED 2026-06-03** (after extension reload): `startEasyApply`/`openJob` now correctly find the SDUI anchor button.

**TRIGGER IS BLOCKED — autonomous LinkedIn Easy Apply is NOT feasible (verified 2026-06-03, three methods):**
1. Synthetic `eaBtn.click()` in content script → no-op; URL stays on `/jobs/view/<id>/`.
2. Real CDP `computer.left_click` on the anchor (claude-in-chrome) → no-op; no overlay/form appears.
3. Direct navigation to `/jobs/view/<id>/apply/?openSDUIApplyFlow=true` (the anchor's real href, with trackingId) → LinkedIn **redirects back** to `/jobs/view/<id>/`.

The SDUI apply overlay only opens from a genuine, trusted user gesture the SPA router intercepts; automated clicks don't fire LinkedIn's handler. This is effectively a trusted-gesture / anti-automation gate on the new apply rollout. There is no `continueEasyApply` traversal to fix because the form never opens.

**Re-confirmed 2026-06-03 (second job, JioHotstar 4418746428):** real CDP click → no overlay, page just reloads skeletons, identical to Atomicwork. Gate is NOT lifted on any job tested.

**BEWARE FALSE POSITIVES:** an interim `startEasyApply` had `... || document.querySelector("main")` as the surface fallback. `main` always exists on the job page, so it returned `{success:true, step:"questions"}` even though no overlay opened — a haiku apply agent then reported "gate LIFTED, modal opens." It was a lie; `continueEasyApply` failed ("modal not found") because there was no real surface. FIXED: `startEasyApply` now only accepts a real apply container (`div[role='dialog']`, `[class*='artdeco-modal']`, `[class*='jobs-easy-apply']`, `form[class*='apply']`, `div[data-test*='apply']`) that also contains a Submit/Review/Next control or a resume file input; otherwise returns `sdui_gated`. Never reintroduce a `main`/generic-`form` fallback.

**Current state of code:** detection works; trigger is a confirmed dead end. `startEasyApply` returns `{success:false, sdui_gated:true, error:"...apply manually"}` honestly. Do NOT keep dispatching apply agents to retry — programmatic triggers are dead. LinkedIn Easy Apply candidates stay in `data/pipeline.md` for manual application until LinkedIn changes the flow or a trusted-gesture workaround is found. Re-test only if LinkedIn's apply DOM changes. See [[linkedin-extension-mcp]].
