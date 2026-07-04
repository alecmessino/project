# Reference results — Third Turn Benchmark Dataset (v1)

Ten public-information signals evaluated with the Third Turn Protocol against a sharp live MLB
totals market. **None clears forecast encompassing.** New signals should report their elimination
rung against this table (see `../examples/report_template.md`).

## Headline: forecast encompassing (rung 6)

| model | out-of-sample R² (remaining runs) |
|---|---|
| our features alone (`Y ~ X`) | 0.279 |
| sharp market alone (`Y ~ B`) | **0.304** |
| market + features (`Y ~ B + X`) | 0.286 |
| **encompassing gain** (`B+X` − `B`) | **−0.017** |
| book error predictable from features (`(Y−B) ~ X`, OOS R²) | **−0.037** |

Per-feature incremental R² beyond the market (E+) is ≤ +0.0018 for every feature (bullpen best;
velocity, tier, park, weather ≤ 0). The market encompasses each feature jointly and individually.

## The ten reference signals and where each is eliminated

| signal | eliminated at rung | key diagnostic |
|---|---|---|
| Times-through-order penalty | 2 Robustness | decay is continuous, not a cliff; OOS below breakeven |
| Velocity decline | 4 Debiasing | post-treatment selection; clean AUC 0.61 → 0.52 |
| Bullpen-fatigue multiplier | 1 Signal | fatigued bullpens concede no more runs |
| Drop reversion (Over) | 3 Out-of-sample | right-skewed; median below the line |
| Drop reversion (Under) | 2 Robustness | not monotone; concentrated in the recent sample |
| Alternate-line skew | 5 Conditional | empirical < implied at every increment |
| Early-run anchoring | 5 Conditional | market prices the climb (hit-driven bursts) |
| Weather / park context | 5 Conditional | hitter-friendly Overs hit *less* (over-adjusted) |
| Remaining-runs fatigue term | 6 Encompassing | ΔMAE ≈ 0 (no improvement); game state already suffices |
| **Forecast encompassing (all features)** | **6 Encompassing** | **book error not predictable OOS (R² −0.037)** |

## Transfer function (rung 7)

Every positive-run event lies on one common slope ≈ 0.74 through the origin (walk 0.63, double 0.64,
single 0.72, home run 0.81, triple 0.84) — uniform attenuation consistent with single-source ~1-min
measurement, not a per-event inefficiency. The market is approximately calibrated within the sample
(remaining-runs model R² = 0.226; book error mean +0.49 but median 0 — right-skewed, and unpredictable).

*All numbers are the committed values in `../../output/*.json`.*
