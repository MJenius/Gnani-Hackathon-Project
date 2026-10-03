# Architecture

DriveOS is one Next.js console and one FastAPI service. A structured mission graph is the source of truth. The planner proposes tasks; deterministic policy decides whether tools may run. Tool outputs and concise action events are visible, never hidden reasoning.

The first slice accepts a browser transcript, extracts an explicitly requested delay notification, builds one task, runs a synthetic contact tool, persists the result, and speaks a short confirmation. Browser speech is an explicitly labeled development fallback, not Gnani integration. Unsupported missions are escalated instead of silently approximated.

SQLite provides local durable mission, audit and idempotency storage without setup. PostgreSQL is included in Docker for the subsequent shared deployment phase; it is not yet wired into the service. Redis is unnecessary. One transactional execution boundary prevents duplicate simulated mutations. External production tools will need provider idempotency keys and reconciliation after timeouts.

Trust boundaries: bounded request schemas, fixed tool allowlist, server-owned action classes, explicit per-request authorization, and immutable request-key binding. No real calls, messages or payments are sent.

See gnani-integration.md for the credential and API gates before enabling real voice/planning.
