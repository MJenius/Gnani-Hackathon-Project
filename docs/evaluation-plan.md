# Mission evaluation

Run `python -m unittest discover -s tests -v` and `python -m app.evaluation.runners.evaluate`.

Checks cover API → persistent graph → policy → synthetic tools → durable state: bounded input/tool validation, authorization, exact/stale/declined confirmations, replay/concurrent revisions, unsupported actions, call stages, bounded no-answer, same-ID replanning and restart recovery. Frozen-schema equality is tested.

`voice_missions.json` includes English, Kannada, Hinglish, spoken/digit times, punctuation/transcription variations and changed name/time/budget negative controls. Observed real Prisma English/Kannada spellings are included. Personal/work/delivery are unsupported-context fixtures: passing means safe escalation, not pharmacy/inventory/shipment success. No noisy-car benchmark is claimed.

`evaluate` writes ignored `data/evaluation-results.json`: supported mission completion, expected outcome, schema/dependency/intent validity, replanning, duplicate/unsafe-action rates, confirmation compliance, bounded no-answer, ground truth and interventions. Completion excludes unsupported fixtures and rejected/no-answer negotiations. Ground truth includes missions with verified route selections. Latency is local text-to-persisted-result time, excluding voice and browser pacing. These finite fixture rates are not production guarantees.

`voice_demo --real --case english|kannada` performs real synthetic-input Prisma → MockEvon → changing-world v2 → Timbre. It saves ignored evidence/audio; `--reuse-audio` avoids input synthesis. Latency includes a labeled ten-second TTS cooldown. No automatic provider retries or Evon quality claim. Actual microphone/noisy-car/listening quality needs human verification.

For an API process restart: run `python -m app.evaluation.runners.restart_check capture`, restart the backend, then run the runner with `verify`. It checks exact state and same-ID completion. `secret_scan` checks source, Git index and frontend bundles for configured secrets/patterns without printing matches. Offline tests require no credits.
