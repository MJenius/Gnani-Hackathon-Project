# DriveOS — Codex Master Context

## 1. Product

**Name:** DriveOS

**Tagline:** You drive. It handles everything around the drive.

DriveOS is a voice-first AI operations layer for people who are driving or otherwise physically occupied. The user gives the agent a multi-step goal in natural speech. DriveOS understands the mission, creates a plan, talks to people/businesses when needed, uses tools and external systems, replans when reality changes, and tells the driver only what matters.

This is NOT:
- a generic voice chatbot
- a fleet-management dashboard
- a navigation app
- a voice wrapper around ChatGPT
- a trucking-only product
- a collection of disconnected voice commands

The core product abstraction is a **Mission**.

Example:
> “I’m running late for my 4 PM meeting. Tell Ananya, see if 4:30 works, find parking near her office, and I need fuel before I get there.”

DriveOS should decompose this into a mission graph, execute the necessary actions, react to changing information, and complete the objective with minimal driver interaction.

---

## 2. Why voice is essential

DriveOS must pass this test:

> If the same task could be solved almost as well by typing into a normal chatbot, it is probably not a good DriveOS task.

Voice is essential because the user is driving / operating equipment / physically occupied. The agent must:
- work without requiring the user to touch a screen
- handle natural, fragmented, code-mixed speech
- support interruption and correction
- call real people/businesses when current information is unavailable
- perform multi-step actions across tools
- replan when the outside world changes

The product value is not “talking to AI.” The value is **delegating real-world work while the user stays focused on driving**.

---

## 3. Primary user and contexts

Primary user:
- someone driving for personal or work purposes

Secondary contexts:
- cab/ride-hailing driver
- delivery driver
- field sales worker
- service technician
- maintenance worker
- small-business owner travelling between jobs

Do NOT let the first version become a logistics product. The same mission engine must work across personal and professional driving.

Three demo contexts should exist:
1. Personal driving
2. Work/field driving
3. Delivery/logistics

All three use the same underlying architecture.

---

## 4. Core product loop

Every mission follows:

1. Understand
2. Create plan
3. Check current state
4. Execute safe actions
5. Talk to people / verify ground truth when needed
6. Replan if something changes
7. Confirm important irreversible actions
8. Finish mission
9. Summarize outcome

Example:

User:
> “I’m 25 minutes late for my meeting. Tell Ananya, move it to 4:30 if she agrees, find parking, and get fuel if it doesn’t add more than 5 minutes.”

Mission graph:
- contact Ananya
- negotiate new time
- update calendar
- find nearby fuel
- estimate detour
- find/verify parking
- update route
- monitor ETA

If parking is full, do not ask the user immediately. Find an alternative, verify availability, recalculate, then report the new plan.

---

## 5. Gnani AI requirements

The product must genuinely use Gnani's models/APIs.

### Prisma
Use for:
- live user speech
- noisy car audio
- Kannada/English and Hinglish/code-switching
- names
- numbers
- addresses
- dates
- phone numbers
- confirmation phrases

The voice layer should make Indian-language speech a first-class experience rather than a demo add-on.

### Evon
Use as:
- mission planner
- task decomposition/replanning engine
- conversational reasoning layer
- ambiguity resolver
- tool-selection proposal layer

Evon should NOT directly own authorization. Tool execution must be governed by deterministic policy.

### Timbre
Use for:
- concise spoken responses
- natural confirmations
- call-agent speech where appropriate
- short driver-safe responses

The voice UI must be designed around low cognitive load.

---

## 6. Product principle: Mission, not command

Bad:
> “Find a parking lot.”

Good:
> “Get me to the meeting on time.”

The second form creates a mission containing:
- route
- ETA
- parking
- communication
- scheduling
- optional fuel stop

DriveOS should optimize the mission, not execute isolated commands.

---

## 7. GroundTruth principle

Do not blindly trust stale search/index data when the answer depends on current human state.

