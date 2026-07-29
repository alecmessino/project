<div class="titleblock">
<h1>What Prices Cannot Tell You: Identifying Information Transmission in Live Markets</h1>
<p class="epigraph">Markets reveal prices. They do not reveal how those prices came to be.</p>
<p class="author">Alec Messino<br/><span class="affil">The Third Turn Research Initiative &middot; alec.messino@gmail.com</span></p>
<p class="wp">Working Paper &middot; DRAFT, Sections 1-5 &middot; Results not yet written</p>
</div>

> **Draft status.** This manuscript is complete through the Methods section. The Results and
> Discussion sections are deliberately unwritten: they are gated on four objective measurement
> conditions stated in Section 5.6, and the analysis plan in Section 5.5 is pre-registered so that
> the design cannot be shaped by the evidence. Nothing in the sections below reports an empirical
> finding from the dataset described in Section 4.

## Abstract

A companion study found that a live baseball wagering market encompasses every public-information
candidate tested against it: no variable in a ten-hypothesis ladder improved on the market's own
forecast of remaining runs. That null is a statement about outcomes, and it invites a question about
mechanism. The companion study asked whether prices *contain* public information; this paper asks
whether prices *reveal how that information entered the market*. Information in prices and formation
of prices are distinct questions, and the second does not follow from the first by adding data.

We take up the transmission question directly, and find that it is largely an identification problem.
The delay between a game event and an observed price change decomposes into a bookmaker's pricing
latency, its feed's transport latency, and the observation latency imposed by our own sampling. That
decomposition is arithmetic. The substantive difficulty is that only their sum is observed, and this
paper is about what can and cannot be learned under that constraint. We show that three materially
different markets, one in which a bookmaker genuinely prices faster, one in which pricing speeds are
identical and only publishing infrastructure differs, and one in which both differ and partially
offset, generate numerically identical timestamp data. No statistic computed from timestamps alone
separates them.

Working from a two-book, thirty-one-second live quote panel matched to game-state events, we define
an event-anchored response latency and state precisely the conditions under which its cross-book
contrast is a statement about pricing rather than about plumbing. We show that several intuitive
estimators of information leadership are mechanically confounded by update frequency and by the
analyst's choice of which posted line to treat as the main line, and we characterize the resolution
floor below which this class of instrument is silent. The design admits three outcomes, all of which
we regard as publishable: identification of a pricing contrast, identification of bounds only, or a
demonstration that the quantity is not identifiable without richer instrumentation. The third is not
a failure of the study. Much of the microstructure literature studies environments in which richer
event and timestamp information is available than sportsbook endpoints provide, so the decomposition
we confront can often be assumed away there rather than established. Showing precisely where it
cannot be assumed away is itself a contribution.

---

## 1. Introduction

Every pitch thrown in a Major League Baseball game can trigger dozens of price updates across
sportsbooks before the next pitch is delivered. These are high-frequency markets in the ordinary
sense, with one property that makes them an unusually clean laboratory for studying price formation:
every contract settles within hours against an objective terminal payoff, so the quantity being
forecast is eventually revealed and the forecast can be graded. Equity prices offer no such closure.

Market efficiency tests answer a question about outcomes. They ask whether some information, held by
someone, would have improved on the price. When the answer is no, as it frequently is, the finding is
reported and the matter closed. But a null of that kind is a statement about a mechanism whose
operation was never observed. Something incorporated the information. The efficiency test does not
say what, or how quickly, or through which participant.

This paper begins where a companion study ended. That study treated a sharp live betting line as an
incumbent forecast of the runs remaining in a baseball game and asked whether any of ten publicly
observable candidates, pitcher fatigue and velocity decay among them, carried incremental predictive
content beyond it. None did, and the one candidate that appeared alive proved to be a post-treatment
selection artifact.

