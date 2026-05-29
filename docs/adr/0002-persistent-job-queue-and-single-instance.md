# Persistent job queue and single-instance lock

LexiFlow persists the LLM job queue to disk so pending and failed jobs survive crashes and clean shutdowns. A job that was **running** when the app exited is treated as incomplete: on next launch it returns to **pending** and is picked up automatically. Individual job failures are isolated (error surfaced, app keeps running); the user can retry failed jobs later. Only one app instance may run at a time to avoid sqlite and markdown file locking conflicts.

**Considered:** in-memory queue only (lost on exit); allowing multiple instances with shared data (risky on desktop filesystems).

**Consequences:** core owns queue persistence and state machine; UI shows queue/history and retry actions; startup must acquire single-instance lock before opening databases.

**Single-instance mechanism:** Qt `QLocalServer` / `QLocalSocket` (not filesystem file locks). Second process sends focus message to primary or shows Open existing / Close dialog.
