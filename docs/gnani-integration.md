# Verified Gnani integration contracts

Verified 2026-10-03 against the official [documentation index](https://docs.gnani.ai/llms.txt), [Prisma REST](https://docs.gnani.ai/api/STT/speech-to-text), [Prisma realtime](https://docs.gnani.ai/api/STT/stt-websocket), [Timbre REST](https://docs.gnani.ai/api/TTS/tts-inference), [voice catalog](https://docs.gnani.ai/api/TTS/available-voices), and [Evon model card](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B).

Real Prisma/Timbre have passed synthetic English/Kannada and mixed-language tests. On 2026-10-03, English and Kannada signature audio also completed the persistent v2 changing-world flow with MockEvon and real Timbre start/completion WAVs. Keys remain backend-only and excluded from Git/Docker. A later English human microphone → real Prisma → persistent v2/replan → real Timbre run was human-verified on 2026-10-04, with audible playback confirmed. Kannada/Hinglish human capture, pronunciation benchmarks, noisy-car quality and Evon inference remain unverified.

## Prisma v2.5

Base https://api.vachana.ai; header X-API-Key-ID. POST /stt/v3 uses multipart audio_file, language_code and optional format=transcribe for number/date normalization. Documented WAV/MP3/OGG/FLAC/AAC/M4A inputs up to 60 seconds. Our verified path accepts only mono 16-bit WAV, up to 30 seconds and 4 MB; browser capture stops at 15 seconds. No assumption that browser WebM is accepted.

Realtime wss://api.vachana.ai/stt/v3/stream uses upgrade headers x-api-key-id, lang_code, x-sample-rate and x-format. Current docs list 8, 16, 44.1 and 48 kHz. Send signed little-endian mono PCM, not WAV/container bytes. Transcript JSON has type=transcript, text, segment ID and latency; VAD determines boundaries. Realtime is a documented upgrade path, not implemented yet. REST capture proves the first loop without a streaming framework.

## Bounded mission interpretation

Prisma output now feeds slot extraction rather than whole-sentence signature matching. Required values are Ananya, 16:30, parking near the office, fuel requested, and at most five added minutes. Each instruction clause must appear exactly once; clauses may be reordered. Explicit aliases cover 4:30 / 04:30 / four thirty, five / 5 minutes, Kannada spoken numbers, common notification/parking phrases and Hinglish poochho / poocho / pucho, dhundo / dhundho / dhoondo. Punctuation and bounded fillers (um, uh, erm, please, okay, ok) are accepted. The grammar is in app/agent/planner/slots.py; it uses no fuzzy matching or model inference.

Every remaining word must be a supported connector. Unknown names, times, budgets, missing or repeated slots, negated actions and extra instructions return no plan tasks and escalate. The allowed negative phrase inside the fuel clause expresses the five-minute upper bound; it does not negate fuel. Parking without an explicit office destination now escalates. Existing smaller negotiation/parking demos keep their separate finite scope. Frozen schema, policy and execution are unchanged.

Offline checks cover 72 clause orders across three languages, rejected mutations and persistent Hinglish completion. These checks do not verify human Kannada/Hinglish capture or Prisma accuracy; both language tests still require the human microphone and listening path.

## Timbre v2.5

POST /api/v1/tts/inference with the same speech auth header. JSON text, voice, model=timbre-v2.5, language, speed and audio_config. App requests binary mono 16 kHz 16-bit WAV. Voices: Kaveri English, Saanvi Kannada, Nalini Hindi, Poorvi Hinglish; auto is documented for mixed content. Verified quick-start has no separate beta endpoint. SSE /api/v1/tts/sse and WebSocket /api/v1/tts are future latency improvements.

Observed live responses use an unfinished streaming WAV frame count of 2,147,483,647. The adapter repairs that known header from actual PCM bytes, then validates it. Inbound audio validation stays strict. Formatting guidance recommends spoken words for times/numbers; synthetic fixture tests follow it. Spoken-feedback pronunciation still needs listening QA.

## Errors and latency

Docs: 401 authentication, 400 invalid request, 429 throttling, 500/503 provider error. Real Timbre testing encountered 429; there are no automatic paid retries. We expose only operation/status, never raw provider error bodies. Metadata ledger records request latency, HTTP outcome and input units. HTTP success is not proof of pronunciation or transcription quality. Synthetic round trips do not establish noisy-car performance. For the production voice loop, use server-side authenticated streaming and interruption/cancellation after this basic proof succeeds.

## Evon

The challenge describes requested open weights, separate from speech APIs. HF token, metadata/config and weight shard HEAD access passed for gnani/gnani-evon-v3.3-30B-A3B. No weights were downloaded. HF lists no hosted inference provider. A weight-access token is not an inference endpoint.

DriveOS owns EvonClient, which validates a strict Plan before deterministic policy. Its completion callback can use any separately verified inference mechanism; default transport follows official OpenAI-compatible vLLM/SGLang examples. It uses only EVON_API_KEY for that deployment, never the speech key or HF token. Model-card tool-call support is documented, not live-tested. Official gated weights are accessible, but local BF16 inference is infeasible. Zero-cost GPU verification is prepared through the community GGUF conversion in Kaggle/Colab; actual loading and English/Kannada planning remain unverified. See evon-free-notebook.md and evon-development.md. No fallback planner impersonates Evon in live mode.

## Telephony decision

The separate [Agent Builder trigger-call API](https://docs.gnani.ai/Platform/Trigger_Call) documents POST https://api.inya.ai/platform/v1/agents/{botId}/trigger_call?environment=development, x-api-key with agents permission, an agent ID and a whitelisted number. Speech credentials do not establish that entitlement. No real calls were made. Phase 1 uses synthetic external parties until separate provisioning is verified. The [LLM config endpoint](https://docs.gnani.ai/Platform/Get_LLM_Models) configures Agent Builder; it is not an Evon completion API.

## Budget and privacy

Secrets load only in the backend from ignored .env. Public documentation does not establish current account credit balance or precise rates/throttling limits. Local per-stage request caps and metadata logging are implemented; dashboard verification is required before broad usage. Synthetic audio stays in memory; smoke results retain metadata only. Mission state and replay caches retain transcripts locally under ignored data/. See api-budget.md and phase-0-status.md.
