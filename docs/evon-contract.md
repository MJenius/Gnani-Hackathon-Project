# Frozen DriveOS / Evon contract v1

The planner proposes a graph; deterministic DriveOS policy and tools own execution. A provider failure, malformed output, unavailable inference or replacement must not alter the engine contract. MockEvon is the default offline fixture provider, not evidence of model inference.

Input carries version, mission, context, available_tools and constraints. Context facts are server-owned synthetic fixtures: contact Ananya, demo-meeting, office destination, a 25-minute ETA delay and normalized 16:30 proposal. When the signature request omits a numeric delay, the planner uses that explicit context fact. It never guesses a live ETA.

```json
{
  "version": "1",
  "mission": "I'm 20 minutes late. Tell Ananya and ask if 4:30 works.",
  "context": {
    "contact": "Ananya",
    "meeting_id": "demo-meeting",
    "destination": "office",
    "eta_delay_minutes": 25,
    "meeting_time": "16:00",
    "requested_new_time": "16:30",
    "source": "synthetic demo fixtures"
  },
  "available_tools": [
    "contact.negotiate",
    "calendar.reschedule",
    "parking.select",
    "fuel.select"
  ],
  "constraints": [
    "No real calls or purchases",
    "Calendar change only after explicit acceptance",
    "At most five total added route minutes",
    "Unknown or ambiguous requests escalate"
  ]
}
```

Output:

```json
{
  "version": "1",
  "goal": "Handle the synthetic mission",
  "tasks": [
    {
      "id": "t1",
      "action": "contact.negotiate",
      "arguments": {
        "contact": "Ananya",
        "delay_minutes": 20,
        "proposed_time": "16:30"
      },
      "depends_on": []
    },
    {
      "id": "t2",
      "action": "calendar.reschedule",
      "arguments": {
        "meeting_id": "demo-meeting",
        "proposed_time": "16:30"
      },
      "depends_on": [
        "t1"
      ]
    }
  ],
  "needs_confirmation": false
}
```

Canonical schema: `app/agent/planner/contract.py` and generated `docs/evon-plan-v1.schema.json`. Unknown fields/tools, invalid arguments, duplicate IDs/actions, unknown dependencies and cycles fail validation. Calendar requires a negotiation dependency; runtime additionally requires an explicit accepted response. Fuel depends on parking when both are requested, allowing the tool to enforce the remaining **total** detour limit. Current arguments are deliberately confined to synthetic fixtures; broader tools need a new reviewed contract version.

Tools: contact.negotiate (delay + 16:30 proposal, one attempt), calendar.reschedule (only after acceptance), parking.select (candidates + detour + verified selection), fuel.select (candidates + remaining detour + selection). These compound informational tools cover discovery/estimation/selection without exposing invented primitive APIs. Fuel selection never buys fuel; purchases remain class C and unsupported by this contract.

EvonClient.plan_mission(input) accepts this input and returns a validated MissionPlan. MockEvon.plan_mission(input) provides documented exact fixture plans. Completion remains injectable. No inference mechanism leaks into the graph runner. Existing Plan/Task notification contract remains the initial voice slice for compatibility. Real v1 remote execution is not enabled until known-plan inference and transport have been verified; live mode never silently substitutes MockEvon.

`EVON_MODE=mock` is default. Set remote only for separately configured/verified real testing. No endpoint is fabricated. Semantic fixture expectations live in app/evaluation/fixtures/mission_plans.json; these are checked against model output after English/Kannada basics pass. Accepting valid JSON alone is insufficient.
