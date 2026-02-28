# Meeting: Product Sync

**Date:** 2026-02-28
**Attendees:** @julien, @alice, @bob
**Facilitator:** @julien
**Note-taker:** @alice

---

## Agenda

1. Q1 launch readiness
2. Auth bug reports
3. API rate limiting design

---

## Discussion

### Q1 launch readiness

We're targeting March 14 for the public launch. Main blockers are auth reliability and the
onboarding flow still being too long (5 steps, want to get to 3). Marketing has the landing
page copy ready and is waiting on us.

Bob flagged that the staging environment is missing the new env vars for the payment provider.
Needs to be fixed before QA can sign off.

### Auth bug reports

Three users reported being logged out unexpectedly after about 20 minutes. Looks like the JWT
refresh logic isn't handling token expiry correctly when the tab is in the background. Alice
has a reproduction case. This is blocking the enterprise pilot — Acme Corp won't sign off
until it's fixed.

### API rate limiting

We agreed to implement rate limiting before launch to prevent abuse. Bob proposed 100 req/min
per API key with a 429 response and Retry-After header. Need to decide on storage: Redis vs
in-memory. Redis is more correct but adds an infra dependency. Decision: Redis, we already use
it for sessions.

---

## Action Items

- [ ] **@alice** — Fix JWT refresh logic for background tab token expiry — due 2026-03-03 — blocking enterprise pilot
- [ ] **@julien** — Reduce onboarding flow from 5 steps to 3 steps — due 2026-03-10
- [ ] **@bob** — Add missing payment provider env vars to staging — due 2026-02-28 — blocking QA signoff
- [ ] **@bob** — Implement Redis-backed rate limiting (100 req/min per API key, 429 + Retry-After) — due 2026-03-07
- [ ] **@julien** — Write API rate limiting docs for developer portal — due 2026-03-10
- [ ] **@alice** — Coordinate with Acme Corp to schedule enterprise pilot after JWT fix

---

## Decisions

- Rate limiting: Redis (not in-memory) — already in stack, correctness worth the dependency
- Launch date: March 14 is firm — no slip without explicit sign-off from all three

---

## Next meeting

**Date:** 2026-03-07
**Agenda:** Launch readiness check, rate limiting QA, pilot status
