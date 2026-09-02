<!-- engram:begin reflection-fix rk-monitor-dod -->
## Definition of Done — terminal UI changes

A UI or key-handling change is not done until a functional interaction
test has run — for key handling, drive the app with real key input (for
example `scripts/tui-smoke.sh`) — in addition to unit tests. If the
functional check cannot run, say the behavior is unverified and do not
claim the fix is complete.
<!-- engram:end reflection-fix rk-monitor-dod -->
