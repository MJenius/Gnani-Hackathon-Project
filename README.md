# DriveOS

**DriveOS is a voice-first mission execution layer for people whose hands and attention are occupied.**

Prisma hears the driver. DriveOS converts a supported request into an accountable mission. Mission Engine v2 executes, observes changes and replans under the same mission ID. Timbre speaks the result. The console shows task progress, call state, world change, revised plan, ETA and completion.

## Final runtime

Microphone -> mono WAV -> real Prisma -> normalized transcript -> DriveOS Mission Interpreter -> deterministic policy -> persistent Mission Engine v2 -> synthetic services -> replanning -> real Timbre -> browser playback.

The interpreter is the retained **MockEvon** implementation: a deterministic matcher for documented English, Kannada and Hinglish fixtures, with no inference or general reasoning. Equivalent time forms (`four thirty`, `04:30`), punctuation and bounded fillers are accepted. Unknown names, times, constraints, negations and additional actions safely escalate. The frozen schema and allowlist are unchanged.

Evon was investigated as the reasoning model but is **not part of the final runtime path** unless an actual verified deployment becomes available. Evon inference remains unavailable/unverified. No other LLM substitutes for Evon. Optional legacy live endpoints fail closed; the primary demo requires only Prisma and Timbre.

**All contact calls, negotiation, calendar changes, parking, fuel and maps/ETA facts are simulated.** Synthetic CallPilot is a local service, not verified Gnani telephony. No real calls, bookings, purchases or navigation occur.

## Run locally

From the repository root, with Python and Node.js installed:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd app/web
npm ci
npm run dev
```

Open [DriveOS](http://127.0.0.1:3000). Copy `.env.example` to `.env`, set backend `GNANI_API_KEY` for real speech, and restart the API. Evon configuration is unnecessary. Text simulation works without credentials. SQLite state, transcripts, usage and speech caches stay in ignored `data/`. The browser drives the synthetic clock; closing pauses progression and reopening restores persisted state.

## Hackathon Demo

1. Rehearse with **Run changing-world demo**. The synthetic call rings, connects and accepts 4:30. The garage becomes unavailable during execution. The same mission replans to East lot, retains fuel within five shared detour minutes and recalculates ETA to 4:30. These are backend transitions, not a prerecorded animation. Offline feedback uses browser speech.
2. For real speech, enable microphone permission on localhost/HTTPS and configure backend credentials. Ensure at least **three remaining requests** in the local allowance. Check provider credits before adjusting the allowance; the local counter is not a credit balance.
3. Select **Prisma / DriveOS Interpreter / Timbre**, choose English, click **Start Gnani voice mission**, say the exact request below, then **Stop and run voice mission**. Capture stops automatically after 15 seconds.
4. Watch **VOICE MISSION RESULT** for capture completion, actual Prisma transcript, mission ID/status, progress, replans and Timbre playback events. The timeline and action log show accountable execution. Autoplay restrictions may require pressing play.
5. Use **Retry same recording** on network failure; it retains request identity. Use **Speak current result with Timbre** if final speech fails. State remains committed and successful audio is cached by exact revision.

> I'm running late for my meeting. Tell Ananya, ask if 4:30 works, find parking near her office, and get fuel if it doesn't add more than five minutes.

For Kannada and Hinglish, select the corresponding language and read the exact `kannada` or `hinglish` text in [voice fixtures](app/evaluation/fixtures/voice_missions.json). Supported fixture scope is finite. Real English and Kannada synthetic-audio v2 runs are verified; real Hinglish v2 and human microphone completion/listening remain unverified. Completion summaries are currently spoken in English.

Personal, Work and Delivery buttons visibly escalate pharmacy, inventory and shipment requests that the frozen contract cannot represent. They do not advertise implemented external effects.

## Technology

- **Gnani Prisma v2.5:** real backend REST transcription, `POST /stt/v3`.
- **Gnani Timbre v2.5:** real backend synthesis, `POST /api/v1/tts/inference`, WAV browser playback.
- Existing Next.js console, FastAPI, deterministic interpreter/policy, SQLite Mission Engine v2 and synthetic world services. No new framework or paid infrastructure.

[Integration details](docs/gnani-integration.md) document implemented contracts. Credentials never enter browser variables or bundles.

## Measured evidence - 2026-10-03

[Evidence snapshot](docs/evaluation-evidence.json) contains the latest offline evaluation and earlier real provider results. These measurements describe the fixture scope.

| Check | Result |
|---|---|
| Unit suite | 53 passed |
| Offline v2 expected outcomes | 21/21 |
| Supported mission completion | 11/11, including changing-world case |
| Replanning / no-answer | 1/1 each; no-answer bounded to 2 attempts |
| Duplicate notification / unsafe effects | 0 / 0 |
| Confirmation compliance | 21/21 |
| English / Kannada / Hinglish named fixture runs | 4/4, 1/1, 1/1 valid respectively |
| Median local mission latency | 119.37 ms; excludes speech and browser pacing |
| Real synthetic-audio English / Kannada v2 | Both completed with start/final Timbre audio and 5-minute detour |
| Real speech loop latency | English 15,918 ms; Kannada 15,990 ms; includes 10-second cooldown |
| Human microphone completion | Unverified; earlier transcript observed, but attempt escalated |
| Frontend / changing-world browser | Build passed; browser completed with East lot, fuel and 4:30 ETA |
| Secret scan | 0 findings; no tracked credentials, recordings or local databases |

## Verify

```powershell
python -m unittest discover -s tests -v
python -m app.evaluation.runners.evaluate
python -m app.evaluation.runners.mission_demo
python -m app.evaluation.runners.secret_scan
cd app/web
npm run build
```

Opt-in real provider checks use existing speech credits:

```powershell
python -m app.evaluation.runners.voice_demo --real --case english
python -m app.evaluation.runners.voice_demo --real --case kannada
python -m app.evaluation.runners.voice_demo --real --case hinglish
```

Each synthesizes input, transcribes it, runs persistent v2 and requests start/completion audio. No automated paid retries. `--reuse-audio` uses an existing ignored WAV. Synthetic checks do not establish microphone accuracy or pronunciation.

## Safety and limitations

Strict schemas and allowlists reject unsupported behavior. Counter-offers require the exact displayed confirmation ID and current revision; stale approval fails. Bound keys, durable command/effect identities and transactions prevent duplicate synthetic effects. Replanning retains completed contact/calendar work. Speech failures preserve committed mission state.

This is an unauthenticated local demo with a synthetic clock, finite interpretation scope and caches without automatic expiry. Real external services, noisy-car quality and human listening remain gates. See [submission brief and 60-second script](docs/submission.md), [architecture](docs/architecture.md) and [Mission Engine v2](docs/mission-engine-v2.md).