Examples:
- “Is this parking garage actually open?”
- “Does this pharmacy have the medicine?”
- “Can the restaurant seat four right now?”
- “Can the customer still meet me at 4:30?”
- “Is the technician available today?”

When necessary, DriveOS should call the business/person to establish current ground truth.

This is one of the major differentiators from ordinary ChatGPT/search.

---

## 8. CallPilot principle

DriveOS can act as the user's telephone delegate.

It should:
- place calls
- navigate simple IVRs
- explain the user's request
- answer predictable questions from known data
- negotiate within bounded rules
- detect when a sensitive decision requires the user
- summarize the result
- update the mission state

The driver should not need to manually make a sequence of phone calls.

---

## 9. Safety and action policy

Use three action classes.

### Class A — Informational
Examples:
- read ETA
- check weather
- retrieve appointment details

Can run automatically.

### Class B — Reversible / bounded
Examples:
- ask someone whether 4:30 works
- send a delay notification
- search for alternatives
- request a reservation

Can generally run automatically if within explicit policy limits.

### Class C — Sensitive / irreversible
Examples:
- payment
- cancellation
- purchase
- committing to material cost
- changing sensitive account details

Require explicit user confirmation.

Important:
- Evon proposes actions.
- Deterministic policy validates them.
- Sensitive actions require confirmation.
- Every state-changing action is idempotent.
- Maintain an audit log.
- Never silently execute unsafe actions.

Use the existing Mandate-style engineering pattern where useful: authorization, deterministic policy, idempotency, validation, traceability.

---

## 10. Mission state model

Recommended high-level states:

NEW
UNDERSTANDING
PLANNING
EXECUTING
WAITING_ON_EXTERNAL
REPLANNING
AWAITING_CONFIRMATION
COMPLETED
FAILED
ESCALATED

Each task should have:
- id
- description
- status
- dependencies
- priority
- tool
- inputs
- output
- confirmation requirement
- retry policy
- timestamps

Do not rely on free-form text as the source of truth for state.

---

## 11. UI/UX direction

The UI should feel like a premium, calm operations console — not a generic ChatGPT clone.

### Visual direction

- dark, high-contrast interface
- large typography
- subtle map/route visualization
- mission timeline as the central element
- live activity feed
- minimal chrome
- no excessive cards
- no decorative gradients everywhere
- no “chat app” layout as the primary surface
- motion should communicate state, not decoration

Use a restrained dark interface with one bright accent color for active state/action.

### Main screen

Center the UI around:

**MISSION**

Example:

MISSION
Get to Ananya's office by 4:30 PM

- Contact Ananya — DONE
- Meeting rescheduled — DONE
- Parking — VERIFYING
- Fuel — PLANNED
- ETA — 4:26 PM

Below it:
- live route/ETA
- compact task timeline
- active call indicator
- short transcript snippet
- current mission status

### Live activity

Examples:
- Calling Ananya…
- Ananya accepted 4:30
- Checking parking availability…
- Parking confirmed
- ETA recalculated: 4:26 PM

Do not expose hidden chain-of-thought. Show only concise, user-relevant action state.

### Voice interaction

The user should see:
- microphone state
- what DriveOS heard
- current action
- a very short spoken response

The interface should not require reading paragraphs while driving.

---

## 12. Signature demo

Primary demo:

User is driving to a meeting.

> “I’m running 25 minutes late. Tell Ananya, ask if 4:30 works, find parking near her office, and get fuel if it doesn’t add more than five minutes.”

DriveOS:
1. understands the mission
2. calls Ananya
3. reschedules meeting
4. finds parking
5. verifies parking availability
6. plans fuel stop
7. recalculates ETA
8. handles any change without restarting

Potential visual twist:
- parking location is reported full
- DriveOS autonomously finds another
- recalculates ETA
- only then informs the user

This shows true replanning.

---

## 13. Secondary demos

### Personal
> “Pick up my mother’s medicine on the way home. Call the pharmacy first and make sure they have it.”

### Work / field
> “Tell the customer I’m 20 minutes away, check whether the replacement part is ready, and if not find a service centre on the route.”

