# Mission Engine v2

Mission is the persistent object. A validated frozen v1 plan supplies its initial dependency graph. V2 executes one durable transition at a time and preserves task identity/history when conditions change. Evon contract/schema files are unchanged; MockEvon supplies the current signature fixture. The execution runner also accepts any valid graph within that contract, not only the complete four-task signature.

## State and execution

Each mission stores goal, original plan, tasks/dependencies, task state/history/generation, revision, synthetic world, requirements, call state, route/ETA, confirmations and action events in SQLite. Task states: PLANNED, READY, EXECUTING, WAITING_ON_EXTERNAL, REPLANNING, AWAITING_CONFIRMATION, COMPLETED, SKIPPED, BLOCKED, CANCELLED, FAILED. Dependencies gate execution. Independent route tasks can continue while calendar waits for user approval. Unknown/cyclic graphs fail frozen-contract validation.

A command atomically saves its task transition, mission state and synthetic effect. Start keys bind to the request; command keys bind to operation/payload. Replays return current durable state without repeating effects. Revision checks reject stale concurrent commands. Logical notification and calendar effect identities prevent duplicate mutations even when route tasks reopen. Per-task history preserves earlier selections and failures. Service exceptions roll back the attempted transition; prior committed progress remains.

The browser advances the demo every 1.1 seconds. No job framework/background worker is added. Closing the page pauses progression, while SQLite state survives refresh/server restart. Continue resumes the same mission. This local unauthenticated simulator is not an always-on deployment or production driving interface.

## Mutable synthetic services

Contact/call: one queued delay intent, notification delivered at most once after an answer, up to two call attempts, accepted/rejected/no-answer responses and a 16:45 counter-offer. Calendar: simulated original 16:00 meeting, acceptance-gated updates. Parking: garage (2 added minutes), East lot (3), mutable availability and a select-then-verify phase. Fuel: near stop (2), far stop (7), mutable detour and select-then-verify. Maps: synthetic departure 16:00, base travel 25 minutes, recalculated arrival and total detour whenever routing/world/requirements change. These are per-mission facts, not live maps, calls or bookings.

Parking becoming full invalidates the candidate or reopens completed routing; dependent fuel is reconsidered. Rejection exposes the external counter-offer and pauses calendar for explicit approval. No-answer retries once without another notification, then blocks calendar and escalates. Fuel exceeding the **shared parking + fuel** detour allowance is omitted after alternatives are checked. User changes (fuel inclusion, detour limit up to five minutes) selectively reopen routing in the same mission; completed contact/calendar actions remain intact. New traffic estimates recalculate ETA; an arrival later than the agreed time escalates instead of claiming completion. Repeated arbitrary world changes are external input, not unbounded autonomous retries.

The original proposed 16:30 remains in the frozen planner input/output. A verified external counter-offer is a runtime fact, not a rewritten Evon contract. Deterministic policy permits 16:30 only after acceptance; a different time needs explicit confirmation bound to mission/task/arguments/requirement version/task generation. Stale or declined confirmation does not update the calendar. Sensitive purchases remain blocked by the frozen tool allowlist and class-C policy; no purchase API is introduced.

## API

POST /missions/start accepts transcript, request_key, authorized, optional demo=parking-change and optional frozen-contract plan. It persists a graph before running actions. GET /missions/{id} restores current state. POST /missions/{id}/advance progresses one transition. PATCH /missions/{id}/world changes simulated conditions; PATCH /missions/{id}/requirements changes user requirements. POST /missions/{id}/confirm accepts the exact confirmation_id and approved boolean. Commands require request_key + expected_revision. Null/unknown/out-of-range changes fail request validation. Legacy /missions and speech endpoints remain unchanged for their existing tests.

## UI and hands-free demonstration

The main page shows goal, current action, simulated dialing/ringing/connected/request/response call stages, ETA, task history, route/meeting, replans and completion. One changing-world control runs the browser-speech simulation. Gnani voice controls capture WAV → Prisma → frozen-plan validation/policy → persistent v2 → cached Timbre acknowledgement and completion/confirmation. English/Kannada synthetic-input provider runs passed; English human permission/capture, mission completion and audible Timbre playback were verified on 2026-10-04; Kannada/Hinglish human runs and noisy-car quality remain unverified. Browser recognition retains the narrow mid-mission commands. Counter-offers pause for exact approval.

The deterministic demo starts with an open garage. After choosing it but before verifying it, the synthetic world marks it full. The runner records WORLD_CHANGED/DEMO_EVENT/REPLANNING, verifies East lot, recalculates ETA and fits fuel within the remaining allowance, all under the original mission ID. Run python -m app.evaluation.runners.mission_demo for the offline equivalent; evidence is saved under ignored data/.

Automated coverage includes normal mission, mid-execution parking change, rejected time/approval, fuel detour changes, combined no-answer/parking/fuel failures, user changes, persistence/resumption, replay/concurrency, stale/declined confirmation, plan review, unauthorized/invalid mutations and frozen-schema equality. No paid model calls or infrastructure changes are needed.
