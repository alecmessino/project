# Postmortem — Collector outage, 2026-07-06

- **Severity:** SEV-2 (collection halted; no data corruption, no research impact)
- **Duration:** ~8.4 h (2026-07-06 06:32Z stop, detected and recovered 14:52Z)
- **Detected by:** the daily operations review, via checkpoint staleness (not by any automated alert)
- **Status:** Recovered (manual re-arm, run #15). Preventive fix landed in this change.

## Summary

The 24/7 live collector stopped and did not restart itself. The running job (Actions run #14)
was terminated by a **platform-side cancellation**, not an application bug. Because the workflow's
self-re-arm ran only as the tail of the daemon step, the cancellation killed the step before it
could relaunch the successor, and with the cron bootstrap disabled there was no independent
recovery path. Collection was down until a human noticed the stale checkpoint and re-armed it.

## Impact

- No new checkpoints for ~8.4 h. The gap fell mostly in the overnight window (0–2 am ET), so few
  live games were missed; the data cost is low but nonzero.
- **No integrity impact.** The last checkpoint (06:26Z) and all banked panels are clean
  (rows=47,832, 0 malformed / missing / duplicate / future-ts). Nothing collected was lost or
  corrupted; the loss is coverage, not correctness.
- **No research impact.** Paper 1 is frozen; no gate was affected.

## Timeline (UTC)

| Time | Event |
|---|---|
| 03:55 | Run #14 starts (workflow_dispatch), daemon begins polling every ~30 s |
| 06:26 | Last successful health checkpoint committed |
| 06:32:08 | Daemon logs its final healthy poll ("8 quoted") |
| 06:32:24 | `##[error] The runner has received a shutdown signal … The operation was canceled` |
| 06:32:25 | Runner cleans up orphan processes; run #14 ends `conclusion: failure`; **no successor dispatched** |
| 06:32 – 14:52 | No active run; no checkpoints; collection halted |
| 14:50 | Daily review detects an 8.4 h checkpoint gap and no in-progress run |
| 14:52 | Manual `workflow_dispatch` re-arms the collector (run #15, queued) |

## Root cause (five whys)

1. **Why did collection stop?** The collector process (run #14) was terminated and nothing relaunched it.
2. **Why was it terminated?** GitHub sent the runner a shutdown/cancellation signal (infrastructure reclamation of the hosted runner), unrelated to the daemon, which was healthy to the last log line.
3. **Why didn't it restart itself?** The self-re-arm was the final block of the daemon step. A cancellation stops the current step, so the re-arm code never executed.
4. **Why was there no backup restart?** The only other bootstrap, the cron `schedule`, is disabled by repo convention (and would not fire from a feature branch anyway, since Actions cron runs only on the default branch).
5. **Why did no one know for 8 hours?** There is no liveness alarm on checkpoint freshness; the health report's own "running normally" line is written *by* the collector, so once the collector dies the last report is frozen and still reads healthy. Staleness is only visible by comparing the checkpoint timestamp to wall-clock, which the daily review does by hand.

**The single point of failure:** recovery depended entirely on the *previous run finishing its own tail cleanly*. Any terminal state that skips the tail (platform cancellation, hard timeout, runner loss) left the system dead.

## The fix (in this change)

Move the re-arm out of the daemon step into a **dedicated `if: ${{ always() }}` step**. GitHub runs
`always()` steps even when a job is cancelled (the 06:32Z log shows the runner still executing
cleanup after the cancel signal, which is exactly the window an `always()` step uses). So a
cancelled run now still relaunches its successor. `START` is handed to the step via `$GITHUB_ENV`;
the `≥60 min` guard is retained so a fast crash still cannot storm dispatches; the `ttt-live`
concurrency group collapses any double-dispatch to a single runner.

This directly eliminates the failure mode observed today: recovery no longer requires the daemon
step to finish normally.

## Residual risk and follow-ups

- **Hard runner loss** (the VM disappears with no cleanup window) would still skip even an
  `always()` step. Today's incident was a *cancellation with cleanup*, which the fix covers, but a
  total VM loss is not covered by any in-run mechanism.
- A fully **out-of-band watchdog** (a scheduled or `workflow_run`-triggered rescue that relaunches
  when no run is active) is the complete answer, but Actions `schedule`/`workflow_run` fire only
  from the **default branch**. Standing up that watchdog therefore requires placing it on the
  default branch, which is outside this feature branch's remit. **Decision for the owner:** either
  (a) accept the `always()` re-arm as sufficient for the common case, or (b) authorize a small
  rescue workflow on the default branch. Recommended: (a) now, revisit (b) if a hard-loss outage
  ever recurs.
- **Detection gap:** consider a cheap liveness signal (for example, the daily review flags any
  checkpoint older than ~45 min as an incident, which it now does by default). No new always-on
  alerting is proposed; the daily review is the monitor.