### Delivery
> “The receiver isn’t answering. Find out if they can still take the shipment today and tell dispatch if the slot changes.”

---

## 14. Demo quality bar

The demo must visibly show:
- real voice interaction
- multilingual / code-mixed speech
- tool use
- phone call or simulated call
- mission state
- replanning
- real state change
- a visible outcome

Avoid demos where the model only talks.

The audience should be able to understand the product in 3 seconds.

---

## 15. Evaluation

Build an evaluation harness around missions, not only LLM responses.

Test:
- intent/mission extraction
- task decomposition
- correct tool selection
- correct call target
- information extraction from calls
- replanning after external changes
- confirmation behavior
- duplicate action prevention
- unsafe-action blocking
- Kannada / Hinglish / English
- noisy speech
- latency
- end-to-end mission completion

Important metrics:
- mission completion rate
- correct replanning rate
- unsafe action rate
- confirmation compliance
- duplicate execution rate
- ground-truth verification success
- median time to resolution
- number of driver interventions required

---

## 16. Initial technical architecture

Preferred stack:
- Next.js / React frontend
- FastAPI backend
- PostgreSQL
- Redis only if useful
- Docker
- Prisma integration
- Timbre integration
- Evon integration
- explicit tool layer
- deterministic policy layer
- structured event log
- automated evaluation harness

Keep the architecture simple. Do not introduce microservices, Kubernetes, Kafka, or multiple agent frameworks unless a real requirement emerges.

---

## 17. Initial repository structure

app/
  web/
  api/
  agent/
    planner/
    state/
    policies/
  speech/
    prisma/
    timbre/
  tools/
    calls/
    calendar/
    maps/
    places/
    trip/
  mission/
    graph/
    execution/
    replanning/
  safety/
    authorization/
    confirmation/
    idempotency/
  evaluation/
    datasets/
    runners/
    metrics/
  ui/
    mission/
    calls/
    route/
    timeline/

tests/
docs/

---

## 18. Product non-goals for first version

Do NOT:
- build fleet management
- build a full navigation application
- build a generic AI assistant
- support dozens of integrations
- build a true production telephony platform
- depend on real enterprise APIs
- require real personal data
- build a giant multi-agent framework
- over-focus on UI before the mission engine works

Use synthetic backends and realistic simulations where necessary.

---

## 19. Demo backend

Create deterministic simulated services:
- calendar
- maps/ETA
- parking business
- fuel station
- contact
- service provider
- dispatcher
- optional business phone endpoint

These simulations should behave like real systems and occasionally change state.

Examples:
- parking lot becomes full
- contact accepts proposed time
- contact rejects proposed time
- fuel detour exceeds threshold
- business doesn't answer
- business provides new availability

The purpose is to demonstrate dynamic planning and recovery.

---

## 20. Development philosophy

Prioritize in this order:

1. Product correctness
2. Mission engine
3. Voice quality
4. Ground-truth/call interactions
5. Safety
6. Replanning
7. Evaluation
8. UI polish
9. Demo polish

Never hide a broken core behind polished UI.

Every major feature should have:
- a normal case
- at least one failure case
- automated test coverage
- clear observability

---

## 21. First build task for Codex

Before writing substantial product code:

1. Inspect the repository.
2. Create a `docs/product-context.md` containing this entire product definition.
3. Create `docs/architecture.md`.
4. Create `docs/ux-spec.md`.
5. Create `docs/mission-engine.md`.
6. Create `docs/demo-scenarios.md`.
7. Create `docs/evaluation-plan.md`.
8. Create a short implementation backlog grouped into phases.
9. Identify unknowns that must be verified against Gnani's current API/docs.
10. Only then scaffold the application.

Do not start by building a generic chat UI.

After the documentation/specification pass, implement a minimal vertical slice:
voice input → mission extraction → one mission graph → one tool → one state update → voice confirmation.

That vertical slice must work end-to-end before broadening the system.
