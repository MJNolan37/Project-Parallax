# Project Parallax
**Equity Dispersion, Attribution, and Return Structure**

> **Status: Phase 1 Complete | Phase 2 Pending Gates | No Hypothesis Testing Has Occurred**

---

## Research Question and Why Now

Has the balance between market-, industry-, and firm-specific variation in U.S. equities changed materially since the original Campbell-Lettau-Malkiel-Xu research, and what might that imply for the importance of security selection today?

Does the individual company matter more, or differently, than it once did?

Campbell, Lettau, Malkiel, and Xu (2001) decomposed equity return variance into three components: market-wide, industry-level, and firm-specific. Phase 1 of this project reproduces a public-data version of that decomposition for 2010-2024, establishing the measurement foundation. No hypothesis has been tested.

**Why revisit it now?** The original literature studied a market substantially different from today's. Two competing forces operate simultaneously, and neither can be assumed to dominate.

Modern market structure could make equities more systematic: passive and algorithmic flows, rapid information transmission, and common-factor exposures may increasingly move securities together.

The same era could make equities more differentiated: winner-take-most economics, intangible capital, technology-driven competitive divergence, and AI as a variable affecting firms unequally may push company-level outcomes further apart.

The tension is genuine. It is the reason to measure rather than assume.

*The project begins with an intuition, but the intuition does not get a vote once the evidence arrives.*

---

## Phase 1: What We Found

Phase 1 implements and validates a public-data CLMX-style three-component variance decomposition across 180 monthly observations from 2010-2024. These statistics validate the Phase 1 measurement framework; they do not test H1.

| Parameter | Value |
|---|---|
| Study window | 2010-2024 (180 months) |
| Universe | Current S&P 500 constituents (backcast) |
| Weighting | Value-weighted, prior-month-end market caps |
| Industry mapping | FF49 (EDGAR SIC crosswalk) |
| Canonical treatment | Option B / `complete_month` |
| Synthetic validation | 24/24 PASS |
| Regression tests | 11/11 PASS |

The decomposition produces two distinct FIRM variance share statistics that must not be conflated:

- **39.95%:** FIRM as a share of total variance, computed as the ratio of summed monthly components across all 180 months (ratio of total-period sums).
- **46.32%:** FIRM as a share of total variance, computed as the arithmetic mean of the monthly FIRM/(MKT+IND+FIRM) ratio across all 180 months (mean of monthly ratios). Higher than the ratio-of-sums because months with low total variance carry disproportionately high FIRM share.

**Survivorship limitation:** The ticker universe is derived from current S&P 500 constituent membership projected backward. Securities that entered and exited the index during 2010-2024 without surviving to the current list are excluded. The direction and magnitude of the resulting survivorship bias on FIRM variance share have not been empirically established for this dataset. No directional claim is made.

Two open methodological decisions were resolved before results were examined. Option B (`complete_month`) is the canonical missing-data treatment; a q_t audit confirmed that Option A and Option B produce numerically identical component totals across all 180 months, so the selection carried no numerical tradeoff. The extended study window 2005-2009 failed the preregistered 85% coverage gate and was rejected. Full adjudication record in `RESEARCH_LOG.md`.

---

## Why Parallax / Research Architecture

Parallax is the apparent shift of an object when viewed from different positions. That shift is not noise; it is information about structure.

The same equity-market outcome looks different depending on the analytical lens. This project moves through a sequence of viewpoints: variance decomposition, dispersion and correlation analysis, Brinson attribution, factor attribution, and residual/specific risk analysis. Only the first lens is complete.

The research questions form a conceptual ladder:

1. **H1 (Structural change):** Does firm-specific variation in the modern sample differ materially from what earlier research established?
2. **H2 (Regime dependence):** Or does observed behavior vary primarily by market regime rather than representing a secular shift?
3. **H3 (Systematic explanation):** If something changed, can changing systematic factor exposures account for it?
4. **H4 (Residual persistence):** After systematic explanations, does meaningful firm-specific variation remain?

None of these has been tested. Phase 2 has not been authorized. H1 uses "differs materially" rather than "increased" because the direction is not assumed. A result consistent with no structural change is a valid and successful outcome of this project.

Four competing explanations are maintained throughout:

| | Explanation | Core claim |
|---|---|---|
| A | Genuine idiosyncratic divergence | Firms increasingly behave differently for firm-specific reasons |
| B | Classification failure | Sector/industry labels increasingly group companies with systematically different exposures |
| C | Regime effects | The apparent pattern is cyclical or conditional, not secular |
| D | Availability bias | Visible large-stock moves create an impression broader data may not support |

Distinguishing among these is the research obligation, not merely identifying the best fit. Full hypothesis treatment and operationalizations are in `PROJECT_CHARTER.md`.

Three related concepts are kept distinct throughout. Dispersion (securities moving apart) does not imply firm-specific causes. Brinson selection effects can arise from systematic factor tilts rather than idiosyncratic returns. Residual/specific return, after controlling for common exposures, is the measure closest to the primary research question. Conflating these determines what evidence can support what conclusion.

---

## Why This Is Harder Than It Looks

A catalogue of issues encountered in Phase 1 that do not appear in the original paper. Full provenance in `RESEARCH_LOG.md`.

