# Project Parallax — Methodology Notes

*Working document for methodological decisions and rationale. Updated as research progresses.*

---

## Factor Baseline

**Decision:** Fama-French Five Factors + Momentum (FF6)

**Factors:**
- **Mkt-RF** — Market excess return
- **SMB** — Small minus big (size)
- **HML** — High minus low (value)
- **RMW** — Robust minus weak (profitability)
- **CMA** — Conservative minus aggressive (investment)
- **Mom** — Momentum (UMD)

**Source:** Kenneth French Data Library
**URL:** https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html

**Rationale:** Publicly accessible, academically established, independently reproducible. Provides a sufficient breadth of systematic controls for initial testing. Not treated as a complete model of security returns.

**Constraint:** Additional factors may be introduced only when supported by a documented research reason. The baseline is not upgraded opportunistically.

---

## Brinson Attribution Framework

**Validation approach:** Controlled synthetic portfolios with known expected attribution before applying the engine to empirical portfolios.

See `tests/test_brinson.py` for known-answer test cases.

**Attribution components:**
- Allocation effect
- Selection effect
- Interaction effect

**Key conceptual distinction:** Brinson selection is a portfolio attribution construct. It does not imply that the attributed return was idiosyncratic. A security that outperformed its sector benchmark may have done so because of systematic factor exposures, not firm-specific behavior.

**Primary comparative question:** What changes when the same portfolio return is viewed through Brinson attribution versus factor attribution? The differences between the two frameworks may reveal structural information that neither framework exposes on its own. This comparative question is a primary research output of Phases 3–5.

---

## Residual Return — Model Dependence

**Design requirement:** Residual or specific return means unexplained by the specified factor model — not inherently or purely firm-specific in an economic sense. Omitted factors inflate measured residual variance. The H1 test therefore measures whether residual variance as a share of total variance has changed under a specified model, not whether some quantity of "pure idiosyncrasy" has changed.

Sensitivity testing across at least two model specifications is planned for Phase 5 to assess how model choice affects residual estimates.

---

## Dispersion Normalization

**Design requirement:** Raw cross-sectional dispersion is mechanically elevated during periods of high aggregate market volatility. All dispersion measures must be presented alongside volatility-normalized equivalents to separate structural changes from regime changes.

---

## Survivorship Bias

**Design requirement:** Current S&P 500 constituents are not equivalent to historical point-in-time constituents. Using only current constituents creates a sample composed exclusively of companies that survived — distorting historical dispersion, correlation, and attribution estimates.

**Survivorship filter as explicit architectural node:** The pipeline explicitly projects current S&P 500 membership backward into historical periods. This filter must be documented as a named architectural step — not buried in a data-loading comment — because its presence shapes every downstream estimate. Historical FIRM variance is understated relative to a full-universe panel because distressed companies (higher idiosyncratic volatility) are excluded. Phase 1 (`notebooks/01_data_validation.ipynb`) contains the formal bias diagnostic.

The data pipeline monitors and documents survivorship exposure throughout. No result is considered mature until the survivorship implications have been reviewed.

---

## CLMX Variance Decomposition

**Implementation reference:** Campbell, Lettau, Malkiel & Xu (2001), *Journal of Finance* 56(1); confirmed in Campbell, Lettau, Malkiel & Xu (2022), NBER WP 29916.

**Confirmed estimator (CLMX 2022, Figure notes 1–4):**

Monthly variance for each component is the sum of raw squared daily return components within the month:

$$\text{MKT}_t = \sum_d \mu_{t,d}^2 \qquad \text{IND}_t = \sum_j W_j \sum_d \eta_{j,d}^2 \qquad \text{FIRM}_t = \sum_j W_j \sum_{i \in j} w_{ij} \sum_d \varepsilon_{i,d}^2$$

- Returns are NOT demeaned before squaring
- Monthly totals are NOT divided by trading-day count
- Value-weighted primary (D-019); both VW and EW reported in CLMX (2022)

**FF49 industry classification:** Fama-French 49 industries (not 48 — confirmed in CLMX 2001 paper text). SIC codes sourced from SEC EDGAR public API. SIC → FF49 mapping via the Kenneth French Data Library crosswalk (Siccodes49.zip). SIC retrieval date, source endpoint, and crosswalk version are recorded in the notebook for reproducibility. Modern S&P 500 companies sometimes file under legacy SIC codes; mismatches are flagged.

**VW weight convention:** Prior-month-end market-cap weights. Weights held fixed for the calendar month. Approximate market cap = price × current shares outstanding (shares are a static proxy; documented limitation for companies with significant share-count changes).

**Observation rules (registered design choices, not CLMX requirements):**
- D-017: Minimum 10 valid daily return observations per stock per month
- D-018: OPEN — comparison between complete-month completeness (Option B, preferred) and valid-day inclusion (Option A). Decision pending review of FIRM variance overlay chart in `notebooks/02_historical_replication.ipynb`, Step 8.

**CLMX FIRM variance vs. Factor-model residual variance:** These are distinct measures. CLMX FIRM variance removes market and industry components only — it is not factor-controlled. It will be elevated relative to the FF6-residual variance computed in Phase 5 (Layer 5), which also removes size, value, profitability, investment, and momentum exposures. Code and documentation maintain this distinction explicitly: `FIRM` for the CLMX component, `residual_variance` / `specific_variance_share` for the FF6 residual.

---

*Methodology decisions are registered in the Decision Register (internal) and summarized here for public reference.*
