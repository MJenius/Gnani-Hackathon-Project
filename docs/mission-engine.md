# Mission engine

States: NEW, UNDERSTANDING, PLANNING, EXECUTING, WAITING_ON_EXTERNAL, REPLANNING, AWAITING_CONFIRMATION, COMPLETED, FAILED, ESCALATED. The initial slice uses PLANNING → EXECUTING → COMPLETED, or ESCALATED for unsupported intent; failure rolls back execution.

Tasks have IDs, descriptions, status, dependencies, priority, tool, inputs/output, confirmation requirement, retry policy and timestamps. The initial graph has one node. The v1 signature runner validates dependencies/cycles and executes ready tasks. A failed negotiation blocks calendar only; independent routing continues. Parking checks synthetic availability and selects the alternate lot on full-garage input, emitting REPLANNING. Fuel waits for parking and fits within the remaining shared route budget. One contact attempt, two parking candidates, two fuel candidates: no unbounded retries.

Policy: A informational; B bounded reversible action only within explicit mandate; C sensitive action only with explicit confirmation bound to the concrete action. Unknown tools fail closed. The first allowlisted tool is contact.notify_delay with a synthetic fixed contact Ananya and 1–120 minutes. Its class is B. The user must explicitly request notification and authorize the simulation.

Idempotency keys bind to the full normalized request. A replay returns the stored mission. Reusing a key for another request is rejected. Mission result, simulated mutation and audit events commit together. Audit records contain action state, not model reasoning. The current local storage is demo-only; authentication and retention policy precede deployment.

The v1 allowlist adds contact.negotiate/calendar.reschedule (B), parking.select/fuel.select (A). Fuel selection means a route suggestion, never payment. Complete graphs pass authorization before mutation. Task effects and mission events share the same transaction; provider failure rolls back. See evon-contract.md for frozen provider input/output.