The two studies stand in a natural progression rather than a sequence of increments. **Paper 1 asked
whether prices contain public information. This paper asks whether prices reveal how that
information entered the market.** The first is a question about the content of a price; the second is
a question about its formation, and the two are answered with different instruments and different
assumptions. The transition can be stated more precisely still. **The
companion study established that public baseball variables contain no incremental information beyond
a sharp market observed at one-minute resolution; this paper asks whether that apparent efficiency is
genuine, or whether it is partly an artifact of observing the market only after the information has
already propagated through it.** The companion study's closing section anticipates the question,
listing cross-book propagation, the information half-life of a shock, and the microstructure limits
of one-minute single-book snapshots among the things its data could not settle.

The obstacle is not statistical power. It is that the process of interest is unobserved. A baseball
market is punctuated by discrete, publicly dated events, and each is followed, sooner or later, by a
revised price; but between the event and the revision we record sit stages that no outside observer
sees.

![](figures/p2_boundary.png)

**Figure 1.** *We never observe the pricing process itself.* Of the five stages between a game event
and a row in our dataset, the two in the shaded band are exactly the two the question is about: when
the bookmaker decided to move, and when its feed made that decision visible. Everything we record
sits below the boundary.

Box 1 makes the difficulty concrete before any notation is introduced.

<div class="protocol-box">
<div class="pb-title">Box 1. A thought experiment</div>
<p>Two sportsbooks are quoting the same game. A run scores. Book A updates its price 800
milliseconds later; Book B updates 1.6 seconds later. You observe both prices once every 30 seconds.</p>
<p>Can you conclude that Book A processes information faster?</p>
<p><strong>No.</strong> You did not observe the pricing engines, the feed delays, or the moment the
event actually occurred. You observed two timestamps, produced by a sampling process of your own
construction, at a resolution nearly twenty times coarser than the difference you are trying to
detect. Both books land in the same poll. The data are silent.</p>
<p>This paper is about what it takes to make them speak, and about being candid when they cannot.</p>
</div>

The problem has a familiar shape. Astronomers infer the mass of a planet they cannot see from the
wobble of a star they can, and the inference is only as good as the model of what lies between the
observer and the object; much of the work is characterizing the instrument rather than the sky. Our
position is the same. **Markets reveal prices. They do not reveal how those prices came to be.**

Two prices are therefore the minimum. A single book's response time confounds how fast the bookmaker
reprices with how fast its infrastructure publishes and how fast the analyst happens to be sampling.
Comparing two books raises the possibility that the shared components difference out. Whether they
actually do is an architectural question about publishing infrastructure, not a statistical one, and
it is the question on which the paper's central estimand stands or falls. Section 3 shows that three
materially different markets generate numerically identical timestamp data, so the possibility cannot
be settled by any statistic computed from the timestamps themselves; that result, illustrated in
Figure 4, is the paper's core.

We frame this accordingly as a paper about identification in high-frequency markets, not as a second
efficiency paper and not as a paper about sportsbooks. Sports betting is the laboratory, chosen
because its information arrivals are discrete and precisely dated and its contracts settle against
ground truth. The identification problem it exposes is general. Three consequences follow.

First, the estimand must be defined before the data are examined, because the intuitive estimators
are wrong in a specific and instructive way. The obvious approach, timing one book's price change
against the other's, is mechanically biased toward whichever book updates more often. A book that
re-prices every thirty seconds will reach any given price level before a book that re-prices every
eight minutes, regardless of which one is better informed. That is not leadership; it is sampling.

Second, the identification problem must be confronted rather than assumed away. The delay we observe
is a sum of three delays, and only one of them is about pricing. Separating them requires either an
independent measurement of transport latency or an argument that transport latency is common across
books. Neither is free, and we do not assume either.

Third, the instrument's limits must be stated in advance. A panel sampled every thirty-one seconds
cannot resolve sub-second price formation. If the economically interesting action happens below the
sampling floor, no amount of care in the analysis will recover it, and the honest report is that the
question is out of reach for this apparatus.

