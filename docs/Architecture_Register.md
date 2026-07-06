# The Driftwood Architecture Register

*Internal design document — not a public page. The Canon (`Driftwood_Canon.md`) governs the **pieces**;
this governs the **properties**. Its whole job is to prevent drift: years from now, when a new idea
arrives, there is a simple test — which property does it strengthen, and would it violate that property's
governing purpose?*

Driftwood is a publisher and research institution first, with software that **expresses** the philosophy
— not the other way around. The essays explain the ideas, the Atlas documents the landscape, the Review
applies the framework, and the Diagnostic personalizes it. Each property answers **one governing
question** and has one thing it must **never become**. When a property starts to answer another's
question, or drifts toward its forbidden form, the architecture is weakening — treat that as a defect.

## The permanent properties

| Property | Mode of use | Governing question | Must never become |
| --- | --- | --- | --- |
| **Our Story** | something you *trust* | Who is behind this? | A credentials wall |
| **How We Invest** | something you *study* | Why do we believe this? | A product brochure |
| **Insights** | something you *read* | How should I think? | News / market commentary |
| **The State Atlas** | something you *browse* | How does this state work? | Sales material |
| **After-Tax Review** | something you *work through* | How should this portfolio be structured? | A calculator / fintech dashboard |
| **Tax Diagnostic** | something you *receive* | What is happening in my portfolio? | A generic report |

The distinct **mode of use** matters as much as the question: five properties that all *felt* like tax
calculators would be four too many. Browsing, working through, receiving, reading, and studying are five
different postures — protect that difference.

### On the horizon — governed before they are built

So a future property inherits a purpose rather than acquiring one by accident:

| Property | Mode of use | Governing question | Must never become |
| --- | --- | --- | --- |
| **Investment Policy** *(planned)* | something you *reference* | What are the rules we operate by? | An IPS template / boilerplate |
| **The Driftwood Letter** *(planned)* | something you *await* | What did a year teach us? | A performance recap |

## The two tests every new idea must pass

1. **Which property does it strengthen?** New work should *deepen an existing property* — a better
   citation system strengthens the Atlas; a new flagship essay strengthens Insights; a clearer framework
   strengthens the Review; better methodology strengthens How We Invest. If it strengthens none, it is
   probably not worth doing.
2. **Would it violate that property's governing purpose?** A scorecard that turns the Review into a
   dashboard, an email gate that turns the Atlas into sales material, a timely take that turns Insights
   into news — each is a failure even if it is individually well-made.

A genuinely new **property** faces a higher bar than a feature: it must justify why it deserves to become
another permanent surface, declare its own governing question, and name what it must never become —
*before* any of it is built. The default answer to "should this be a new page?" is no.

## The design filter

For any widget, animation, chart, or "scorecard," ask one question: **does this belong in an advisor's
notebook, or a fintech dashboard?** The notebook is judgment; the dashboard is optimization. Driftwood is
the notebook. Anything that fails this test is cut, however well-built.

## The phase we're in

The major architectural decisions — taxonomy, navigation, naming, separation of concerns — are in place.
The work ahead is **compounding, not invention**: deepen the Atlas until it is citable (sources, an
"as-of" law date, an update history), expand the Canon essay by essay, develop the Investment Policy page
into a flagship reference, refine the Review until it feels inevitable — and only then consider another
software property. Each of these reinforces an existing structure instead of creating new complexity,
which is exactly why they age well.
