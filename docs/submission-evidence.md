# Submission evidence

Refinement measured 2026-10-04 (Asia/Kolkata). External calls, calendar updates, parking/fuel selections, maps and ETA are simulated. No live calls, bookings, purchases, live navigation or production driving support are claimed.

## Offline engine evaluation

| Check | Measured result | Reproduce |
|---|---|---|
| Complete unit suite | 60 tests passed, including the existing untracked Evon smoke test | `python -m unittest discover -s tests -v` |
| Legacy text slice | 3/3 expected outcomes | `python -m app.evaluation.runners.evaluate` |
| Persistent mission evaluation | 27/27 expected outcomes | Same runner; `data/evaluation-results.json` |
| Supported completion subset | 13/13 | Finite supported fixtures plus successful recovery presets; excludes scenarios expected to escalate or await approval |
| Garage replanning | 1/1 | Same runner; parking-change case |
| Bounded no answer | 2/2; each uses exactly two attempts | Same runner; preset and direct world scenario |
| Confirmation compliance | 27/27 | Same runner; rejected-time runs leave calendar unchanged |
| Duplicate notification effects / unsafe tool effects | 0 / 0 across 27 replayed runs | Same runner; not a claim of production exactly-once delivery |
| Named English / Kannada / Hinglish fixtures | 10/10, 1/1, 1/1 | Includes scenario variants for English; language-specific transcription accuracy is not measured |
| Local latency | Median 136.05 ms; mean 101.94 ms | Text → persisted state including replay checks; excludes Prisma, Timbre and browser pacing; machine-dependent |
| Intervention outcomes | 14 across 27 runs | Counts each escalation or pending approval once; not measured human clicks |
| Chaos checks | 13/13 | `python -m app.evaluation.runners.chaos`; `data/chaos-results.json` |
| Stale command/confirmation rejection | Passed rejection and unchanged-state assertions | Named replay and stale-confirmation chaos checks; not a population-rate estimate |
| API restart | Two real API processes; exact saved state restored; same mission completed | `python -m app.evaluation.runners.restart_check auto`; `data/restart-results.json` |

The restart check recorded one call, one actual notification, one calendar update, one parking selection and one fuel selection. Chaos recovery preserves completed task history as well as committed effect counts. Invalid planner output and unsupported secondary missions cannot mutate an already committed mission.

## Real Gnani provider evaluation

Previously recorded on 2026-10-03: real Prisma and Timbre completed English and Kannada persistent-v2 missions using synthetic Timbre input audio. Both returned start/final speech and completed with five detour minutes. Loop latencies were 15,918 ms and 15,990 ms, each including a ten-second cooldown. These are historical provider observations, preserved in `evaluation-evidence.json`, not newly repeated in this pass.

No new provider requests were made during refinement. The configured local allowance has one remaining request; a fresh full voice mission needs at least three. Provider credits have not been reverified. Real persistent-v2 Hinglish remains unverified. Reproduce provider checks only after checking credits and the local allowance:

```powershell
python -m app.evaluation.runners.voice_demo --real --case english --reuse-audio
python -m app.evaluation.runners.voice_demo --real --case kannada --reuse-audio
python -m app.evaluation.runners.voice_demo --real --case hinglish
```

Reuse requires existing ignored synthetic WAVs. These checks do not test a human microphone.

## Human microphone validation

End-to-end microphone completion, listening quality and noisy-car performance remain unverified. An earlier human transcript was observed but the mission escalated; accepting that transcript offline does not retroactively establish live completion. The manual gate is: record each displayed English/Kannada/Hinglish fixture, inspect actual Prisma text and constraints, complete the same mission, and listen to the final Timbre result. Record the outcome honestly, including failures.

## Build, secrets and browser

Production frontend build passed. The final secret scan checked 80 source files plus 11 frontend bundle files, the Git index and history, with zero findings. The browser signature mission completed under the same ID at revision 12: East lot, Route fuel stop, five added minutes, 4:30 ETA and 24 persisted events. Duplicate/stale-revision guards preserved state; a genuinely retired counter-offer approval was rejected with the calendar unchanged. Browser service recovery completed the same mission with one contact notification, calendar update and parking selection. The evidence export returned exact persisted JSON through the frontend proxy.

These measurements are also recorded in the [machine-readable evidence snapshot](evaluation-evidence.json). Browser rehearsal uses text and labeled browser speech fallback; it does not count as Gnani validation. The Mission Record is persisted backend evidence rather than model reasoning or prerecorded animation.

## Evon

Hosted inference remains unavailable/unverified: no verified endpoint/base URL. `MockEvon` is the deterministic DriveOS interpreter. The frozen v1 contract remains unchanged, enabling a verified structured-plan provider to be inserted later. No other LLM provider was added.
