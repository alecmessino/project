# Submission & Visibility Kit

Ready-to-paste copy for getting *From Pitcher Fatigue to Market Efficiency* out the door.
Companion to `../ROADMAP.md` (strategy). Everything below is copy you can paste tonight.

---

## A. Where to publish (preprint) — do tonight

| Venue | Fit | Friction | Action |
|---|---|---|---|
| **SSRN** | Best — the paper is written in this register; econ/finance indexing | Free account; instant | Post tonight. Primary citable link. |
| **OSF Preprints** | General, reputable, frictionless | Free; no endorsement | Post as a mirror; gives a DOI. |
| **Zenodo** | For the **dataset + code** (the infrastructure contribution) | Free; instant DOI | Mint a DOI for the Third Turn Benchmark Dataset v1; cite it in the paper's data-availability line. |
| **arXiv** (`q-fin.ST` primary; cross-list `econ.EM`, `stat.AP`) | Strong for the forecasting audience | **Needs a personal endorser** since Jan-2026 policy | Pursue an endorser (any arXiv author in q-fin/econ you know or email); not blocking. |
| SportRxiv | Sports audience, but scope is exercise/performance science | Free | Optional; imperfect fit for an econometrics paper. |

## B. Conferences (beyond MIT SSAC)

| Venue | When / deadline | Notes |
|---|---|---|
| **MIT Sloan SSAC 2027** (Boston) | **Abstract due Oct 1, 2026, 11:59pm EST**; requires an **open-source public repo link**; talks mid-Feb 2027 | The near-term priority. Highest visibility. |
| **NESSIS** (New England Symp. on Statistics in Sports) | Biennial; next ~2027, abstracts ~summer 2027 | Boston-area, academic; ideal fit. |
| **Carnegie Mellon Sports Analytics Conf. (CMSAC)** | Fall; reproducible-research track | Values open code; strong methodological audience. |
| **UConn Sports Analytics Symposium (UCSAS)** | Fall | Academic, welcoming to new work. |
| **Saberseminar** (Boston) | Summer; baseball-specific | Practitioner + research; great for the baseball hook. |
| **JSM**, Section on Statistics in Sports | Abstracts ~Feb for August | A talk slot; academic statistics reach. |
| **WEAI** (Western Economic Assoc. Intl.) | Sessions year-round | The economics-side venue if you want econ exposure. |

## C. Journals (rolling; submit the working paper or after a 2nd month of data)

1. **International Journal of Forecasting** — primary target (encompassing / Clark-West / Diebold-Mariano are their core; they publish negative forecast comparisons).
2. **Journal of Sports Economics** — natural home.
3. **Journal of Quantitative Analysis in Sports** — where Brill-Deshpande-Wyner published the TTOP work.
4. **Journal of Forecasting** — secondary forecasting venue.
5. Aspirational (with the strengthened draft): **Management Science** (Simon 2024) or a finance field journal.

---

## D. Ready-to-paste assets

### D1. Abstract (≈150 words, for SSRN / SSAC / arXiv)

> How completely does a high-frequency market capitalize public information? Live, in-play sports
> betting offers a clean setting: information arrives as discrete, well-valued events and every
> contract settles within hours. Treating a sharp live betting line as an incumbent forecast, we
> apply the Chong-Hendry forecast-encompassing framework to 163 Major League Baseball games, asking
> whether any publicly observable state variable (times through the order, velocity decline, bullpen
> fatigue, line-drop reversion, alternate-line skew, early-run anchoring, weather, park) improves on
> the market's own forecast of remaining runs. None does: the market's forecast error is not
> predictable out of sample (R² = −0.037; a Clark-West test does not favor the augmented model), and
> the design rules out moderate incremental information. The one variable that appears to beat the
> market, a starter's velocity decline, is post-treatment survivorship bias. We name this boundary
> the efficient frontier of public information, and release a validation protocol and benchmark
> dataset.

### D2. Keywords / JEL

*Keywords:* market efficiency; high-frequency betting markets; forecast encompassing; incremental
information; public-information capitalization; calibration; reproducible benchmark.
*JEL:* C53 (forecasting), G14 (information & market efficiency), Z23 (sports economics).

### D3. arXiv metadata

- **Primary:** q-fin.ST (Statistical Finance). **Cross-list:** econ.EM, stat.AP.
- Title + abstract as above. License: CC BY 4.0. Needs an endorser (Section A).

### D4. Cover letter — International Journal of Forecasting

