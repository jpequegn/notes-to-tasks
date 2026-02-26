# ADR-001: Investigate Three Architectures in Parallel

**Date:** 2026-02-26
**Status:** Accepted
**Deciders:** jpequegn

## Context

We need to extract, score, and share tasks from meeting notes across a small dev team.
Multiple valid architectures exist, each with different trade-offs. Rather than committing
to one upfront, we build and evaluate all three.

## Decision

Build three parallel implementations:

- **A — MCP Server:** Local Python server exposing typed tool calls
- **B — Pure Markdown:** Zero-dependency file-based task storage
- **C — Backlog.md:** Wrapper around an existing markdown task manager

All share the same task schema (`SCHEMA.md`), extraction scripts (`scripts/`), and meeting
note format (`meeting-notes/TEMPLATE.md`).

## Rationale

- We don't have enough data to choose confidently upfront
- The implementations are small enough to build in parallel
- Testing all three reveals trade-offs that aren't obvious from specs
- The shared schema means tasks are portable between implementations

## Consequences

- More initial build effort
- Clearer decision signal after evaluation
- `docs/EVALUATION.md` captures the comparison

## Research basis

Gemini research (2026-02-26) confirmed:
- MCP is production-ready for this use case
- Pure markdown is optimal for solo/1-3 person teams
- Notes-only approaches break at team scale without enforced schema
- The winning pattern for dev teams involves structured extraction into an existing tracker
