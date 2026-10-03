# Gnani verification gates

Checked 2026-10-03: https://github.com/Gnani-AI-Mintlify/livekit-plugins-gnani links https://docs.gnani.ai and documents the gnani-vachana SDK, Prisma STT and Timbre TTS. Use the official SDK/docs as integration authority. No SDK calls are currently implemented and no credentials were supplied.

Verify before implementation: account access and pricing; exact REST upload schema; accepted browser recording formats versus raw PCM; language/code-switching behavior; streaming authentication; partial/final transcripts; Timbre response formats and voices; cancellation, quotas and error contracts.

Evon remains unverified: obtain the hackathon's current endpoint, authentication, model identifier, structured tool-call schema, context limits and latency requirements. Do not assume an OpenAI-compatible endpoint or invent one.

GNANI_API_KEY must remain server-side. Browser speech recognition/synthesis is a development fallback and may use browser-provider services. Real Gnani voice and Evon planning remain a completion gate for the full product.
