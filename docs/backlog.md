# Phased implementation backlog

## Track A — product development (independent of GPU access)

Foundation, Mission Engine v1 and persistent v2 implemented (see mission-engine-v2.md): strict fixture planner (MockEvon), dependency validation, bounded synthetic contact negotiation, acceptance-gated calendar, parking alternative/replan, shared parking/fuel detour budget, SQLite atomic effects and request replay, console conditions/task outcomes. Unsupported requests escalate. No real calls, bookings, purchases or arbitrary-language planning are claimed.

V2 adds mutable world events, persisted waiting/resume, exact counter-offer approval, synthetic ETA, requirement changes and staged CallPilot. Real Prisma/Timbre now wraps v2; English/Kannada synthetic-input signature runs passed. Finite multilingual/transcription fixtures and machine-readable mission evaluation exist. Personal/work/delivery fixtures escalate under the unchanged contract. English human microphone completion and audible Timbre playback are verified on 2026-10-04. Next: optional Kannada/Hinglish human QA, noisy recordings, reviewed broader contract, authentication, external-provider reconciliation and production retention.

## Track B — Evon verification

Official gated access passed; original BF16 inference is infeasible on the laptop. An authenticated free dual-T4 Kaggle run now tests the community GGUF path: Q3_K_S → Q3_K_M → IQ4_XS. Gate A load, B English, C Kannada, D expected plans/repeated structured JSON. See evon-free-notebook.md for actual results; no inference success is inferred from successful compilation. HTTP exposure remains deferred; no tunnel exists. Preserve the adapter and MockEvon regardless of outcome.

Real synthetic English/Kannada signature audio and sanitized results are retained under ignored data/. Actual microphone → Prisma → Evon → policy → tool → Timbre remains a separate gate. No paid GPU, new paid inference or tunnel was introduced.
