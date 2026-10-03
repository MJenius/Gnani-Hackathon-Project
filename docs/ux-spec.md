# Voice-first mission console

Dark, high-contrast canvas; lime accent; large mission heading; timeline and activity feed, rather than chat bubbles. Show microphone state, transcript, task status and short outcome. All controls have labels, keyboard focus and a responsive layout. Status is conveyed with text as well as color.

The primary object is a persistent v2 mission with goal, task history, current action, synthetic call state, route/ETA, constraint controls, replans and exact confirmation. One control runs the changing-world demo. Separate labeled Gnani voice controls select planner/language, record up to 15 seconds, submit WAV to Prisma and play Timbre. Live Evon is visibly unavailable without endpoint configuration. Text entry remains accessible simulation input. Speech failures preserve mission state; replay uses cached audio after successful synthesis.

CallPilot displays simulated dialing, ringing, connected, request communicated, structured response, acceptance/rejection/counter-offer or bounded no-answer. Browser voice correction supports the existing narrow commands; streaming interruption, real telephony and noisy-car speech quality remain outside verified scope.