The paper is organized around those three commitments. Section 2 develops the conceptual framework
and decomposes the observed delay. Section 3, the heart of the paper, treats identification: what can
and cannot be learned from a two-book panel, and under exactly which assumptions. Section 4 describes
the data and explains why this instrument differs fundamentally from the one used in the companion
study, a difference that precludes any direct comparison of results. Section 5 states the estimation
procedure and the pre-registered analysis plan, and closes by listing the objective conditions that
must be satisfied before results may be reported.

---

## 2. Conceptual framework

### 2.1 The transmission chain

Consider a discrete, publicly observable event in a baseball game occurring at clock time
`t_E`: a run scores. The event changes the conditional distribution of the game's final total, and a
bookmaker offering a live total on that game will, at some point, revise its posted number. An
outside observer records the revision at some later time. Between the event and the record lie three
distinct delays, produced by three distinct mechanisms.

**Pricing latency**, which we write as the interval between the event and the bookmaker's internal
decision to revise, is the economically meaningful quantity. It reflects how quickly the bookmaker
detects the event, updates its model, and commits to a new number. Differences in pricing latency
across books are differences in how the market processes information.

**Feed latency** is the interval between the bookmaker's internal revision and the moment that
revision becomes visible on the public endpoint we query. It is a property of publishing
infrastructure, caching, and content delivery, not of judgment about baseball.

**Observation latency** is the interval between publication and our sampling of it. It is a property
of our own collector. With a polling interval of roughly thirty-one seconds, a revision published
immediately after a poll waits, on average, about fifteen seconds to be seen, and up to
thirty-one seconds in the worst case.

![](figures/p2_race.png)

**Figure 2.** *Four internal events; two recorded numbers.* Each book decides to re-price and
each book's feed publishes that decision. None of the four is visible. What we hold is one
timestamp per book, and the interval we can measure is a sum of intervals we cannot measure
separately.

![](figures/p2_why_paper1.png)

**Figure 3.** *Paper 1 never needed to identify internal latency.* It compared two endpoints, a
public variable and a realized outcome, with the market price between them, and every node it
required was observable. This paper's question is the machinery itself, and two of its four
stages are hidden from any outside observer.


The data contain only the sum. For book `b` and event `E`, the observable is

> `Δt_b(E) = λ_price_b(E) + λ_feed_b(E) + λ_obs_b(E)`

As an accounting identity this is unremarkable, and we do not present it as a contribution. Writing
a delay as a sum of its parts is bookkeeping. What matters is the consequence: **no manipulation of a
single book's series recovers the individual terms, because only the left-hand side is ever
observed.** Everything difficult about this paper follows from that sentence, which is why the
identification section is longer than the estimation section.

### 2.2 Why two books might help

If the second and third terms were identical across books, the cross-book difference would remove
them:

> `Δt_A(E) - Δt_B(E) = λ_price_A(E) - λ_price_B(E)`

and the contrast would isolate the economics. This is the hope that motivates a two-book design, and
it is an assumption, not a fact.

![](figures/p2_three_worlds.png)

**Figure 4.** *Identical observations can arise from different underlying markets.* In the first world a bookmaker genuinely
prices faster and the publishing infrastructure is equal, so the observed lag means what it appears
to mean. In the second, the two bookmakers price at identical speed and the entire observed lag is
produced by one book's slower feed. In the third, both differ and partially offset. The observed
timestamps, marked by the dashed guides, fall in exactly the same places in all three panels. The
datasets are numerically identical; the markets are not. Any statistic computed from timestamps
alone assigns the same value to all three, so distinguishing them requires evidence from outside the
timing series.

Observation latency is plausibly common-mode by construction: a single collector polls both books on
the same schedule, so the sampling penalty is drawn from the same distribution for each. Feed latency
is not. Two commercial sportsbooks run different infrastructure, and there is no reason in principle
for their publishing delays to match. Whether the difference is material relative to the pricing
differences we hope to detect is precisely what Section 3 must establish.

