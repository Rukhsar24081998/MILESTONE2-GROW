# Phase 4 — Minimal User Interface: Edge Cases

**Reference:** [Phase 4 in phase-wise-architecture.md](../phase-wise-architecture.md#phase-4--minimal-user-interface-week-23)  
**Exit criteria:** E2E — example questions work; advisory question shows refusal; disclaimer always visible.

---

## Layout and compliance copy

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P4-EC-01 | P0 | Disclaimer “Facts-only. No investment advice.” not visible on load | Fail UX checklist; show persistent banner |
| P4-EC-02 | P1 | Disclaimer scrolled off on mobile | Sticky header/footer or always above input |
| P4-EC-03 | P2 | Welcome text implies recommendations | Reword to facts-only scope |

---

## Example question chips

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P4-EC-04 | P1 | Chip text does not match any of 5 schemes | Use: Mid Cap expense ratio, Silver FoF exit load, Defence benchmark |
| P4-EC-05 | P2 | User taps chip twice quickly | Debounce; single in-flight `/ask` request |
| P4-EC-06 | P2 | Chip sends query but API returns refusal | Display refusal styling distinct from answer |
| P4-EC-07 | P3 | Fourth example chip added (ELSS lock-in) | Remove or disable — ELSS not in corpus |

---

## Chat input and submission

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P4-EC-08 | P1 | Submit empty input | Disable send or inline validation |
| P4-EC-09 | P1 | Paste >500 characters | Truncate client-side or show API error message |
| P4-EC-10 | P1 | Double-click Send | Prevent duplicate messages; idempotent UI state |
| P4-EC-11 | P2 | Newline-only input | Treat as empty |
| P4-EC-12 | P2 | Special characters / emoji in query | Allow; API strips HTML only |

---

## API response rendering

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P4-EC-13 | P1 | `citation_url` present but not rendered as link | Clickable anchor opens in new tab |
| P4-EC-14 | P1 | Footer `Last updated from sources: <date>` missing on bot bubble | Always render below answer text |
| P4-EC-15 | P1 | Response `type: refusal` looks like normal answer | Visual distinction (label, icon, or muted style) |
| P4-EC-16 | P2 | Answer text contains raw markdown URL | Render as single link; don’t show duplicate URLs |
| P4-EC-17 | P2 | Very long 3-sentence answer on small screen | Wrap text; no horizontal scroll |

---

## Error and loading states

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P4-EC-18 | P1 | `/ask` network timeout | User-safe: “Unable to reach assistant. Try again.” |
| P4-EC-19 | P1 | API returns 500 | Show generic error; no stack trace |
| P4-EC-20 | P1 | API returns 400 (empty query) | Inline hint near input |
| P4-EC-21 | P2 | Slow LLM (>10s) | Loading indicator; optional cancel |
| P4-EC-22 | P2 | CORS error (wrong API origin in dev) | Console hint in dev; user message in UI |
| P4-EC-23 | P2 | Empty retrieval / low confidence body | Show “Couldn’t find this in our sources” copy |

---

## Advisory and sensitive input (UI layer)

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P4-EC-24 | P1 | User submits “Should I invest?” via example misuse | Show refusal from API |
| P4-EC-25 | P2 | User enters PAN in chat | API refuses; UI must not echo PAN in history export |

---

## Accessibility and browser

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P4-EC-26 | P2 | Keyboard-only navigation | Send on Enter; focus management after reply |
| P4-EC-27 | P3 | JavaScript disabled | Graceful static message if SPA-only |

---

## Phase 4 test checklist

- [ ] Disclaimer visible on first paint (desktop + mobile width)
- [ ] Three example chips produce valid answers with link + footer
- [ ] Advisory manual query shows refusal UI
- [ ] Network failure shows friendly error
- [ ] No duplicate bot messages on double submit
