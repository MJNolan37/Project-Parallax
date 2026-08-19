# Project Parallax — Project Charter

**Equity Dispersion, Attribution, and the Changing Importance of Security Selection**

*Public research charter | Aligned with internal baseline v0.2 | August 18, 2026*

---

## 1. Origin of the Question

A simple market observation motivates this project: large positive and negative moves in individual equities appear increasingly common, while securities grouped within the same sector, industry, or investment theme sometimes fail to move uniformly in the way the classification might suggest.

That observation raises a portfolio question. Has security selection become more important relative to allocation decisions in explaining portfolio outcomes? And if it has, is that because individual companies are genuinely behaving more idiosyncratically — or because traditional sector and industry classifications have become less adequate descriptions of economically relevant systematic differences among companies?

This project does not assume an answer. It attempts to measure one.

---

## 2. Primary Research Question

**Has the share of individual-security return variation not explained by common systematic exposures increased over time within at least some areas of the U.S. equity market?**

This is the project's primary scientific question. Its answer must come from data, not from the intuition that generated it.

---

## 3. Core Conceptual Distinctions

Three related concepts are frequently conflated in discussions of market structure and portfolio attribution. Maintaining the distinctions is not pedantry — it determines what evidence can actually support the hypothesis.

### 3.1 Dispersion

Dispersion describes how spread apart security returns are. High dispersion means securities moved differently; it does not explain why. A common factor shock can produce wide dispersion if companies carry different systematic exposures to that factor. Dispersion can increase without idiosyncratic behavior increasing at all.

### 3.2 Brinson Selection Effect

Brinson attribution decomposes active portfolio return into effects attributed to group-level allocation decisions and security selection decisions made within those groups. A rising Brinson selection effect says that security choices within sectors or industries are explaining more active return. It does not establish that those returns were firm-specific. The securities selected may simply carry systematically different factor exposures than their sector peers — a form of implicit factor tilting that Brinson labels as selection.

### 3.3 Specific / Residual Return

After controlling for common systematic exposures, the portion of security return that remains unexplained is specific or residual return. This is the measure closest to the underlying hypothesis. If specific return as a share of total variance is increasing, that is closer to saying the individual company itself is contributing more independently to its return behavior.

**These three may move together. The project does not assume they do. Determining whether they describe the same phenomenon — or systematically different ones — is part of the research.**

---

## 4. Hypotheses

### H1 — Rising Security-Specific Importance

Within at least some U.S. equity sectors or industries, the share of security-level return variation remaining after systematic controls has increased over time.

**Primary operationalization:** Residual or specific variance as a proportion of total security-level variance after controlling for specified systematic exposures. This measure is chosen because it comes closest to the underlying question: is the individual company contributing more independently to its own return behavior?

**Literature context:** Prior work (Campbell, Lettau, Malkiel, and Xu 2001) documents a rise in idiosyncratic volatility over 1962–1997. More recent evidence suggests this trend did not persist cleanly after approximately 2001. H1 is therefore stated as a question under investigation, not as a finding to be confirmed. Period-specific and regime-dependent behavior — captured under Explanation C — is a live candidate. The project makes no assumption about the direction or persistence of the result.

### H1a — Structural Expression

Within-sector or within-industry dispersion has increased over time and/or average within-group correlation has declined. Possible evidence includes higher cross-sectional dispersion, lower average within-sector or within-industry correlations, wider distributions of pairwise correlations, or greater frequency of extreme security-relative moves.

This sub-hypothesis establishes whether the structural phenomenon exists before asking what explains it.

### H1b — Portfolio Attribution Expression

The magnitude of Brinson security-selection effects has increased over time within at least some sectors or industries. This is treated as a portfolio-level expression of changing security differentiation — not as direct evidence of increased idiosyncratic return.

### H1c — Explanation Test

If increasing Brinson selection effects are primarily explained by systematic factor exposures, residual variance should not increase proportionally. Evidence strengthens when Brinson selection rises, factor explanatory power remains insufficient, residual variance rises, and within-group correlation falls. H1c is the project's main bridge between the attribution frameworks.

### H2 — Sector Heterogeneity

Any increase in security-specific importance will not be uniform across the market. The magnitude and direction of change will vary across sectors and industries. No sector-level conclusion is assumed in advance.

### H3 — Regime Dependence

Observed dispersion, correlation, and residual behavior may depend more strongly on macroeconomic conditions than on a stable secular trend. This hypothesis is investigated after the core equity structure is established, not as a prerequisite.

---

## 5. Null Hypothesis

**H0 — No Meaningful Structural Increase**

After appropriate data-quality controls, systematic factor adjustment, and regime conditioning, there is no persistent or economically meaningful increase in security-specific importance across the U.S. equity market or relevant subgroups.

