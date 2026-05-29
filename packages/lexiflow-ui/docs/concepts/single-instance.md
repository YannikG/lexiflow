# Single instance

## What this is

LexiFlow allows only one UI instance per user session (**Single instance**). A second launch offers to open the existing window or close, preventing sqlite and markdown file contention.

## Mechanism

- Qt `QLocalServer` / `QLocalSocket` (not filesystem locks) per ADR-0002
- Server name: `lexiflow-{username}`
- Primary instance listens; secondary probes connect, shows dialog, optionally sends an activate message
- Primary calls `MainWindow.request_activation()` on activate (`raise_`, `activateWindow`, `QApplication.alert` for dock bounce on macOS)

## Stale recovery

If `listen()` fails after a crash, `QLocalServer.removeServer()` clears a stale socket name once, then listen retries.

## Package boundary

**lexiflow-ui** owns `SingleInstanceGuard`. **lexiflow-core** databases open only after the primary instance acquires the lock (via `app.run` orchestration).

## Phase 05 scope

Acquire lock, secondary dialog (Open existing / Close), activation message to raise primary window. No change to queue or library persistence.
