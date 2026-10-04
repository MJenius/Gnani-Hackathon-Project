# Final submission checklist

Status meanings: **VERIFIED** = recorded engineering/provider evidence; **UNVERIFIED** = still needs a person or external confirmation; **SIMULATED** = deterministic synthetic services, not real external actions. A human-reported local result does not automatically upgrade these claims.

## Engineering

| Item | Status | Evidence / remaining action |
|---|---|---|
| Unit tests | VERIFIED | 64 passing tests after bounded multilingual slot extraction; includes Latin/Devanagari Hinglish, clause ordering, rejection mutations and persistent Hinglish execution; final commands below |
| Evaluation | VERIFIED | 27/27 expected persistent outcomes; 13/13 supported completion subset |
| Chaos | VERIFIED | 13/13 including actual two-process restart |
| Restart recovery | VERIFIED | Same persisted mission restored and completed after API restart |
| Production build | VERIFIED | Next.js production build |
| Secret scan | VERIFIED | Source, frontend bundles, Git index/history; zero findings |

## Gnani

| Item | Status | Evidence / remaining action |
|---|---|---|
| Prisma | VERIFIED | Real integration; English/Kannada synthetic-input observations on 2026-10-03 and successful human English transcript on 2026-10-04 |
| Timbre | VERIFIED | Real synthesis; English human final playback confirmed audible on 2026-10-04 |
| Evon | UNVERIFIED | Optional hosted endpoint/inference; not required and not claimed as used |
| Current credits | VERIFIED | Human dashboard check before validation; balances are mutable, recheck before further calls; full voice needs at least 3 local requests |

## Human validation

| Item | Status | Evidence / remaining action |
|---|---|---|
| English microphone completion | VERIFIED | Human-confirmed actual English browser run on 2026-10-04; real Prisma → persistent v2 → one replan → COMPLETED |
| Kannada microphone (optional) | UNVERIFIED | Select Kannada, use displayed fixture, record an independent result |
| Hinglish microphone / real persistent-v2 (optional) | UNVERIFIED | Select Hindi/Hinglish; real persistent-v2 integration outcome is not verified |
| English audible final playback | VERIFIED | Real Timbre playback completed and human confirmed audible; broader quality unverified |
| Local outcome mechanism | VERIFIED | Browser-only checkboxes, timestamp, language, result and short notes; no database migration |

## Demo

| Item | Status | Evidence / remaining action |
|---|---|---|
| Changing-world demo | VERIFIED | Tested execution; all external world services SIMULATED: Clean isolated world per run: contact → calendar → parking → garage full → same-mission replan → fuel limit → ETA → completion |
| Repeatability / reset | VERIFIED | Reset clears the active mission/transcript/playback; next Run starts a new clean world; prior records retained; no database edits |
| Judge presets | VERIFIED | Offline evaluation/chaos and bounded failure presets; external services SIMULATED |
| Mission Record | VERIFIED | Actual persisted events and JSON export; external effects represented in that record are synthetic |
| Short promo | VERIFIED | Local Brag render: 22 seconds, 1920×1080, 30 fps, H.264/AAC, 660 frames; actual console, synthetic-service labels and historical pending-human-validation disclosure; this earlier text promo predates the successful human run and is not the final live submission video. See docs/promo-video.md; publication remains unverified |
| 60-second submission video | UNVERIFIED | Script ready; human must record the full demonstration, using actual human English, Prisma and Timbre footage; READY TO RECORD |

## Documentation

| Item | Status | Evidence / remaining action |
|---|---|---|
| README | VERIFIED | Run instructions, honest integration scope and validation links |
| Architecture | VERIFIED | docs/architecture.md |
| Technical design | VERIFIED | docs/technical-design.md |
| Limitations | VERIFIED | README and docs/submission-copy.md disclose synthetic services and unverified voice claims |

## Submission

| Item | Status | Evidence / remaining action |
|---|---|---|
| GitHub repository | VERIFIED | https://github.com/MJenius/Gnani-Hackathon-Project; use latest main for submission; generated video is a local artifact, excluded from Git |
| Public demo post draft | VERIFIED | Copy READY in docs/submission-copy.md |
| Public demo post publication | UNVERIFIED | Human must publish using organizer-required hashtags |
| Hashtags | UNVERIFIED | Use exactly the competition-required hashtags; authoritative list not supplied, no tags invented |
| Final video | UNVERIFIED | Review promo; record/upload required 60-second demo according to organizer rules |
| Final description | VERIFIED | docs/submission-copy.md; human must paste into submission and confirm word limits |