> Dear Editors,
>
> Please consider the enclosed manuscript, "From Pitcher Fatigue to Market Efficiency: A
> Forecast-Encompassing Test of Public Information in Live Baseball Wagering Markets."
>
> The paper uses a sharp live sports-betting line as an incumbent forecast and asks, via the
> Chong-Hendry encompassing framework and a Clark-West nested comparison, whether any publicly
> observable variable improves on it out of sample. Across 163 games it does not: the market's
> forecast error is unpredictable (out-of-sample R² = −0.037), and the design has the power to
> exclude moderate incremental information. A variable that appears to beat the market is shown to
> be post-treatment survivorship bias.
>
> The contribution is threefold: an empirical mapping of where public information stops improving a
> sharp forecast; a methodological one, an escalating validation protocol that shifts the burden
> from demonstrating prediction to demonstrating incremental information beyond an existing forecast;
> and an infrastructure one, a released benchmark dataset and reference implementation. We believe
> the forecast-evaluation framing and the emphasis on a rigorously characterized negative result fit
> the journal's scope. The work is not under consideration elsewhere.
>
> Sincerely, Alec Messino

### D5. Plain-language summary (SSRN abstract page / blog lede)

> We tried to beat live baseball betting markets with everything sabermetrics knows, pitcher fatigue,
> velocity, bullpens, weather, ballparks, and a dozen more. The market had already priced all of it.
> The paper is really about a discipline: telling apart a variable that *predicts runs* from one that
> *improves on the price*, which are not the same thing, and the tool (forecast encompassing) that
> keeps you honest about the difference.

### D6. Social thread (X) — attach Figure 3 and Figure 7

1. We spent months trying to beat live MLB betting markets with everything sabermetrics knows. The market had already priced all of it. New paper 🧵
2. The trap: "this variable predicts runs, so it's an edge." Predicting the outcome and improving on a sharp market's forecast are different problems. We test the second one directly (forecast encompassing). [Fig 3]
3. Across 163 games, no public variable, TTO, velocity, bullpen, weather, park, improves on the live line. The market's forecast error is unpredictable out of sample (R² = −0.037).
4. Our best "edge" was a mirage: velocity decline looked strong (AUC 0.61) until you notice it's only measured on pitchers who survived long enough to be measured. Debias it and it's a coin flip (0.52). [Fig 7]
5. We call the boundary the efficient frontier of public information, and we release the protocol + benchmark dataset so the next hypothesis gets tested against the same yardstick. Paper: [SSRN link]

### D7. LinkedIn post

> New working paper: *From Pitcher Fatigue to Market Efficiency.* We treat a sharp live baseball
> betting line as a forecast and ask whether any public information, times through the order,
> velocity, bullpen, weather, ballpark, improves on it. It doesn't. The interesting part isn't the
> null; it's the method: a forecast-encompassing protocol that separates "predicts the outcome" from
> "beats the price," and a survivorship-bias case study that shows how easily the two get confused.
> Protocol and benchmark dataset released. Link in comments. #SportsAnalytics #Forecasting #MarketEfficiency

### D8. Outreach email (to cited authors, e.g. Brill/Deshpande/Wyner, J. Simon)

> Subject: Encompassing test of live-market efficiency (independently reproduces your TTOP result)
>
> Dr. ___, I thought this might interest you. In a study of live MLB totals I apply a forecast-
> encompassing test to a sharp betting line and find no public variable improves on it; along the
> way I independently reproduce your continuous-decay (no third-time cliff) finding. Preprint here:
> [link]. Any reactions welcome. Best, Alec Messino

---

## E. Checklist (with deadlines)

**Tonight**
- [ ] Post to **SSRN** (title, D1 abstract, D2 keywords/JEL, PDF). Grab the link.
- [ ] Make a **public GitHub repo** (paper PDF + figures + code + committed caches + benchmark dataset + protocol/ops docs). SSAC will require the link; it also anchors reproducibility.
- [ ] Mint a **Zenodo DOI** for the benchmark dataset; drop it into the paper's data-availability line.

**This week**
- [ ] Mirror on **OSF Preprints**.
- [ ] Post the **X thread (D6)** + **LinkedIn (D7)** with Fig 3 and Fig 7; share to r/Sabermetrics and Tom Tango's community.
- [ ] Email **2-3 cited authors (D8)**; ask one who is an arXiv author for an **endorsement**.
- [ ] Add the paper to your **Google Scholar** profile.

**By Oct 1, 2026**
- [ ] Submit to **SSAC27** (abstract + full paper + public repo link).

**Rolling**
- [ ] Submit the journal version to **International Journal of Forecasting** (cover letter D4), after folding in the second month of data if you want temporal robustness first.
