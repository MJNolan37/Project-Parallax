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

The data pipeline monitors and documents survivorship exposure throughout. No result is considered mature until the survivorship implications have been reviewed.

---

*Methodology decisions are registered in the Decision Register (internal) and summarized here for public reference.*
