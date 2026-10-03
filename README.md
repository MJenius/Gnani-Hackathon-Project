# DriveOS

You drive. It handles everything around the drive.

Foundation: Next.js mission console, FastAPI, MockEvon planner and bounded dependency runner, policy validation, synthetic contact notification, durable SQLite mission/audit events and idempotency, and an evaluation harness. Real Prisma v2.5 transcription and Timbre v2.5 synthesis are connected. External contact actions remain simulated. Evon inference is unverified. The original BF16 checkpoint is impractical on this laptop; a free Kaggle/Colab llama.cpp experiment is prepared using a community GGUF conversion. No claim of original-checkpoint evaluation is made.

## Modes and secrets

- **Demo Simulation:** browser recognition/synthesis, MockEvon, synthetic negotiation/calendar/parking/fuel tools and bounded replanning. No paid model calls.
- **Gnani speech test:** microphone WAV → Prisma → MockEvon fixture planner → synthetic tool → Timbre. This is not an Evon-powered mission.
- **Gnani Live:** Prisma → EvonClient → policy → synthetic tool → Timbre. Disabled until an Evon deployment is configured; never silently substitutes the demo planner.

The root `.env` loads on the backend only. It holds `GNANI_API_KEY` and `HF_TOKEN`; never put credentials in frontend variables. Git excludes all environment files except `.env.example`. Docker excludes secrets from the build context and injects local `.env` at runtime. Restart the API after changing credentials. The API usage ledger stores metadata only. Mission records and voice retry caches retain transcripts locally under ignored `data/`; use synthetic requests only.

## Run locally

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.api.main:app --reload
```

In another terminal:

```powershell
cd app/web
npm install
npm run dev
```

Open http://localhost:3000. Run the default meeting mission, or use “Tell Ananya I am 25 minutes late.” Test the simulated reply, full-garage and detour controls. Calendar changes only after acceptance; fuel is omitted when it exceeds the remaining route budget. In Gnani speech test mode, Start voice mission records up to 15 seconds; Stop and run mission sends mono WAV through the backend. Capture requires microphone permission and localhost/HTTPS. The result has a playable Timbre confirmation. Kannada/Hindi transcription is available, but MockEvon handles only documented fixture requests. Full multilingual planning requires Evon.

## Verify

```powershell
python -m unittest discover -s tests -v
python -m app.evaluation.runners.evaluate
cd app/web
npm run build
```

Paid verification is opt-in:

```powershell
python -m app.evaluation.runners.evon_access
python -m app.evaluation.runners.gnani_smoke --speech --case english
python -m app.evaluation.runners.gnani_smoke --loop
python -m app.evaluation.runners.gnani_smoke --evon
```

The access check fetches metadata and HEADs one weight shard, without downloading it. `--speech` without `--case` spends up to ten speech calls and stops on failure. `--loop` uses three paid requests for a synthetic real-speech/tool loop and spaces fixture/response synthesis by ten seconds to avoid observed burst throttling. `--evon` reports blocked when no deployment exists. Offline tests mock providers and spend no credits. Results and usage metadata go to ignored `data/`.

`docker compose up --build api` runs the API with durable local storage. PostgreSQL is optional scaffolding (`--profile postgres`), not yet wired to persistence. This is a local unauthenticated demo. See [budget strategy](docs/api-budget.md), [Evon deployment](docs/evon-development.md), and [Phase 0 status](docs/phase-0-status.md).

Specifications: [product context](docs/product-context.md), [architecture](docs/architecture.md), [UX](docs/ux-spec.md), [mission engine](docs/mission-engine.md), [demo scenarios](docs/demo-scenarios.md), [evaluation](docs/evaluation-plan.md), [backlog](docs/backlog.md), [Gnani verification gates](docs/gnani-integration.md).

Phase 0 verification remains open: real GGUF English/Kannada and expected-plan checks, then the actual microphone → Prisma → Evon → policy → tool → Timbre loop. Product development proceeds independently: Mission Engine v1 already runs the signature mission with MockEvon. `EVON_MODE=mock` is the default; `EVON_MODE=remote` enables separately configured real testing. Free GPU evaluation follows gates A–D before HTTP exposure (Gate E); tunnel code is deliberately absent. See [frozen v1 contract](docs/evon-contract.md), [free notebook](notebooks/evon_free_gpu.ipynb) and [speech fixture slots](test_audio/README.md).
