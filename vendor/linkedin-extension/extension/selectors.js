// LinkedIn DOM selectors — single source of truth.
// Ported verbatim from vendor/linkedin-selenium/src/config/constants.py (2026-06)
// plus new job-search selectors. Update SELECTOR_VERSION when LinkedIn changes DOM.
//
// Loaded as a plain content script (not a module) so it attaches to window.LI_SEL.

window.LI_SEL = {
  SELECTOR_VERSION: "2026-06-v3",

  // --- URLs ---
  BASE: "https://www.linkedin.com",
  FEED: "https://www.linkedin.com/feed",
  CONNECTIONS: "https://www.linkedin.com/mynetwork/invite-connect/connections/",
  MESSAGING: "https://www.linkedin.com/messaging/",
  SENT_INVITES: "https://www.linkedin.com/mynetwork/invitation-manager/sent/",
  SEARCH_CONTENT: "https://www.linkedin.com/search/results/content/",
  JOBS_SEARCH: "https://www.linkedin.com/jobs/search/",

  // datePosted codes for post/job search
  DATE_CODES: {
    "past-24h": "r86400",
    "past-week": "r604800",
    "past-month": "r2592000",
  },

  // --- Login / nav ---
  // LinkedIn migrated to CSS modules — class names are hashed and unstable.
  // Use data-testid="primary-nav" (stable) as primary signal; fall back to nav element.
  NAV_ME: '[data-testid="primary-nav"], nav',

  // --- Connections ---
  // New structure: lazy-column direct children with data-display-contents.
  // Extraction logic is inline in getConnections(); these selectors just drive scrollCollect.
  CONNECTION_CARD: '[data-testid="lazy-column"] > [data-display-contents="true"]',

  // --- Messaging ---
  // li.msg-conversation-listitem is stable; the old __link variant is now a div child.
  MSG_THREAD: "li.msg-conversation-listitem",
  MSG_PARTICIPANTS: ".msg-conversation-listitem__participant-names, .msg-conversation-card__participant-names",
  MSG_SNIPPET: ".msg-conversation-card__message-snippet, .msg-conversation-listitem__message-snippet",
  MSG_TIME: ".msg-conversation-listitem__time-stamp, .msg-conversation-card__time-stamp",
  MSG_UNREAD_CLASS: "msg-conversation-listitem--unread",
  MSG_COMPOSE: ".msg-form__contenteditable",
  MSG_SEND_BTN: "button.msg-form__send-button",
  MSG_FILE_INPUT: "input[type='file'].msg-form__file-attachment-btn--hidden, input[type='file']",
  MSG_BUBBLE: ".msg-s-message-list__event",
  MSG_BUBBLE_SENDER: ".msg-s-message-group__name, .msg-s-event-listitem__link",
  MSG_BUBBLE_BODY: ".msg-s-event-listitem__body, p",
  MSG_BUBBLE_TIME: ".msg-s-message-group__timestamp, time",

  // --- Profile (verified 2026-06-v3) ---
  // Profile action buttons use hashed classes + text labels, mostly no aria-label.
  // sendMessage/connect now match by visible TEXT in content.js (btnByText). These
  // CSS selectors remain only as legacy fallbacks.
  PROFILE_MESSAGE_BTN:
    "button.pvs-profile-actions__action[aria-label*='Message'], .pv-s-profile-actions__message",

  // --- Connect / invitations ---
  // Connect is reached via the "More" dropdown (button[aria-label='More']) → a
  // menuitem whose text is "Connect"; logic lives in content.js connect(). Modal
  // sub-buttons (Add a note / Send) still expose aria-labels.
  MORE_ACTIONS_BTN: "button[aria-label='More'], button[aria-label='More actions']",
  NOTE_TEXTAREA: "textarea#custom-message, textarea[name='message'], textarea[id*='custom-message']",
  // Sent-invitations page rows (verified 2026-06-v3): CSS-module markup, no stable
  // classes. Each invite is a componentkey listitem wrapping a /in/ link; the name
  // is the FIRST <p> in the card, the title is the second.
  SENT_INVITE_ITEM: "[componentkey]:has(a[href*='/in/'])",
  SENT_INVITE_NAME: "p",

  // --- Posts (content search) ---
  // New structure: lazy-column direct children with data-display-contents.
  // Extraction logic is inline in searchPosts().
  POST_CARD: '[data-testid="lazy-column"] > [data-display-contents="true"]',
  POST_BODY: '[data-testid="expandable-text-box"]',

  // --- Jobs ---
  // Use only li[data-occludable-job-id] to avoid duplicates from div.job-card-container.
  JOB_CARD: "li[data-occludable-job-id]",
  JOB_TITLE: ".job-card-list__title, .job-card-container__link, a.job-card-list__title--link",
  JOB_COMPANY: ".job-card-container__primary-description, .artdeco-entity-lockup__subtitle",
  JOB_LOCATION: ".job-card-container__metadata-item, .artdeco-entity-lockup__caption",
  JOB_FOOTER: ".job-card-container__footer-wrapper, .job-card-list__footer-wrapper",
  // Job DETAIL page (verified 2026-06-v3): migrated to hashed CSS modules — the old
  // .job-details-* / #job-details / h1 selectors are ALL dead. openJob() now reads
  // the JD from <main> innerText and title/company from document.title + the company
  // link. Easy-Apply is detected by button text ("Easy Apply"), not class.
  JOB_DETAIL_MAIN: "main",
  JOB_DETAIL_COMPANY_LINK: "a[href*='/company/']",

  // --- Rate limit ---
  RATE_LIMIT_EMPTY: ".artdeco-empty-state",
  RATE_LIMIT_STRINGS: [
    "You've reached the weekly invitation limit",
    "weekly limit",
    "try again next week",
  ],
};