### 2.3 Why the estimand is anchored to the event

A tempting alternative avoids the event entirely: observe when each book arrives at a given price
level and call the earlier one the leader. This is mechanically defective.

![](figures/p2_anchoring.png)

**Figure 5.** *A denser book leads by construction, not by insight.* Left: a book that re-prices frequently passes through any given price level before a
book that re-prices rarely, purely as a consequence of update density. A leadership statistic built
on book-to-book arrival times reports this sampling artifact as information leadership. Right:
anchoring each book's response to the exogenous game event measures each against a clock that neither
book controls, so update density no longer confers a spurious advantage.

The game event is exogenous to both books in the relevant sense: runs are not caused by bookmaker
quoting behavior. Anchoring to it converts a comparison between two endogenous, differently sampled
series into two comparisons against a common external clock. This does not solve the feed-latency
problem, but it removes the frequency confound, which is a distinct and more easily made error.

### 2.4 What the market is quoting

One structural fact about the instrument shapes the analysis and is easy to get wrong. The posted
live number is a **full-game total**, not a forecast of remaining runs: it is the expected final
combined score, incorporating runs already scored. Consequently a run that scores enters the posted
number with a positive sign, partially offset by the reduction in scoring opportunities that remain.
A revision following a run is therefore expected to be upward, and its magnitude is a pass-through
fraction rather than an elasticity. We verify this property directly in Section 4 rather than
assuming it, because the opposite convention would reverse the sign of every response we measure.

---

## 3. Identification

This section is the paper's core contribution. We state the assumptions under which the cross-book
contrast identifies a pricing difference, examine each against what is known about the instrument,
and describe what remains estimable when an assumption fails.

### 3.1 The estimand

As Figure 4 makes clear, the target of inference cannot be read off the data; it must be defined and
then argued for. Let `E` index discrete game events with clock times `t_E`, and let `t_b(E)` denote the time of book
`b`'s first main-line revision attributable to `E`. Define the event-anchored response latency

> `λ_b = E[ t_b(E) - t_E ]`

and the cross-book contrast `Δλ = λ_A - λ_B`. The target of inference is `Δλ`, and the question the
paper asks is under what conditions `Δλ` is a statement about pricing rather than about plumbing.

### 3.2 The assumptions

**A1. Event exogeneity.** Game events are not caused by bookmaker quoting behavior. This is
uncontroversial in this setting and is the reason event anchoring is available to us at all.

**A2. Clock comparability.** Event timestamps and quote timestamps are on a common, comparable
clock. This is not automatic. Event times are derived from one upstream provider and quote times from
another, and either may be a publication time rather than an occurrence time. A2 requires a direct
audit of timestamp provenance, and any residual skew must be quantified rather than assumed away,
because a constant skew shifts both `λ_A` and `λ_B` equally but a book-specific skew is
indistinguishable from a pricing difference.

**A3. A well-defined main line.** The response `t_b(E)` presupposes a single price series per book.
Books post multiple simultaneous total lines, a main line and alternates, without a discriminator.
Reasonable rules for extracting the main line disagree with one another on a large majority of
observations, and downstream statistics move materially depending on the choice. A3 therefore
requires a fixed, documented, and tested extraction rule, together with a demonstration that the
conclusions do not depend on it.

**A4. Separability of transport from pricing.** This is the binding assumption, and Figure 4 is its
statement in visual form. `Δλ` identifies the
pricing contrast only if feed latency is common-mode across books, or if a book-specific transport
component can be independently measured and removed. We do not assume A4 holds. Establishing whether
it holds, or demonstrating rigorously that it cannot be established with instruments of this class,
is the paper's principal empirical task.

