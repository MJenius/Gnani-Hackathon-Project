# Phased implementation backlog

## Track A — product development (independent of GPU access)

Foundation and first Mission Engine v1 implemented: strict fixture planner (MockEvon), dependency validation, bounded synthetic contact negotiation, acceptance-gated calendar, parking alternative/replan, shared parking/fuel detour budget, SQLite atomic effects and request replay, console conditions/task outcomes. Unsupported requests escalate. No real calls, bookings, purchases or arbitrary-language planning are claimed.

Next: richer negotiated alternatives, asynchronous waiting/resume/cancellation, route ETA source, authenticated concrete-action confirmations, provider reconciliation, production storage/retention. Then broaden personal/work/delivery scenarios and noisy-microphone UX.

## Track B — Evon verification

Official gated model access passed; original BF16 inference is infeasible on the laptop. Free llama.cpp community GGUF notebook prepared: Q3_K_S → Q3_K_M → IQ4_XS. Gate A load, B English, C Kannada, D known expected plans/repeated structured JSON. Actual free GPU tests await authenticated Kaggle/Colab access. Only after A–D pass investigate authenticated HTTP exposure (E); no tunnel code is currently implemented. Keep the provider-agnostic adapter and MockEvon regardless of outcome.

Prisma/Timbre synthetic real tests already passed. Reusable speech fixture storage/replay is prepared without spending further credits; audio slots are currently empty because previous audio was not saved. Actual microphone → Prisma → Evon → policy → tool → Timbre remains an integration gate, not a blocker for Track A.
