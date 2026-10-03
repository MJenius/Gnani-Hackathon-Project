# Phase 0 checkpoint — 2026-10-03

Completed: master context/specifications reviewed; speech key and HF token stored in ignored local `.env`; Git/Docker secret exclusions; official speech API contracts; real English Prisma/Timbre round trip; real Kannada and Kannada–English round trips; separate simulation/speech-test/live modes; server-side adapters, metadata logging, local call caps and offline tests.

Initial English mission TTS ~1,342 ms and STT ~464 ms. Kannada script, synthetic contact and numeric delay were detected in appropriate cases. These single synthetic observations are not benchmarks or noisy-microphone accuracy evaluations. Testing encountered HTTP 429 and stopped without automatic retries.

Numbers/time and date synthesis/transcription cases passed, with digits detected. The integrated real Prisma → demo planner → simulated notification → real Timbre loop passed with synthetic in-memory audio and a valid 3.84-second output WAV. The measured loop took ~1,790 ms after input was provided (excluding fixture generation and cooldown). Back-to-back fixture/response synthesis hit 429; spacing those separate TTS requests by 10 seconds passed. This is an observation, not a verified account rate limit. Browser microphone behavior still needs a user microphone check.

Full Prisma → Evon → policy → tool → Timbre remains blocked: HF token/model access succeeded but local RAM/GPU/disk cannot support the official weights, and no hosted inference service is available. Actual English/Kannada Evon structured-output tests therefore remain unverified; mocked contracts do not count as inference.

Public docs confirm separate Agent Builder outbound test calling, requiring agents permission, an agent and a whitelisted number. This account's calling entitlement is unverified. External parties stay simulated; no real calls/messages or personal data are used.

Remaining account unknowns: exact credit conversion, current balance and throttling limits. The dashboard remains authoritative; local request caps do not claim a dollar/credit spending guarantee. Local sanitized results are in ignored `data/`; no raw input audio is saved.

Phase 0 is not complete until real Evon English/Kannada smoke tests and the full three-model voice loop pass.


## Two development tracks

Phase 0 verification stays open for real GGUF English/Kannada output, expected v1 plans and the actual-microphone full loop. The free notebook tests model feasibility before any networking. No paid cloud, BF16 download or tunnel is used. Authenticated notebook access is still required.

Phase 1 product development has begun independently. Mission Engine v1 + MockEvon implements the documented signature fixture with dependency execution, acceptance-gated calendar, alternate parking, and constrained fuel selection. Rejection/no-answer escalate contact/calendar while independent route tasks finish. Tests validate replay, rollback and policy. This is deterministic simulation, not Evon quality evidence. Speech fixtures can now be captured explicitly and replayed offline; earlier recordings are unavailable and slots remain empty.