Evidence consistent with H0 may include stable or declining residual variance share, stable within-industry correlations, dispersion increases explained by changing aggregate market volatility, Brinson selection increases explained by factor exposures, trends that disappear after correcting for survivorship bias, or results limited to isolated episodes rather than persistent change.

**A result supporting H0 is a successful outcome of this project.**

---

## 6. Competing Explanations

The project maintains four active competing explanations. It must be capable of distinguishing among them — not merely reporting which one appears to fit.

**A — Genuine Idiosyncratic Divergence**
Companies within the same sector or industry increasingly behave differently for firm-specific reasons. Expected evidence: higher residual variance, lower within-industry correlation, higher unexplained return after factor controls, persistent divergence across multiple regimes and not just one.

**B — Classification Failure**
Apparent selection reflects systematic differences among companies that share a sector or industry label. Companies within a common classification increasingly differ in exposures to size, value, momentum, profitability, capital intensity, interest-rate sensitivity, or secular themes. Expected evidence: Brinson identifies increased selection; factor attribution explains much of that increase; residual variance does not increase proportionally.

**C — Regime Effects**
Security-specific importance varies primarily with market or macroeconomic conditions rather than representing a stable secular change. Expected evidence: high differentiation during some environments, strong common-factor movement during others, long-run averages that mask distinct regime behavior.

**D — Availability Bias**
The original observation may be incorrect. Highly visible large moves in prominent equities may create the impression of structural change when broader data does not support that conclusion. Expected evidence: no meaningful change in broad cross-sectional data after normalization, trends concentrated in highly visible securities, extreme-move frequency stable after conditioning on aggregate volatility, results that disappear in point-in-time constituent samples.

A result consistent with Explanation D is a valid and successful research outcome.

---

## 7. Analytical Framework

The research proceeds through nested analytical layers. Each layer answers a different question and uses different methods. No single layer is sufficient to address the primary hypothesis.

### Layer 1 — Dispersion

*Are security outcomes becoming more differentiated?*

Measures may include cross-sectional standard deviation, interquartile range, median absolute deviation, absolute sector-relative and industry-relative returns, extreme-move frequency, and dispersion normalized by aggregate market volatility. Normalization is required because raw dispersion increases mechanically during high-volatility periods.

### Layer 2 — Correlation Structure

*Are securities classified together behaving less similarly?*

Measures may include rolling pairwise correlations within sectors and industries, average and median within-group correlations, distributions of pairwise correlations rather than means alone, and crisis-period versus normal-period comparisons. Distributions matter because averages can mask structural heterogeneity.

### Layer 3 — Brinson Attribution

*Where does active portfolio return appear: allocation or security selection?*

Core components: allocation effect, selection effect, and interaction effect. Attribution is applied first to controlled synthetic portfolios with known expected outcomes (see Section 9), and then to empirical portfolios once the engine is validated.

### Layer 4 — Factor Attribution

*Can systematic exposures explain apparent selection effects?*

**Baseline model: Fama-French Five Factors + Momentum (FF6)**
Factors: market (Mkt-RF), size (SMB), value (HML), profitability (RMW), investment (CMA), momentum (Mom).
Source: [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)

The FF6 baseline is publicly accessible, academically established, and reproducible from primary sources. It is not treated as a complete or definitive model of security returns. It is the starting point. Additional factors will only be introduced when supported by a documented research reason.

### Layer 5 — Specific / Residual Return

*What remains after systematic controls?*

Measures may include residual variance, residual volatility, rolling model R², and specific-to-total variance ratio. This layer provides the primary test of H1 and the bridge between Layers 3 and 4: a rising Brinson selection effect that is not accompanied by rising residual variance is better explained by factor exposure changes than by genuine idiosyncratic divergence.

### Layer 6 — Macro Regime Interaction *(later extension)*

*Under what environments do the relationships identified above strengthen, weaken, or change character?*

This is an extension of the core equity research. Potential conditioning variables include interest rates, inflation, growth, volatility, and financial conditions. This layer is not a prerequisite for the initial hypothesis test.

---

## 8. Data Strategy

**Initial universe:** S&P 500 (provisional — see Open Design Decisions)
**Market data:** Yahoo Finance / yfinance
**Factor data:** Kenneth French Data Library

The use of free market data is an explicit prototyping decision, not an assumption that the data is institutionally complete.

---

## 9. Known-Answer Brinson Validation

Before the Brinson attribution engine is applied to empirical portfolios, it is validated against controlled synthetic portfolios designed to produce known expected attribution results.

**Portfolio A — Selection Only**
Benchmark sector weights preserved. Security weights altered within sectors. Expected result: primarily security-selection attribution with minimal allocation effect.

**Portfolio B — Allocation Only**
Sector weights altered. Within-sector security weights kept benchmark-like. Expected result: primarily allocation attribution with minimal selection effect.

