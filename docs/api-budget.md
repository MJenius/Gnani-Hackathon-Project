# API budget and data handling

The [programme](https://www.gnani.ai/internship) grants 5,000 credits per registration. The dashboard is the authority for account balance, rates and unit-to-credit conversion. Public API docs do not establish this account's remaining balance or exact rates; credit-cost estimates remain unknown.

Proposed reserves: DEV 1,000 credits; EVAL 500; DEMO 1,500; FINAL recording/rehearsal 2,000. These are planning allocations, not enforced provider balances. Separate Evon GPU hosting may have separate costs.

Implemented: SQLite ledger atomically reserves calls before network access. `DRIVEOS_API_STAGE=dev|eval|demo|final` selects a bucket; `DRIVEOS_API_MAX_REQUESTS` defaults to 40 attempts per stage. Failures count, restarts do not reset counters, and capped requests fail before network access. Check dashboard consumption before increasing a cap or changing stage. Request counts cannot guarantee a 5,000-credit spend ceiling while conversion rates are unknown.

Logged: UTC timestamp, stage, model, operation, latency, HTTP success/failure, status, input audio seconds/sample rate, text characters or planner character/token bounds. Never keys, auth headers, raw provider responses, prompts, transcripts or audio in the usage ledger. Mission/voice retry storage separately retains transcripts under ignored `data/`.

No paid startup/background calls or automatic retries. Smoke tests are opt-in synthetic fixtures. HTTP 429 stops the matrix. V2 voice replay caches the transcript and successful acknowledgement/completion WAVs; successful playback retry costs no new call. Legacy voice output synthesis still uses one call per replay. `/health` exposes local maximum/used/remaining counts without credentials or provider calls. The mission console disables new recording below three remaining calls (four with remote Evon) and keeps failed recordings available for manual retry. Counts are not provider-credit balances.

Browser recordings remain in memory for explicit retry until the page is closed/reloaded. Normal recordings are not saved on the backend; transcripts and output WAVs are cached in ignored data/. The explicit real v2 verification runner retains synthetic input WAVs and transcript evidence there too. Both local secrets stay excluded from Git/Docker.
