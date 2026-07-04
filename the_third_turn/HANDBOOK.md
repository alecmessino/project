# The Third Turn — lab handbook

A research program on **forecast validation and information incorporation in live probabilistic
forecasting systems**, with sportsbooks as the observable laboratory. Sports betting is the
application domain; the transferable contribution is a disciplined way to distinguish genuinely
incremental predictive information from artifacts.

This handbook separates the **method** from the **data** from the **history**, so each can evolve
and be cited independently.

```
the_third_turn/
├── protocol/                  THE METHOD (domain-general)
│   ├── protocol.md            the Third Turn Protocol — the escalating validation ladder
│   ├── safeguards.md          the safeguard registry (S-01…), each with its provenance
│   └── stopping_rules.md      objective gates that block an analysis until it is powered
├── benchmark/                 THE DATA
│   ├── README.md              Benchmark Dataset front door
│   ├── dataset/               schema, reference results, baselines
│   ├── examples/              how to report a new signal against the protocol
│   ├── CITATION.cff · CHANGELOG.md
├── decisions/
│   └── RESEARCH_DECISIONS_LOG.md   why every safeguard exists — the causal history
├── paper/                     paper1.md (+ figures, build, section drafts)
├── microstructure_notes.md    live-panel findings, daemon priorities, Paper 2 reframing
├── microstructure_probe.py    reproducible probe; prints the stopping-rule gate status
└── <code>                     encompass.py, calibration.py, program_a.py, live_engine.py, …
```

## The three reinforcing assets

1. **The paper** (`paper/paper1.md`) — the evidence that the process works: a reproducible
   procedure that repeatedly eliminated plausible-but-incorrect hypotheses. Its value is the
   process, not "no edge found."
2. **The live infrastructure** — a daemon collecting toward *explicit measurable thresholds*
   (`protocol/stopping_rules.md`), not toward a vague "enough."
3. **The decisions log** (`decisions/`) — the institutional memory: false positive → discovered
   confound → safeguard invented → safeguard became protocol.

## How the pieces reference each other

- Papers cite safeguards by ID (e.g. "following S-05 and S-11"); `protocol/safeguards.md` defines
  them and `decisions/RESEARCH_DECISIONS_LOG.md` records the failure each came from.
- The **Third Turn Protocol** (method) and the **Third Turn Benchmark Dataset** (data) are named
  and versioned apart on purpose — a benchmark implies a dataset; a protocol implies a method.

## Guardrail (do not skip)

Do not let the methodology grow faster than the questions. Every safeguard must be *earned* by a
concrete, logged failure; every stopping rule must have a numeric criterion. The registry's size
should track the number of distinct failure modes encountered — not the ambition of the method.