- **Survivorship bias:** current S&P 500 membership projected backward excludes companies that entered and exited the index without surviving to the current list; direction and magnitude of the resulting bias on FIRM share have not been empirically established.
- **Point-in-time market-cap weighting:** prior-month-end weights require a daily market-cap series separate from the returns matrix; constructing it from public data requires its own pipeline.
- **SIC to FF49 mapping:** EDGAR SIC codes do not map cleanly to the Fama-French 49-industry scheme; the crosswalk requires adjudication and affects industry attribution.
- **Missing-return conventions:** the original paper does not fully specify how to handle a stock that is eligible for a month but absent on specific trading days; the treatment creates a silent internal consistency requirement across `mu_d`, `r_j`, and `eps`. Getting it wrong understates FIRM.
- **Eligibility vs. daily denominator:** a stock qualifying under a lenient monthly threshold may still be absent on individual trading days; how to treat those days affects component totals and is not resolved in the literature.
- **Data source calendar conventions:** yfinance's exclusive-end convention excludes the last calendar date from the price download; December 31, 2024 (a NYSE trading day) is absent from the cache by API design, not by error.
- **Coverage gate rejection:** the 2005-2009 window was evaluated against a preregistered 85% coverage threshold and rejected; the extension was not applied.
- **Math vs. implementation behavior:** `pandas sum(skipna=True)` is not algebraically equivalent to explicit zero-imputation for all components; it coincidentally produces the same `mu_d` and `r_j` but a different, and incorrect, `eps` for stocks missing on individual days.

---

## Validation and Research Governance

- **Clean-room boundary:** no proprietary data, code, tools, models, or methodology from any employer appears anywhere in this repository; all market data is public (Yahoo Finance / yfinance, Kenneth French Data Library, EDGAR SIC codes).
- **Synthetic known-answer validation:** 24/24 PASS before any live data execution (`diagnostics/wp05_synthetic_validation.py`).
- **Canonical implementation regression tests:** 11/11 PASS, including three tests that directly exercise `decompose_month_clmx()` against analytically derived values (`tests/test_clmx.py`).
- **Preregistered decision gates:** D-018 and D-020 were adjudicated from diagnostic evidence, not from which option produced preferred results.
- **Implementation defect documented and regression-protected:** the Option A latent FIRM understatement was identified, root-caused, repaired, and locked in with regression tests before publication.
- **Rejected extensions documented:** the 2005-2009 coverage failure is recorded in `RESEARCH_LOG.md`, not omitted.
- **Evidence and interpretation kept separate:** empirical statistics, methodology decisions, and interpretive commentary are labeled distinctly throughout the research log.
- **AI collaboration:** Matt owns the research question, methodology, preregistered governance, interpretation, and final judgment. AI tools were used as coding, audit, and adversarial-review collaborators, including surfacing implementation defects and challenging methodology decisions. AI output is not treated as empirical evidence; research conclusions trace to reproducible calculations and verified data.

---

## Roadmap

| Phase | Question | Output | Status |
|---|---|---|---|
| 0 | What is already known? | Literature review | Complete |
| 1 | Can the data answer the question? | Bias and feasibility report | Complete (WP-05) |
| 2 | Does the phenomenon exist? | Dispersion and correlation analysis | Pending gates |
| 3 | Does the attribution engine work? | Brinson engine and tests | Pending gates |
| 4 | What do systematic factors explain? | Factor attribution engine | Pending gates |
| 5 | Where do the frameworks agree and disagree? | Comparative attribution | Pending gates |
| 6 | Has the structure changed through time? | Structural analysis | Pending gates |
| 7 | When does the macro environment matter? | Regime analysis | Future extension |

No phase is treated as mandatory if an earlier gate invalidates its underlying question. Return frequency, universe scope, and final historical horizon remain open pending Phase 2 gate authorization; full detail in `PROJECT_CHARTER.md` Section 11. Phase 2 hypothesis testing has not been authorized and has not begun. The research question remains open in both directions.

---

## Reproduce and Explore

| File | Contents |
|---|---|
| `notebooks/02_historical_replication.ipynb` | Canonical Phase 1 CLMX decomposition |
| `diagnostics/wp05_live_diagnostic.py` | Live data pipeline and `decompose_month_clmx()` |
| `diagnostics/wp05_synthetic_validation.py` | 24-case synthetic validation suite |
| `tests/test_clmx.py` | 11-case regression test suite |
| `RESEARCH_LOG.md` | Complete Phase 1 execution history |
| `PROJECT_CHARTER.md` | Preregistered methodology and hypotheses |

```bash
python diagnostics/wp05_synthetic_validation.py   # 24/24 PASS
pytest tests/test_clmx.py -v                      # 11/11 PASS
```

Live data results require a fresh yfinance download; the decomposition engine and test suites are fully reproducible from this repository.

**Related:** [vd-cloud](https://github.com/MJNolan37/vd-cloud) examines whether volatility and dispersion measures can identify useful market regimes. Project Parallax approaches dispersion from a different direction, asking how changing security differentiation relates to attribution and the systematic versus specific decomposition of returns.

---

[Project Charter](PROJECT_CHARTER.md) · [Research Log](RESEARCH_LOG.md) · [Bibliography](docs/bibliography.md) · [Methodology](docs/methodology.md) · [Live Data Execution](docs/live_data_execution_handoff.md)
