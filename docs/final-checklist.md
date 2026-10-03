# Final submission checklist

Status meanings: **VERIFIED** = recorded engineering/provider evidence; **UNVERIFIED** = still needs a person or external confirmation; **SIMULATED** = deterministic synthetic services, not real external actions. A human-reported local result does not automatically upgrade these claims.

## Engineering

| Item | Status | Evidence / remaining action |
|---|---|---|
| Unit tests | VERIFIED | 60 passing tests; final commands below |
| Evaluation | VERIFIED | 27/27 expected persistent outcomes; 13/13 supported completion subset |
| Chaos | VERIFIED | 13/13 including actual two-process restart |
| Restart recovery | VERIFIED | Same persisted mission restored and completed after API restart |
| Production build | VERIFIED | Next.js production build |
| Secret scan | VERIFIED | Source, frontend bundles, Git index/history; zero findings |

## Gnani

| Item | Status | Evidence / remaining action |
|---|---|---|
| Prisma | VERIFIED | Implemented real backend integration; historical English/Kannada synthetic-input observations on 2026-10-03 |
| Timbre | VERIFIED | Historical real start/final WAV synthesis; human listening still unverified |
| Evon | UNVERIFIED | Optional hosted endpoint/inference; not required and not claimed as used |
| Current credits | UNVERIFIED | Check provider balance before new calls; local allowance last observed 1 remaining, full voice needs at least 3 |

## Human validation

| Item | Status | Evidence / remaining action |
|---|---|---|
| English microphone completion | UNVERIFIED | Perform the eight steps below; no automated microphone substitute |
| Kannada microphone (optional) | UNVERIFIED | Select Kannada, use displayed fixture, record an independent result |
| Hinglish microphone / real persistent-v2 (optional) | UNVERIFIED | Select Hindi/Hinglish; real persistent-v2 integration outcome is not verified |
| Audible final playback | UNVERIFIED | Person must hear and understand final Timbre summary; browser events alone are insufficient |
| Local outcome mechanism | VERIFIED | Browser-only checkboxes, timestamp, language, result and short notes; no database migration |

## Demo

| Item | Status | Evidence / remaining action |
|---|---|---|
| Changing-world demo | SIMULATED | Clean isolated world per run: contact → calendar → parking → garage full → same-mission replan → fuel limit → ETA → completion |
| Repeatability / reset | VERIFIED | Reset creates a new paused persisted mission; Continue executes; prior records retained; no database edits |
| Mission Record | VERIFIED | Actual persisted events and JSON export; external effects represented in that record are synthetic |
| Short promo | VERIFIED | Local Brag render: 22 seconds, 1920×1080, 30 fps, H.264/AAC, 660 frames; actual console, synthetic-service labels and pending-human-validation disclosure. See docs/promo-video.md; publication remains unverified |
| 60-second submission video | UNVERIFIED | Script ready; human must record the full demonstration, including honest validation status |

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
| Public demo post | UNVERIFIED | Draft only; human must publish |
| Hashtags | UNVERIFIED | Draft: #DriveOS #GnaniAI #VoiceAI #Hackathon; confirm organizer-required tags |
| Final video | UNVERIFIED | Review promo; record/upload required 60-second demo according to organizer rules |
| Final description | VERIFIED | docs/submission-copy.md; human must paste into submission and confirm word limits |

## Human actions (stationary, localhost or HTTPS)

Before starting, check Gnani credits and configure a local request allowance with at least three remaining requests. Do not raise the allowance blindly: it counts requests, not provider credits. After checking the provider balance, set `DRIVEOS_API_MAX_REQUESTS` in the ignored `.env` to a ceiling at least three above the current used count, then restart the API. With the last observed 42 used requests, that means at least 45; recheck the actual current count first. Choose English in Voice settings.

> I’m running late for my meeting. Tell Ananya, ask if 4:30 works, find parking near her office, and get fuel if it doesn’t add more than five minutes.

1. Allow microphone access when prompted (normally after Start).
2. Click **Start Gnani voice mission**.
3. Say the request above.
4. Click **Stop and run voice mission** within 15 seconds.
5. Verify actual Prisma transcript, including Ananya, 4:30 and five minutes.
6. Verify mission ID, status and task progress.
7. Verify garage-to-East-lot replanning under the same mission ID.
8. Hear final Timbre playback; press play if autoplay is blocked.

Success requires all eight observations, a completed mission, total detour at most five minutes, and an understandable final spoken result. Permission/capture/provider errors, wrong constraints, escalation/stall, missing replan or unheard audio are failure. Record PASS/FAIL/INCOMPLETE in **Human voice validation**. Results stay in this browser's local storage (last ten); export is optional and ignored by Git. Do not put transcripts, recordings, personal details or credentials in notes. No human pass is claimed here.

## Code-level voice audit

| Stage | Status / boundary |
|---|---|
| Microphone → WAV | Secure-context guard; mono 16 kHz PCM; empty capture rejected; stop releases microphone; human hardware remains unverified |
| WAV → Prisma | Server validates format/size, configured allowance and authorization; credentials backend-only; real provider observations are historical |
| Transcript → interpreter | Conservative Unicode/whitespace normalization; actual received transcript displayed; finite fixture scope preserves name/time/detour; unsupported goals escalate |
| Frozen plan → policy | Frozen schema and allowlisted tools; bounded actions and exact confirmation gates |
| Engine → replanning | Persisted identity/revisions/task histories; affected-task recovery retains committed effects |
| Timbre → browser | Start/final synthesis, saved mission on speech failure, explicit retry/manual play, playback status; only a human can attest hearing |

Fixed readiness gaps: hardware-dependent WAV rate, overlapping capture actions, empty captures, ambiguous stopped/submitted status, reload voice identity, completed-request speech retry, autoplay feedback, and reset without a newly created mission. No known code-level blocker remains after the final checks. Credits, browser permission and actual listening remain manual gates.

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

Browser repeatability was checked with three distinct synthetic missions: Reset → Continue, Run changing-world demo, then Reset → Continue. Each started at revision 0 with an available garage and no selected route, and finished at revision 12 with East lot, fuel, five added minutes and a synthetic 4:30 ETA. Human checkboxes stayed unchecked and no manual result was fabricated.