**A5. Sufficiency of two books.** With two books, a discrepancy is detectable but not attributable:
if one book behaves anomalously there is no third observation to adjudicate which is anomalous. A5
therefore concerns robustness rather than point identification, and it is either satisfied by adding
a third live source or addressed by an explicit outlier-detection procedure that does not require
one.

**A6. Non-arbitrary attribution.** The mapping from an event to "the revision caused by it" requires
an attribution window. A window chosen after inspecting the data is a researcher degree of freedom
capable of manufacturing an effect. A6 is satisfied by pre-registration, which is why the window is
fixed in Section 5.5 before any estimate is produced.

### 3.3 Three admissible outcomes

The design admits exactly three outcomes, and we commit in advance to reporting whichever obtains.

**Outcome A. The pricing contrast is identified.** The clock audit passes, feed latency is shown to
be common-mode or is independently measured, and the extraction rule is shown not to drive the
result. The cross-book contrast is then a statement about how two bookmakers process information.

**Outcome B. Only bounds are identified.** Some assumption holds partially: transport latency is
bounded but not known, or the result is directionally stable but magnitude-sensitive to the
extraction rule. The reportable object is then an interval within which the pricing contrast must
lie, together with the assumption that produced it.

**Outcome C. The quantity is not identifiable with this class of instrument.** No external
measurement of feed latency is obtainable from public endpoints, and no argument establishes
common-mode behaviour. This is the case in which the three worlds of Figure 4 remain
observationally equivalent no matter how much data accumulates. The reportable result is then a demonstration, not a guess: a proof that
timestamp data from public sportsbook endpoints cannot separate market behaviour from publishing
infrastructure, together with a specification of the additional instrumentation that would be
required.

We want to be explicit that Outcome C is a result and not a failure. Much of the market
microstructure literature works in settings where researchers observe richer event and timestamp
information than public sportsbook endpoints provide: exchange-side sequencing, order-level
identifiers, and venue timestamps that pin the publication stage directly. Where that information is
available, the decomposition this paper confronts can be handled by construction. Where it is not,
the discipline is to demonstrate its unavailability rather than to proceed as though the richer
setting obtained. A paper that establishes where identification breaks down tells a subsequent
researcher what to build.

![](figures/p2_ladder.png)

**Figure 6.** *Identification requires assumptions, not computation.* The requirements form a ladder, and each rung depends on the one above it. Each rung depends on the one above it. We hold the top
two. The third is a methodological choice we can fix and test. The fourth, knowledge of feed latency,
is not obtainable from public endpoints, and the fifth depends on it. The colour of the fourth rung
is what determines whether this paper reports Outcome A, B, or C.

![](figures/p2_decision_tree.png)

**Figure 7.** *The paper does not presuppose which branch it takes.* The same logic, as a decision
the reader can walk. All three terminal states are publishable, and the third is the one a study is
least likely to report.

### 3.4 The resolution floor

An instrument cannot report structure below its sampling interval.

![](figures/p2_resolution.png)

**Figure 8.** *The instrument itself limits what can be learned.* The game is finer than the sampling window. Pitches, balls, strikes, and the run itself
arrive on a scale of seconds; our sampling collapses everything inside a thirty-one-second window
into a single observation. A book that re-priced two seconds after the run and one that re-priced
twenty-five seconds after it are recorded identically. This bounds the paper's ambition: no claim
below the window is supportable, and we make none. The figure describes the apparatus, not the
market.

This limit is worth stating plainly because it bounds the paper's ambition. Financial microstructure
research often concerns latencies measured in microseconds. Nothing in this design speaks to that
regime. What it can speak to is the slower, human-and-model-mediated process by which a sportsbook
absorbs a publicly visible event, and whether two such processes can be distinguished from outside.

---

## 4. Data and institutional setting

### 4.1 The instrument

The data are generated by a continuously running collector that polls two sportsbooks and a
game-state provider on a fixed schedule and appends every observation to an append-only panel. The
properties below are verifiable facts about the apparatus rather than findings, and we state them as
such.

