# Project Parallax — Research Log

*A running record of research decisions, hypothesis evolution, methodological changes, and findings as they emerge.*

Evidence and interpretation are kept explicitly separate throughout this log.

---

## 2026-08-18 — Project Initiation

**Status at entry:** Pre-analysis. No substantive hypothesis testing has occurred.

### Originating Observation

Large positive and negative moves in individual equities appear increasingly common, while securities grouped within the same sector, industry, or investment theme sometimes fail to move together as uniformly as expected. This observation motivates the research question but does not constitute evidence for it.

### Research Question Registered

Has the share of individual-security return variation not explained by common systematic exposures increased over time within at least some areas of the U.S. equity market?

### Hypotheses Registered (Pre-Analysis)

**H1 — Rising Security-Specific Importance**
Within at least some U.S. equity sectors or industries, the share of security-level return variation remaining after systematic controls has increased over time.

Primary operationalization: residual or specific variance as a proportion of total security-level variance after controlling for specified systematic exposures.

**H0 — No Meaningful Structural Increase**
After appropriate controls, there is no persistent or economically meaningful increase in security-specific importance across the U.S. equity market or relevant subgroups. H0 is an acceptable and successful project outcome.

Sub-hypotheses H1a (structural expression through dispersion/correlation), H1b (portfolio attribution expression), H1c (explanation test bridging Brinson and factor attribution), H2 (sector heterogeneity), and H3 (regime dependence) are documented in the Project Charter.

### Competing Explanations Registered (Pre-Analysis)

Four explanations are active before any testing begins:

- **A — Genuine idiosyncratic divergence:** firms increasingly behave differently for firm-specific reasons.
- **B — Classification failure:** sector/industry labels increasingly group companies with systematically different exposures.
- **C — Regime effects:** the apparent trend is cyclical or conditional, not secular.
- **D — Availability bias:** the original observation is wrong; visible large moves create an illusion of structural change.

The project must be capable of distinguishing among these explanations, not merely identifying which one is consistent with the data.

### Open Decisions (Registered Unresolved)

The following decisions are intentionally unresolved. They will be locked before Phase 2 hypothesis testing begins.

- **Return frequency:** not yet selected. Will be determined by methodological requirements, literature precedent, and statistical properties of the specific measures used.
- **Historical horizon:** not yet selected. Will be determined by data quality, bias severity, factor-data availability, and regime coverage.
- **Universe:** S&P 500 is the provisional prototype universe. Adequacy depends on Phase 1 survivorship-bias and constituent-coverage validation.

### Analytical Baseline Registered

- **Factor model baseline:** Fama-French Five Factors + Momentum (FF6), sourced from the Kenneth French Data Library.
- **Brinson validation approach:** controlled synthetic portfolios with known expected attribution will be constructed and validated before the engine is applied to empirical portfolios.

### Work Authorized

**Phase 0 — Literature Reconnaissance:** In progress.
Priority topics include: idiosyncratic volatility trends and the Campbell, Lettau, Malkiel, and Xu (2001) literature and subsequent evidence; cross-sectional equity dispersion; within-sector and within-industry correlation; Brinson attribution methodology; factor attribution and Brinson versus factor attribution comparisons; sector-classification explanatory power.

**Phase 1 — Data Feasibility:** In progress.
Initial data source: Yahoo Finance / yfinance. Survivorship bias identified as a first-class analytical risk. Escalation path if free data proves inadequate: Sharadar / Nasdaq Data Link.

### Research Standard

Every material analytical test will record its question, hypothesis, null hypothesis, measurement approach, data used, assumptions made, expected evidence, falsifying evidence, method, result, interpretation, alternative explanations, limitations, confidence level, and next question. Evidence and interpretation will be explicitly separated throughout.

### Note on This Entry

This entry exists to create a public record that hypotheses were registered, competing explanations were enumerated, and open methodological decisions were documented before substantive empirical testing began. The governing principle: the project begins with an intuition, but the intuition does not get a vote once the evidence arrives.

---

*Results will be appended as phases complete.*
