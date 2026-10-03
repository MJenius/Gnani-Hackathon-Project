# Reusable speech fixtures

Slots: english/, kannada/, hinglish/, noisy/. Earlier real Prisma/Timbre test audio was not retained, so these slots currently have no WAVs. No credits were used to fill them. No noisy-car or Hinglish accuracy is claimed.

When another paid synthetic verification is explicitly wanted, add `--save-fixtures` to `python -m app.evaluation.runners.gnani_smoke --speech --case english`. That run saves the WAV, historical Prisma transcript and hashes in the selected group. Paid tests remain opt-in.

Replay using `python -m app.evaluation.runners.gnani_smoke --speech --case english --reuse-fixtures`. It verifies the cached prompt/audio provenance and WAV format without calling any provider. Missing fixtures fail without a paid retry. Historical transcription is not a new STT test. Offline Mission Engine tests use known transcript/plan fixtures and need no audio or network.

Noise testing needs a separately labeled synthetic noisy WAV and fresh expected transcript. Do not reuse clean-audio transcription as noisy accuracy evidence. Commit only documentation; audio and cached transcripts remain local and are excluded from Git/Docker.