| Property | Value |
|---|---|
| Sampling cadence (live) | approximately 31 seconds, median, both books |
| Books observed | two, both retail-facing |
| Games with live quotes | in excess of one hundred, accumulating |
| Quote fields | posted line, both sides' prices, live flag, market status |
| Market status coverage | one book only |
| Game state | inning, half, outs, base occupancy, score, pitch count, times through order |
| Line semantics | full-game total, verified against pregame distribution |

![](figures/p2_windows.png)

**Figure 9.** *Different instruments reveal different phenomena.* The June apparatus saw a sharp benchmark
book, pitch-level measurement, and weather; it could not see two books at once or a market's live
status. The July apparatus sees the second book and the status stream but is blind to everything the
first could measure. Neither is better. They are blind in different places, which is why a result
from one cannot confirm or contradict a result from the other.

### 4.2 What this instrument does not contain

Three absences are load-bearing for interpretation and are properties of the design rather than
accidents of a particular sample.

There is **no sharp benchmark book**. Both observed books are retail-facing. The companion study used
a sharp book as its incumbent forecast; nothing in this panel plays that role, and the leadership
question here is therefore about two retail books rather than about a sharp-to-retail information
cascade.

There are **no pitch-level or meteorological covariates**. The companion study's feature set is
unavailable here.

**Market status is asymmetric**. One book publishes an explicit open, suspended, or removed state;
the other publishes nothing. Any analysis that filters on tradeability can therefore only be applied
to one book, and applying it to one and not the other introduces selection that favors the filtered
book.

### 4.3 Why no comparison with the companion study is possible

It is tempting to treat this dataset as a second sample of the companion study's population. It is
not. The two differ in the benchmark book, in the available covariates, and in the sampling cadence.
Any difference in results between them would be jointly attributable to the passage of time and to
the change of instrument, with no way to apportion between the two. We therefore make no claim in
either direction about the companion study's conclusions. A temporal replication of that study
requires re-running its own instrument, and is a separate exercise reported elsewhere.

---

## 5. Methods

### 5.1 Constructing the event series

Events are extracted from the game-state panel as changes in the combined score between consecutive
observations. The event time is the timestamp of the first observation exhibiting the new score,
which is itself subject to the provider's own publication delay; A2 concerns exactly this, and the
audit described in Section 5.6 quantifies it. Events are typed by magnitude, since a solo home run
and a bases-clearing double are different information arrivals.

### 5.2 Constructing the price series

For each book, the main line is extracted per observation timestamp under a single fixed rule, and
the series is reduced to the sequence of distinct quote states. Repeated identical quotes are not
revisions and are collapsed. The extraction rule is fixed in advance, and the sensitivity of every
reported quantity to that choice is reported alongside it, per A3.

### 5.3 Attribution

A revision is attributed to an event if it is the first distinct main-line change occurring within a
fixed post-event window. The window is stated in the pre-registered plan below. Events whose windows
overlap a subsequent event are flagged and analyzed separately, since attribution is ambiguous when
two information arrivals are closer together than the response time being measured.

### 5.4 Estimation and inference

The unit of replication is the game, not the observation. Quotes within a game are strongly
dependent, and treating them as independent produces intervals that are far too narrow. All
estimation therefore proceeds by computing a per-game statistic and treating the game as the
sampling unit, with intervals constructed accordingly.

### 5.5 Pre-registered analysis plan

Every item below exists to prevent one of the failure modes in Figure 4 from being mistaken for a
finding. The following is fixed before any estimate is computed. Departures from it will be reported as
departures.

1. **Primary estimand.** The cross-book contrast in event-anchored response latency, `Δλ`.
2. **Event definition.** A change in combined score, typed by magnitude.
3. **Attribution window.** Three hundred seconds after the event. Events with a subsequent event
   inside the window are analyzed as a separate, flagged stratum.
4. **Main-line extraction.** A single odds-anchored rule, fixed and documented, with a mandatory
   sensitivity analysis across at least two alternative rules.