## Human actions (stationary, localhost or HTTPS)

Before starting, check Gnani credits and configure a local request allowance with at least three remaining requests. Do not raise the allowance blindly: it counts requests, not provider credits. After checking the provider balance, set `DRIVEOS_API_MAX_REQUESTS` in the ignored `.env` to a ceiling at least three above the current used count, then restart the API. The local ceiling was raised to 60 after the human checked provider credits; inspect the actual current used/remaining count before a repeat run. Choose English in Voice settings.

> I’m running late for my meeting. Tell Ananya, ask if 4:30 works, find parking near her office, and get fuel if it doesn’t add more than five minutes.

1. Allow microphone access when prompted (normally after Start).
2. Click **Start Gnani voice mission**.
3. Say the request above.
4. Click **Stop and run voice mission** within 15 seconds.
5. Verify actual Prisma transcript, including Ananya, 4:30 and five minutes.
6. Verify mission ID, status and task progress.
7. Verify garage-to-East-lot replanning under the same mission ID.
8. Hear final Timbre playback; press play if autoplay is blocked.

Success requires all eight observations, a completed mission, total detour at most five minutes, and an understandable final spoken result. Permission/capture/provider errors, wrong constraints, escalation/stall, missing replan or unheard audio are failure. Record PASS/FAIL/INCOMPLETE in **Human voice validation**. Results stay in this browser's local storage (last ten); export is optional and ignored by Git. Do not put transcripts, recordings, personal details or credentials in notes. The English pass is human-confirmed on 2026-10-04; these steps remain available for repeat/optional language checks.

## Code-level voice audit

| Stage | Status / boundary |
|---|---|
| Microphone → WAV | Secure-context guard; mono 16 kHz PCM; empty capture rejected; stop releases microphone; English capture human-verified; other hardware/environments unverified |
| WAV → Prisma | Server validates format/size, configured allowance and authorization; credentials backend-only; historical synthetic-input tests plus later human English validation |
| Transcript → interpreter | Conservative Unicode/whitespace normalization; actual received transcript displayed; finite fixture scope preserves name/time/detour; unsupported goals escalate |
| Frozen plan → policy | Frozen schema and allowlisted tools; bounded actions and exact confirmation gates |
| Engine → replanning | Persisted identity/revisions/task histories; affected-task recovery retains committed effects |
| Timbre → browser | Start/final synthesis, saved mission on speech failure, explicit retry/manual play, playback status; only a human can attest hearing |

Fixed readiness gaps: hardware-dependent WAV rate, overlapping capture actions, empty captures, ambiguous stopped/submitted status, reload voice identity, completed-request speech retry, autoplay feedback, and reset without a newly created mission. No known code-level blocker remains after the final checks. English permission/capture/listening were human-confirmed; credits and browser settings must be rechecked for another run.

## Final verification commands

```powershell
python -m unittest discover -s tests -v
python -m app.evaluation.runners.evaluate
python -m app.evaluation.runners.chaos
python -m app.evaluation.runners.mission_demo
python -m app.evaluation.runners.secret_scan
cd app/web
npm run build
```

No provider calls or human microphone simulation are part of these checks. Detailed prior measurements remain in docs/submission-evidence.md; local final logs are in ignored data/final-verification/.

Before the blank-console refinement, browser repeatability was checked with three distinct synthetic missions: Reset → Continue, Run changing-world demo, then Reset → Continue. Each started at revision 0 with an available garage and no selected route, and finished at revision 12 with East lot, fuel, five added minutes and a synthetic 4:30 ETA. Human checkboxes stayed unchecked and no manual result was fabricated.

## Final human English record — 2026-10-04

Input human microphone; STT real Prisma; persistent Mission Engine v2; one successful same-mission replan; COMPLETED; parking East lot; route fuel stop selected within shared five-minute limit; added route time five minutes; simulated ETA 4:30 PM; TTS real Timbre; listening confirmed audible by human. Constraints were preserved semantically; exact punctuation/wording is not claimed. No recording or raw transcript is committed. Human English end-to-end mission: VERIFIED. Human Kannada/Hinglish, real persistent-v2 Hinglish, hosted Evon/real Evon planning and noisy-car performance remain UNVERIFIED.
