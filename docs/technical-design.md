# DriveOS execution design

DriveOS is a voice-first mission execution layer for people whose hands and attention are occupied. The reasoning component is replaceable; execution, policy, persistence and recovery belong to DriveOS.

## Planner and executor boundary

Prisma transcribes bounded mono WAV. Conservative normalization feeds the deterministic DriveOS Mission Interpreter, implemented by `MockEvon`. It matches finite English, Kannada and Hinglish fixtures; it does not perform model inference. The frozen `MissionPlan` v1 schema validates tools, arguments and dependencies. Server-owned policy checks authorization before effects. An optional verified Evon deployment could replace the interpreter through this same contract; no verified endpoint is currently available.

The console exposes actions and results, never hidden model reasoning. An unsupported pharmacy or inventory request produces an empty plan and safe escalation, with no invented tool capability.

## Mission and dependency state

A mission stores its ID, original transcript, validated plan, revision, requirements version, synthetic world, route, ETA, confirmation, tasks and events. Each task has a stable ID, tool, inputs, dependencies, status, generation, attempts, candidate, output and transition history.

For the signature mission:

```text
contact.negotiate → calendar.reschedule
parking.select   → fuel.select
```

The engine schedules the first ready task in plan order. Dependencies become ready only after predecessors reach a terminal state. Failed, blocked or cancelled prerequisites block dependent tasks; a skipped optional task does not imply a successful external effect. Independent routing can still complete when contact fails.

Task states include `PLANNED`, `READY`, `EXECUTING`, `WAITING_ON_EXTERNAL`, `REPLANNING`, `AWAITING_CONFIRMATION` and terminal outcomes. Mission status is derived from tasks and constraints. A late route escalates even if individual actions completed. Replanning is an event/transition, often followed by a ready task in the same transaction; the console keeps the replan visible instead of implying it is a long-running model thought.

## Durable transitions and idempotency

SQLite `BEGIN IMMEDIATE` serializes local commands. A transaction writes mission state, command identity and synthetic effect identities together. An unexpected exception rolls back the whole current transition while retaining earlier committed transitions. A known synthetic fuel outage persists a `FAILED` task and honest escalation; restoring that service reopens only fuel.

Three durable identities protect replay:

| Identity | Binding | Behavior |
|---|---|---|
| Start key | Full request fingerprint | Same request returns the existing mission; conflicting reuse fails |
| Mission command key | Operation and command fingerprint | Exact replay returns current saved state; conflicting reuse fails |
| Effect key | Mission and semantic action token | Existing identical effect is reused; conflicting payload fails |

Notification intent and actual notification use distinct keys. Calls use bounded attempt numbers. Calendar effects bind the agreed time. Route effects bind task generation and selected candidate. A changed route may legitimately select a new candidate; replay of the same transition does not repeat its effect.

These guarantees apply to the tested SQLite synthetic effects. A real external provider cannot share this transaction: it would require provider idempotency keys, durable dispatch and timeout reconciliation. DriveOS does not claim distributed exactly-once execution.

## Revisions and confirmations

Every new command supplies the expected current revision. A stale revision returns HTTP 409 without mutating the mission. Successful commands increment the revision, including accepted no-op mutations. Exact replay is checked before revision matching so a retry can recover after a lost response.

A confirmation hashes mission/task identity, action, arguments, requirements version and task generation. Approval supplies both that exact ID and the current revision. Changed requirements or renewed negotiation invalidate the old approval. A 4:45 counter-offer leaves the synthetic calendar unchanged until approved. Original authorization permits the originally requested 4:30 after verified acceptance.

## Same-mission replanning

The world changes availability, contact response, fuel detour or travel time. Candidates are verified again before selection. A vanished garage clears the candidate, increments parking generation and retries a feasible alternative. A changed completed route reopens affected parking/fuel tasks while contact and calendar histories remain completed. Fuel uses the shared remaining budget, not an independent five minutes.

Each replan stores a concise explanation: trigger, affected task IDs, selected alternative and constraint impact. Initially the alternative is pending verification; the persisted record is enriched when that affected task resolves. It is operational evidence, not a reasoning trace.

```text
Trigger: Office garage unavailable
Affected: parking
Alternative: East lot
Impact: +3 min; shared route limit 5 min
Result: fuel +2 min → total +5 min → simulated ETA 4:30
```

No answer uses at most two call attempts. A rejected time with no counter-offer blocks the meeting task. A revised ETA later than the agreed time escalates for another agreement, without silently changing the calendar again.

## Synthetic world and judge mode

Each new mission owns a fresh deterministic world; resets clear the console selection while preserving saved records. Presets change genuine backend state after relevant commits. Parking disappears after its initial candidate; fuel/service/traffic conditions change after the calendar commit. The requirement-change preset models a user removing fuel. The browser drives one transition roughly every 1.1 seconds; this pacing is not included in offline engine latency. Closing the console pauses synthetic execution.

Call stages are dialing, ringing, connected, request communicated and structured response received. Accepted, counter-offer and no-answer outcomes drive mission state. None represent real telephony.

## Voice failures and recovery

Recording retries bind audio hash, language, authorization, mode and engine/demo selection. Successful transcription is cached. Timbre output is cached by exact mission revision, and stale summary requests fail. STT/TTS failures cannot undo committed mission actions. The backend alone holds credentials. The local request allowance is a request counter, not provider credit verification.

## Evaluation methodology

`evaluate` uses isolated SQLite state, finite labeled transcript fixtures and bounded execution. It checks outcomes, dependencies, constraint preservation, notification duplication, policy outcomes and local latency. It intentionally blocks network calls. `chaos` reuses recovery unit assertions, then restarts two actual API processes against one isolated database, comparing exact saved state and committed effect counts.

Three evidence classes remain separate: offline engine evaluation; real Gnani checks using synthetic audio; human microphone completion and listening. Offline percentages are fixture results, not speech accuracy or production reliability. Report sample sizes and local latency scope alongside rates. The evidence file preserves earlier provider records and dates them separately from this pass.

## Known limits

Local unauthenticated demo; SQLite write lock spans planning; finite interpreter fixtures; no background execution; English result speech; unbounded cache retention; synthetic calendar/maps/fuel/parking/contact; no real phone calls, purchases, bookings or live navigation. Human microphone completion/listening, persistent-v2 Hinglish provider verification, noisy-car quality and production driving support remain unverified.
