# Demo scenarios

## Working first slice
Say “Tell Ananya I am 25 minutes late.” The console builds one mission, records a synthetic delay notification and speaks the result. Repeat with the same request key: no duplicate notification. An unsupported mission escalates.

## Implemented signature simulation
“I'm running 25 minutes late. Tell Ananya, ask if 4:30 works, find parking near her office, and get fuel if it doesn't add more than five minutes.” Contact accepts or rejects; calendar updates only after agreement. Parking becomes full: verify another lot, recalculate ETA and report the alternative. Fuel over the threshold is omitted. Implemented for the documented fixture with MockEvon. Contact replies and garage availability are explicit console controls. Route detours are synthetic, not live traffic. No reservations or fuel purchases occur.

## Shared engine contexts
Personal: medicine stock and Mom's ETA. Work: customer ETA and replacement part stock. Delivery: receiver contact and shipment slot. Exact request fixtures now use the same v2 engine but safely escalate: frozen v1 only permits Ananya/office/calendar/parking/fuel. Executing these scenarios requires a separately reviewed contract extension; no unrelated Ananya plan is substituted.

No real personal data, enterprise integration or production telephony is required. All simulated results must be labeled. Genuine Gnani voice is required before claiming the hackathon demo is complete.