**Portfolio C — Combined Effects**
Both sector weights and within-sector security weights altered. Expected result: allocation, selection, and interaction effects are all present.

These known-answer cases are encoded in `tests/test_brinson.py`.

> If the attribution engine cannot correctly explain a portfolio we deliberately constructed, it should not be trusted to explain a portfolio we did not.

*These synthetic portfolios exist solely to validate attribution methodology and are not investable portfolios or investment recommendations.*

---

## 10. Survivorship Bias as a Design Problem

Survivorship bias is a first-class analytical risk, not a post-analysis caveat. Current S&P 500 membership is not equivalent to historical point-in-time membership. Using only current constituents creates a dataset composed of companies that survived — a systematic distortion that would bias findings toward lower apparent historical dispersion and higher apparent historical return.

The data pipeline will explicitly monitor and document:

- missing historical securities
- delisted companies and their histories
- constituent additions and removals over time
- ticker changes and corporate actions
- incomplete return histories
- sector and industry reclassifications
- point-in-time universe limitations

Bias diagnostics are implemented alongside data ingestion, not added after results are examined.

**If the free dataset materially distorts inference, the project will document the failure and migrate to an improved source.**

Current escalation candidate: Sharadar / Nasdaq Data Link.

> Discovering that a dataset cannot answer the question reliably is itself a research result.

---

## 11. Open Design Decisions

The following decisions are explicitly unresolved and will be registered before substantive hypothesis testing begins in Phase 2.

**Return Frequency**
The primary return frequency (daily, weekly, or monthly) has not been selected. Selection will be based on methodological requirements, literature precedent, statistical properties of the specific measures used, and data availability. Dispersion, correlation, factor estimation, and attribution can behave materially differently across frequencies.

**Historical Horizon**
The primary research start date has not been selected. It will be determined by data quality, constituent-data availability, survivorship-bias severity, and the need to capture multiple market regimes — not by which horizon produces more favorable results.

**Universe**
S&P 500 is the provisional prototype universe. Whether it is adequate for defensible inference depends on Phase 1 survivorship and constituent-coverage validation. A broader universe may be evaluated if data quality and research value justify expansion.

Publishing these unresolved decisions before analysis begins is intentional. It is the structure of preregistration, not an admission of incompleteness.

---

## 12. Research Phases

| Phase | Question | Primary Output | Gate |
|---|---|---|---|
| 0 | What is already known? | Literature review | Does H1 remain genuinely open? |
| 1 | Can the data support the question? | Bias & feasibility report | Is the dataset defensible for inference? |
| 2 | Does the phenomenon exist? | Dispersion / correlation analysis | Is the structural observation real after normalization and bias controls? |
| 3 | Does the Brinson engine work? | Attribution engine + tests | Does it reconcile correctly on known-answer portfolios? |
| 4 | What do systematic factors explain? | Factor attribution engine | Is the FF6 baseline sufficient for comparison? |
| 5 | Where do the frameworks agree and disagree? | Comparative attribution | Does combining frameworks reveal additional structure? |
| 6 | Has the structure changed through time? | Structural change analysis | Is the change secular, cyclical, sector-specific, or unsupported? |
| 7 | When does the macro environment matter? | Regime analysis | Does regime conditioning materially improve explanation? |

No phase is treated as mandatory if an earlier gate invalidates its underlying question.

---

## 13. Research Integrity

- Hypotheses are registered before substantive testing begins.
- Exploratory findings are labeled as exploratory and not represented as preregistered.
- A hypothesis generated after observing results is not retroactively treated as prior.
- Methodology changes are documented with the reason for the change and its effect.
- Contradictory evidence is retained, not omitted because it is inconvenient.
- Negative results are retained and documented.
- Data limitations and known biases are disclosed alongside findings, not buried in footnotes.
- Only public or independently licensed data is used. No proprietary data from any employer is included.

---

## 14. AI-Assisted Development

AI tools are used in this project for code development, literature discovery, methodological critique, debugging, and documentation. AI output is not treated as empirical evidence. Research conclusions must trace to reproducible calculations, verified data, transparent methodology, and appropriate external research.

The research log documents material cases where AI contributed to, challenged, or changed the research design.

AI can accelerate the construction of research tools. It does not get to decide whether the hypothesis is true.

---

## 15. Falsification

The project is structured around falsification, not confirmation. The evidence is what matters. A valid final answer to the primary research question may be any of the following:

- Yes — security-specific importance has increased
- No — it has not
- Yes, but only in specific sectors
- Yes, but only during specific regimes
- Apparently yes, but largely explained by systematic factor exposure changes
- Apparently yes, but an artifact of survivorship bias or changing constituent composition
- Impossible to establish with available data

Scientific value comes from narrowing uncertainty, not from producing a predetermined conclusion.

---

*The project begins with an intuition, but the intuition does not get a vote once the evidence arrives.*
