# Submission copy

Claims describe this prototype. No human microphone pass or live external action is implied.

## One sentence

DriveOS turns a supported compound goal into a persistent mission that replans when its synthetic world changes, with real Prisma transcription and Timbre speech integrations.

## 50 words

DriveOS turns a supported spoken or typed goal into a persistent mission. Its deterministic interpreter, policy checks and execution engine coordinate synthetic contact, calendar, parking, fuel and ETA tasks, then replan when conditions change. Real Prisma and Timbre integrations are implemented; human microphone completion and listening still require manual validation.

## 150 words

DriveOS is a voice-first prototype for executing a compound request while keeping its progress inspectable. A supported English, Kannada or Hinglish fixture becomes a frozen MissionPlan through the deterministic DriveOS Mission Interpreter. Policy checks constrain execution, while Mission Engine v2 persists mission identity, task history and results in SQLite.

The signature demonstration notifies Ananya, updates a meeting time, selects parking, responds when the garage becomes full, checks fuel against a shared five-minute detour limit and calculates a synthetic ETA. Replanning retains completed contact and calendar work. The console exposes progress, explanations, confirmation gates and an exportable Mission Record.

Real Prisma transcription and Timbre speech integrations are implemented, with English and Kannada synthetic-input provider observations. External contact, calendar, parking, fuel and maps remain simulated. Hosted Evon is optional and unverified. Human microphone completion, audible playback and real persistent-v2 Hinglish remain unverified. Offline evaluation, chaos checks and API restart recovery provide evidence.

## Technology summary

Python/FastAPI backend; frozen Pydantic MissionPlan; deterministic DriveOS Mission Interpreter (MockEvon, no hosted inference); policy validation; persistent Mission Engine v2 and SQLite; Next.js/React console; native browser mono WAV capture; real backend Prisma STT and Timbre TTS; synthetic CallPilot, calendar, parking, fuel and maps. Hosted Evon is optional and unverified. No additional LLM provider is used.

## Limitations

Finite supported fixtures rather than open-ended planning. External actions and route facts are synthetic: no real phone calls, reservations, purchases or live navigation. English summaries; local unauthenticated API; browser-driven progression; local caches without expiry. Historical provider tests use synthetic input audio. Human microphone completion, listening quality, noisy-car use, real persistent-v2 Hinglish and hosted Evon remain unverified. Check provider credits before manual voice validation.

## 60-second narration

**0–10 seconds:** This is DriveOS: one compound goal, carried through a persistent mission. This demonstration uses text and synthetic external services.

**10–22 seconds:** I’m late for a meeting. Tell Ananya, ask about four thirty, find parking, and get fuel only within five added minutes. The interpreter freezes the plan; policy checks bound each action.

**22–38 seconds:** Contact and calendar tasks finish. The selected garage becomes full. DriveOS replans under the same mission ID, retains completed work, and selects East lot. Fuel fits the remaining shared detour budget.

**38–49 seconds:** The console shows completion, a synthetic ETA, and the Mission Record. Saved state survives an API restart; replay guards reject stale commands.

**49–60 seconds:** Real Prisma and Timbre integrations are implemented. Human microphone completion and listening still need validation. Hosted Evon is optional and unverified. This is an inspectable execution prototype, with honest boundaries.

## Draft public post

DriveOS keeps a supported compound goal moving when the world changes. Watch the same mission replan from a full garage to East lot without repeating completed contact/calendar work. The demo's external services are synthetic; Prisma/Timbre integrations are real, and human voice validation remains pending.

Repository: https://github.com/MJenius/Gnani-Hackathon-Project

Draft tags: #DriveOS #GnaniAI #VoiceAI #Hackathon (organizer requirements unverified).
