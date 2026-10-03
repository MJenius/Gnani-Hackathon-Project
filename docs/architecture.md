# Architecture

DriveOS is one Next.js console and one FastAPI service. A structured mission graph is the source of truth. The planner proposes tasks; deterministic policy decides whether tools may run. Tool outputs and concise action events are visible, never hidden reasoning.

The first slice accepts a browser transcript, extracts an explicitly requested delay notification, builds one task, runs a synthetic contact tool, persists the result, and speaks a short confirmation. Simulation keeps browser speech as a labeled fallback. Gnani speech-test mode uses real Prisma/Timbre around the demo planner; full live mode requires a deployed EvonClient and never silently substitutes simulation. Unsupported missions are escalated instead of silently approximated.

SQLite provides local durable mission, audit and idempotency storage without setup. PostgreSQL is included in Docker for the subsequent shared deployment phase; it is not yet wired into the service. Redis is unnecessary. One transactional execution boundary prevents duplicate simulated mutations. External production tools will need provider idempotency keys and reconciliation after timeouts.

Trust boundaries: bounded request schemas, fixed tool allowlist, server-owned action classes, explicit per-request authorization, and immutable request-key binding. No real calls, messages or payments are sent.

Server-side dotenv loads local credentials. Voice retry keys bind to recording hashes, language, authorization and mode; only transcripts are cached. Usage caps reserve paid calls atomically and store metadata only. See gnani-integration.md for verified contracts and evon-development.md for the inference gate.

Product development and model verification are independent tracks. MockEvon supplies frozen v1 fixture plans; the dependency runner executes synthetic negotiation/calendar/parking/fuel tools. EvonClient also accepts the same structured input and validates v1 output, but the existing live voice slice stays narrow until real v1 inference/transport is verified. The UI exposes synthetic failure conditions and per-task outcomes. No paid GPU or tunnel is added.
