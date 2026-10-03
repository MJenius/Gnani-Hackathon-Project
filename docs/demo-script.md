# DriveOS: 60-second signature demo

Rehearse while stationary. Configure backend Prisma/Timbre credentials and verify credits/local allowance first. A fresh microphone mission needs at least three requests (STT, start TTS, final TTS). Current allowance is insufficient; do not record a video that presents text rehearsal as live Prisma. Autoplay may require pressing play.

| Time | Screen / action | Spoken narration |
|---|---|---|
| 0–5 s | Product headline, clean console | “You're driving, and the plans around you change. DriveOS keeps one mission moving.” |
| 5–16 s | Click **Start Gnani voice mission**, speak, then stop | “I'm running late for my meeting. Tell Ananya, ask if 4:30 works, find parking near her office, and get fuel if it doesn't add more than five minutes.” |
| 16–24 s | Actual Prisma transcript and persisted task graph | “One goal becomes an accountable mission.” |
| 24–32 s | Synthetic call stages; acceptance and calendar commit | “These external services are simulated. Their results drive the engine.” |
| 32–39 s | Garage candidate becomes unavailable; visible replan explanation | “The garage fills after selection. The mission recovers.” |
| 39–48 s | East lot, fuel checked against shared five-minute budget, same ID | “Completed work stays completed. Only affected work changes.” |
| 48–55 s | ETA 4:30, completed mission, final Timbre playback | Let the actual Timbre summary speak; avoid talking over it. |
| 55–60 s | Open Mission Record | “Prisma hears. DriveOS executes. Timbre speaks. Every action has a record.” |

This is a target edit, not a measured provider latency guarantee. Allow provider timing slack; cut pauses, never replace the actual transcript or world transition. The browser engine takes roughly 13 seconds after creation; provider/network timing varies. If capture or synthesis exceeds the slot, shorten the introduction rather than misrepresenting the result.

## Deterministic rehearsal

Click **Reset demo**, then **Run changing-world demo**. This is one-click text rehearsal with browser speech fallback, not Prisma/Timbre validation. The backend starts with an available garage and genuinely changes it after selection. Keep the mission ID, replan explanation and shared-budget chips visible. Open **Mission Record** and download JSON after completion.

## Thirty-second engineering follow-up

Choose **Judge mode → Fuel service fails → Run scenario from clean world**. Show calendar/parking completed, fuel failed and honest escalation. Open replay protection, restore the synthetic fuel service and show completion without repeated calls/calendar actions. On a paused or completed text mission, submit the same request and stale commands; show preserved state verdicts.

Secondary product boundary demo: **Personal example** asks for Mom's medicine and pharmacy stock. DriveOS escalates because the frozen contract has no pharmacy tool. Do not present this as implemented fulfillment.

For Kannada or Hinglish, open **Voice settings**, select the language, expand **What to say** and use the displayed fixture. Film each as a separate provider run only after it actually completes; offline fixture support does not establish live speech accuracy.
