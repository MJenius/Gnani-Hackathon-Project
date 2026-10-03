# Architecture

Final submission runtime: Prisma → DriveOS Mission Interpreter (retained deterministic MockEvon) → deterministic policy → Mission Engine v2 → synthetic external services → replanning → Timbre. Evon was investigated but is not in this runtime unless actual inference is verified. The primary console uses speech_test; legacy live configuration remains an optional, unverified path and is not needed for submission. See [submission](submission.md).

DriveOS is one Next.js console and one FastAPI service. A structured mission graph is the source of truth. The planner proposes tasks; deterministic policy decides whether tools may run. Tool outputs and concise action events are visible, never hidden reasoning.

The primary flow captures bounded mono WAV, sends it server-side to Prisma, conservatively normalizes the transcript, validates a frozen mission plan and deterministic policy, and starts persistent v2 execution. The browser advances synthetic transitions and requests cached Timbre audio for completion/confirmation. Legacy one-notification endpoints remain for compatibility. Simulation uses labeled browser speech; live requires configured EvonClient and never substitutes MockEvon. Unsupported missions escalate.

SQLite provides local durable mission, audit and idempotency storage without setup. PostgreSQL is included in Docker for the subsequent shared deployment phase; it is not yet wired into the service. Redis is unnecessary. One transactional execution boundary prevents duplicate simulated mutations. External production tools will need provider idempotency keys and reconciliation after timeouts.

Trust boundaries: bounded request schemas, fixed tool allowlist, server-owned action classes, explicit per-request authorization, and immutable request-key binding. No real calls, messages or payments are sent.

Server-side dotenv loads credentials. Voice retry keys bind to recording hash, language, authorization, mode, engine selection and demo. Transcripts and successful output WAVs are cached under ignored data/. Completion audio binds to the exact persisted revision; stale requests fail. Usage caps reserve real calls atomically and store metadata only. No raw provider error body or credential enters responses.

MockEvon supplies finite English/Kannada/Hinglish fixtures. EvonClient uses the same frozen input/output for v2 live voice missions when configured; live inference remains unverified and unavailable by default. The UI exposes synthetic failure conditions and task outcomes. No paid GPU, tunnel or agent framework is added.

Mission Engine v2 persists incremental transitions, mutable per-mission external facts, task histories and command/effect identities in the existing SQLite database. The mission console drives the synthetic clock; reload restores the same mission. Deterministic policy gates external counter-offers and sensitive actions independently of the planner. The frozen Evon contract stays unchanged. See mission-engine-v2.md.
