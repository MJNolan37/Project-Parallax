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

---

## Dispersion Normalization

**Design requirement:** Raw cross-sectional dispersion is mechanically elevated during periods of high aggregate market volatility. All dispersion measures must be presented alongside volatility-normalized equivalents to separate structural changes from regime changes.

---

## Survivorship Bias

**Design requirement:** Current S&P 500 constituents are not equivalent to historical point-in-time constituents. Using only current constituents creates a sample composed exclusively of companies that survived — distorting historical dispersion, correlation, and attribution estimates.

The data pipeline monitors and documents survivorship exposure throughout. No result is considered mature until the survivorship implications have been reviewed.

---

*Methodology decisions are registered in the Decision Register (internal) and summarized here for public reference.*