5. **Unit of replication.** The game.
6. **Primary comparison.** Direction and magnitude of `Δλ`, reported with a game-clustered interval.
7. **Mandatory falsification tests.** Before any leadership interpretation is offered: a
   symmetry test comparing the frequency of pre-event and post-event revisions, which separates a
   genuine response from a book's baseline revision rate; a shuffled-event placebo; and the
   extraction sensitivity analysis of item 4.
8. **Reporting rule.** A null result is reported with the same prominence as a positive one. No
   estimand, window, or extraction rule is added or altered after inspecting the results.

### 5.6 Conditions required before results may be reported

The Results section of this paper remains unwritten until all four of the following hold, each
verified and recorded:

1. **A well-defined main line.** An extraction rule fixed in code and tested, with a demonstration
   that the primary statistic is materially invariant to reasonable alternatives.
2. **Clock comparability.** An audit establishing that event and quote timestamps are comparable,
   with residual skew quantified.
3. **Transport separability resolved in one direction.** Either an independent measurement of
   book-specific feed latency, or a defended argument that it is common-mode, or a documented
   demonstration that neither is achievable with this class of instrument. The third outcome
   satisfies this condition and converts the paper into a pure identification result.
4. **Robustness support.** A third live source, or an explicit outlier-detection procedure that does
   not require one.

Stating these in advance is the point. A paper that fixes its design before seeing its evidence
cannot be reshaped by the evidence, and a null that arrives under those conditions carries the same
weight as a finding.

---

## 6. Scope of the contribution

Here the paper stops being about sportsbooks.

The identification problem set out above is not a peculiarity of betting markets. It arises whenever
a researcher observes the output of a process rather than the process itself, and wishes to attribute
a measured interval to one stage of that process rather than another. An econometrician timing how
quickly an exchange incorporates a macroeconomic release faces the same decomposition: some of the
measured delay belongs to the traders, some to the exchange's own dissemination, and some to the
vendor feed the researcher happens to have purchased. A political scientist timing how quickly
legislatures respond to public opinion confronts it. So does anyone measuring the speed of pass
through from a policy rate to a posted lending rate. In each case the estimand is a property of an
unobserved stage, and the data are the sum of that stage and the plumbing around it.

What betting markets add is not a novel problem but an unusually clean setting in which to state it.
The information arrivals are discrete, publicly visible, and precisely dated; the contracts settle
against ground truth within hours; and two competing quotes on the identical contract can be observed
simultaneously. Where a general treatment would be forced into abstraction, here the three stages can
be named, the boundary of observation can be drawn, and the conditions for identification can be
written down and checked. A setting in which the problem is tractable is worth more to the literature
than a setting in which it is merely important.

The methodological claim is correspondingly modest and, we think, general. Timestamps are
observations; latency is an inference. Any transmission estimate is a joint statement about the
market and about the apparatus that observed it, and the two cannot be separated by assertion. Where
the separation can be defended, the estimate means what it appears to mean. Where it cannot, the
honest report is a bound, or a demonstration that no bound is available, together with a
specification of the instrument that would be required. Better measurement produces better
identification; better argument does not.

We would rather end on that discipline than on a result. When the mechanism is unobserved, rigour
lies not in stronger conclusions but in recognizing precisely where conclusions end.

**Observation survives. Identification does not.**

---

## Appendix. Where this sits in the research program

![](figures/p2_bridge.png)

**Figure 10.** *Information in prices; formation of prices.* Paper 1 asked whether prices contain
public information and could answer it, because every node it needed was observable. This study starts from an event, passes through a process it cannot see, and arrives at a
timestamp whose interpretation depends on assumptions rather than on computation. The first paper
ends in a finding. The second ends, at best, in a set of conditions.

---

*Sections 6 (Results) and 7 (Discussion) are intentionally not drafted. See Section 5.6.*
