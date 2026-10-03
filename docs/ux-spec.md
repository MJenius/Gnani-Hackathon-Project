# Voice-first mission console

Dark, high-contrast canvas; lime accent; large mission heading; timeline and activity feed, rather than chat bubbles. Show microphone state, transcript, task status and short outcome. All controls have labels, keyboard focus and a responsive layout. Status is conveyed with text as well as color.

Start with a single synthetic delay notification. Mode labels distinguish browser-voice simulation, real Gnani speech with the demo planner, and full live mode with Evon. English/Hindi/Kannada locale selection is available. Browser speech is only the simulation fallback; real capture sends bounded WAV through the backend to Prisma and plays Timbre WAV. Full live mode is disabled until Evon is configured. Text entry remains the accessible simulation fallback. If output speech fails after a committed action, show the completed mission and a separate playback error.

Later: compact route/ETA, active call indicator, interruption/correction, hands-free confirmations and concise replanning announcements. Driver interactions must not require paragraphs of reading.
