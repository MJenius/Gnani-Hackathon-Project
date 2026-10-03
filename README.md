# DriveOS

You drive. It handles everything around the drive.

Foundation: Next.js mission console, FastAPI, deterministic single-task planner, policy validation, synthetic contact notification, durable SQLite mission/audit events and idempotency, browser voice input/output, evaluation harness. No real messages or calls are sent. Gnani integration is not yet connected.

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

Open http://localhost:3000. Use “Tell Ananya I am 25 minutes late.” Microphone capture needs permission and a supporting browser. Review the transcript and run the demo; a spoken confirmation follows if speech synthesis is available. Language selection controls browser recognition, but the narrow planner currently accepts only the English example.

## Verify

```powershell
python -m unittest discover -s tests -v
python -m app.evaluation.runners.evaluate
cd app/web
npm run build
```

`docker compose up --build api` runs the API with durable local storage. PostgreSQL is optional scaffolding (`--profile postgres`), not yet the persistence backend. The API is a local unauthenticated demo; do not expose it publicly.

Specifications: [product context](docs/product-context.md), [architecture](docs/architecture.md), [UX](docs/ux-spec.md), [mission engine](docs/mission-engine.md), [demo scenarios](docs/demo-scenarios.md), [evaluation](docs/evaluation-plan.md), [backlog](docs/backlog.md), [Gnani verification gates](docs/gnani-integration.md).

The signature multi-step mission, simulated calls/replanning, verified Prisma/Evon/Timbre adapters and production authorization are the next phases. The current slice is a working development foundation, not the finished hackathon demo.
