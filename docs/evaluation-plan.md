# Mission evaluation

Run `python -m unittest discover -s tests -v` and `python -m app.evaluation.runners.evaluate`.

Initial checks: supported intent and minutes extraction; bounded input rejection; tool allowlist; missing authorization; sensitive confirmation; duplicate prevention; request-key collision; persistence; unsupported mission escalation. Tests exercise actual API → graph → tool → durable state.

Next datasets: English, Hinglish, Kannada, noisy recorded audio, names/numbers/addresses, accepted/rejected time negotiations, unavailable parking, no-answer calls, fuel limits and interruptions. Human-label expected graph, tool target and outcome; do not score only fluent responses.

Metrics: mission completion, replanning accuracy, unsafe action rate, confirmation compliance, duplicate execution rate, verified ground truth, median resolution latency and driver interventions. Current harness reports deterministic text-slice completion only; it does not measure real speech or Gnani latency.
