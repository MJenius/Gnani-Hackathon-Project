# DriveOS submission brief

## Problem and user

Drivers and field workers have occupied hands and limited attention. A single delay can require informing someone, negotiating a meeting time and adjusting parking/fuel plans. Repeating those tasks in separate apps makes execution hard to track.

## Product and why voice matters

DriveOS is a voice-first mission execution layer for people whose hands and attention are occupied. A compound spoken request becomes one accountable mission with task dependencies, external state, policy decisions and completion evidence. Voice provides a single input and audible outcome; the console makes that execution inspectable. This prototype does not establish safe use while driving; demonstrate it while stationary.

## Architecture

Microphone → bounded mono WAV → Prisma → normalized transcript → DriveOS Mission Interpreter → deterministic policy → persistent Mission Engine v2 → synthetic external services → same-mission replanning → Timbre → browser playback.

The existing Next.js/FastAPI/SQLite architecture is preserved. MockEvon is retained as the deterministic interpreter and test planner. It matches the documented fixture scope and never represents model inference. Frozen v1 plans, allowlisted actions and the existing v2 engine remain unchanged. Browser progression advances actual persisted backend transitions; there is no prerecorded animation.

## Gnani APIs actually used

- Prisma v2.5: backend transcription via `POST /stt/v3`.
- Timbre v2.5: backend WAV synthesis via `POST /api/v1/tts/inference`.

Real English and Kannada synthetic-audio signature runs completed through Prisma, v2 and Timbre. Existing provider evidence is preserved in [evaluation-evidence.json](evaluation-evidence.json). The current changes were validated offline; no new provider requests were spent. The primary runtime requires no Evon deployment.

## Demo flow

Use the [60-second script](demo-script.md), [architecture diagram](architecture.md) and [technical design](technical-design.md) for the final demonstration and engineering review.

Say: “I'm running late for my meeting. Tell Ananya, ask if 4:30 works, find parking near her office, and get fuel if it doesn't add more than five minutes.”

DriveOS creates one mission, negotiates through synthetic CallPilot, updates the synthetic calendar after acceptance, discovers parking, observes the garage becoming unavailable, selects East lot, keeps fuel within the five-minute shared detour constraint and recalculates ETA. All revisions retain the mission ID. Timbre provides start and completion feedback in real speech mode.

Use the visible voice result to inspect recording completion, transcript, mission ID/status, progress, replans and actual audio playback events. Inspect the task timeline and action log for execution evidence. Counter-offers require approval of the exact displayed action. The Personal, Work and Delivery examples visibly escalate unsupported pharmacy, inventory and shipment actions.

## What is simulated

CallPilot calls/contact responses, calendar contents and changes, parking availability, fuel stops, maps, traffic, time and ETA are local synthetic services. No external phone call, booking, reservation, purchase or live navigation is real. Browser speech in the offline changing-world demo is labeled simulation; real speech mode uses Prisma and Timbre.

## Evaluation evidence

The 2026-10-04 refinement passes 60 tests, 27/27 offline mission outcomes, 13/13 supported completion runs and 13/13 chaos checks. The automatic API restart check restores exact committed state across two processes and completes the same mission without repeating contact/calendar effects. Production build and secret scan pass. See [submission evidence](submission-evidence.md) for denominators, latency scope, reproduction commands and manual gates; [machine-readable evidence](evaluation-evidence.json) keeps offline and provider measurements separate.

Real English/Kannada Prisma/Timbre synthetic-audio v2 results are historical observations from 2026-10-03. No new provider requests were spent in this refinement. Human microphone completion/listening and persistent-v2 Hinglish speech remain unverified. One request remains in the local allowance, below the three needed for a new full voice run; provider credits have not been reverified.

## Safety model

Strict input/frozen plan schemas, allowlisted tools and deterministic authorization gates own execution. Exact confirmation IDs bind the proposed action and mission/task generation; revision checks reject stale commands. Immutable request-key fingerprints and durable command/effect identities prevent duplicate synthetic actions. Replanning retains completed calls/calendar work. Unknown clauses, negations, names, times or constraints escalate instead of being guessed. Speech errors leave committed mission state intact. Successful STT and exact-revision output caches preserve manual retries without repeating completed effects.

## Evon status

Evon was investigated as the reasoning model but is not part of the final runtime path unless an actual verified deployment becomes available. Weight access and experimental notebook work are separate from inference. Actual inference is unavailable/unverified. MockEvon is deterministic local code, not Evon. No substitute LLM is presented as Evon; optional legacy live code fails closed.

## Limitations

Finite English/Kannada/Hinglish fixtures, English completion summaries, local unauthenticated backend, browser-driven synthetic clock and local caches without automatic expiry. No production tool integration or provider reconciliation. External actions and facts are simulated. Human capture-to-completion/listening, real Hinglish v2 speech and noisy-car performance remain gates, not claimed successes.

## Run locally

From the root:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd app/web
npm ci
npm run dev
```

Open http://127.0.0.1:3000. For speech, copy `.env.example` to ignored `.env`, set backend `GNANI_API_KEY`, then restart the API. Use localhost/HTTPS and allow microphone access. Keep recordings, databases and credentials untracked. Text rehearsal needs no credentials. Full verification and exact multilingual fixtures are linked from [README](../README.md).

## 60-second demo script

- **0–8 seconds:** “DriveOS turns one voice request into a mission for someone whose hands and attention are occupied. Prisma hears; the mission engine executes and replans; Timbre speaks.”
- **8–23 seconds:** Select English and start real Gnani capture if the human gate and credit allowance have been checked. Say the exact compound request and stop. Otherwise click Run changing-world demo and explicitly say this is the offline simulation.
- **23–38 seconds:** Point to the mission ID, call state and tasks. “The synthetic contact accepts 4:30. Calendar and route tasks are tracked under this same mission.”
- **38–48 seconds:** Show the world change/replan and East lot. “The garage becomes unavailable. DriveOS keeps completed work and fits parking plus fuel inside five added minutes.”
- **48–60 seconds:** Show 4:30 ETA and completion; let Timbre play in real mode. “Prisma and Timbre are real. Calls, calendar and route services are simulated. The interpreter is deterministic; Evon inference and successful human completion are not claimed.”

Timing is a presentation target, not an end-to-end latency guarantee. If provider or playback fails, show the persisted mission and saved result; do not describe offline/browser speech as live Gnani output.
