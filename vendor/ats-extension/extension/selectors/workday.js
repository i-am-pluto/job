// Workday DOM selectors — single source of truth for all ATS platforms.
// Each ATS gets its own key under window.ATS_SEL.
// Update SELECTOR_VERSION when Workday/Greenhouse changes DOM.

window.ATS_SEL = {
  SELECTOR_VERSION: "2026-06-v2",

  workday: {
    // --- URLs ---
    HOST_PATTERN: "myworkdayjobs.com",

    // --- Step / form identification ---
    // Workday panels use [data-automation-id] as stable hooks.
    FORM_CONTAINER: "[data-automation-id='applicationForm']",
    STEP_HEADER: "[data-automation-id='stepHeader']",
    STEP_INDICATOR: "[data-automation-id='stepIndicator']",
    CURRENT_STEP: "[data-automation-id='stepIndicator'] [class*='current']",
    ERROR_SUMMARY: "[data-automation-id='errorSummary']",

    // --- Fields ---
    // Individual form fields
    TEXT_INPUT: "input[data-automation-id='textInput'], input[type='text']",
    TEXTAREA: "textarea[data-automation-id='textarea']",
    SELECT: "select[data-automation-id='select'], div[data-automation-id='select']",
    CHECKBOX: "input[type='checkbox']",
    RADIO_GROUP: "[data-automation-id='radioGroup']",
    RADIO_LABEL: "[data-automation-id='radioLabel']",
    FILE_UPLOAD: "input[type='file']",

    // Label detection: Workday wraps fields in divs with aria-labelledby or
    // preceding label elements. Use data-automation-id on the label wrapper.
    FIELD_LABEL: "[data-automation-id='label']",
    FIELD_WRAPPER: "[data-automation-id*='FormField'], [class*='formField']",

    // --- Question types ---
    // Multi-choice checkbox lists
    CHECKBOX_GROUP: "[data-automation-id='checkboxGroup']",
    CHECKBOX_OPTION: "[data-automation-id='checkbox']",

    // --- Navigation ---
    // NOTE: valid CSS only — no Playwright :has-text(). content.js matches button
    // TEXT via btnByText(); these attribute selectors are the structural fallback.
    // data-automation-id guesses must be confirmed/repaired with ats_audit_selectors.
    NEXT_BTN: "button[data-automation-id='pageFooterNextButton'], button[data-automation-id='nextButton'], button[data-automation-id='bottom-navigation-next-button']",
    SAVE_NEXT_BTN: "button[data-automation-id='pageFooterNextButton']",
    SUBMIT_BTN: "button[data-automation-id='pageFooterSubmitButton'], button[data-automation-id='submitButton']",
    BACK_BTN: "button[data-automation-id='backButton']",

    // --- Login / SSO walls ---
    LOGIN_FORM: "[data-automation-id='loginForm'], form[action*='login']",
    SSO_BTN: "[data-automation-id='ssoButton'], a[data-automation-id='companyLogin']",
    EMAIL_INPUT: "input[type='email'], input[name='email'], input[name*='username']",
    PASSWORD_INPUT: "input[type='password']",
    LOGIN_SUBMIT: "button[type='submit']",

    // --- Confirmation ---
    SUCCESS_MESSAGE: "[data-automation-id='successMessage'], [class*='confirmation']",
  },

  // Placeholder for future Greenhouse selectors
  greenhouse: {},

  // Placeholder for future Lever selectors
  lever: {},
};
