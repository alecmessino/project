# Stopping rules

Objective gates, not "wait until it feels like enough." Each rule states the criteria that must
*all* hold before a given analysis is permitted. Until then, the daemon **collects; it does not
conclude.** `../microstructure_probe.py` prints the live status of these gates every run.

## SR-1 · Cross-book leadership

Leadership / lead-lag analysis is blocked until **all** of:

- **≥ 2,000 simultaneous live quote pairs** (both books live within the same tight window),
- **≥ 100 independent games** with live overlap,
- **median synchronization lag < 15 s** between the paired quotes,
- **≥ 3 sportsbooks** quoting live concurrently.

*Why these numbers:* leadership estimation is extremely data-hungry and dominated by noise below
this scale (SR born from the one-night sample where every estimate was an artifact — see S-10, S-11
and the July 3–4 entries in the decisions log). The synchronization bound exists because
non-contemporaneous quotes measure nothing (S-11); tonight's median lag was ~3,663 s.

## SR-2 · Distribution dynamics

Higher-moment (variance / skew / tail) repricing analysis is permitted once:

- **≥ 50 games** with a continuous implied-PMF trajectory through ≥ 6 innings, and
- event timestamps joinable to the PMF stream (game-state panel aligned within < 30 s).

This gate is looser than SR-1 because the implied-distribution panel is single-source (Pinnacle)
and needs no cross-book synchronization — the scarce resource is *within-game continuity*, not
overlap.

## SR-3 · Real-line encompassing robustness (Paper 1 appendix)

The de-vigged-implied-mean robustness re-run is permitted once alternate-total strips are collected
for **≥ 30 games**, enabling a distribution-free implied mean. Until then the parametric version
(single line + de-vigged P(over) under an assumed run-total law) is the only available form and
must be labelled as assumption-dependent.

## Discipline

A stopping rule may be **loosened only with a stated reason** recorded in the decisions log, and
never mid-analysis to rescue a result. If a gate is cleared and the analysis still finds nothing,
that null is itself reportable — the gate guarantees it was adequately powered.
