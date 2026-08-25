# Project Parallax — Bibliography

*Literature under review for Phase 0 reconnaissance. Annotations will be added as sources are assessed.*

Status indicators:
- 🔄 Under review
- ✅ Reviewed and annotated
- ⚠️ Flagged for follow-up

---

## Foundational Papers — Idiosyncratic Volatility

**Campbell, J. Y., Lettau, M., Malkiel, B. G., & Xu, Y. (2001)**
*Have Individual Stocks Become More Volatile? An Empirical Exploration of Idiosyncratic Risk.*
Journal of Finance, 56(1), 1–43.
Status: ✅ — Primary methodology source. Three-component variance decomposition (MKT/IND/FIRM) using daily returns aggregated to monthly variance estimates; FF49 industry classification; full CRSP universe; value-weighted primary. Foundational finding: FIRM variance rose secularly over 1962–1997. Methodology confirmed via the authors' own 2022 restatement (see below). Implemented in `notebooks/02_historical_replication.ipynb`.

**Campbell, J. Y., Lettau, M., Malkiel, B. G., & Xu, Y. (2022)**
*Idiosyncratic Equity Risk Two Decades Later.*
NBER Working Paper No. 29916. https://www.nber.org/system/files/working_papers/w29916/w29916.pdf
Status: ✅ — **Primary post-2001 benchmark.** Self-replication and extension by the original authors using identical methodology through 2021. Confirms estimator: "Monthly variances are the sum of daily squared returns within a month." Reports both VW and EW versions. Key post-2001 finding: no persistent secular increase in FIRM variance share; market and industry components elevated post-crisis. Figures 2, 3, and 4 are the primary directional comparison targets for Project Parallax's 2010–2024 replication.

---

## Post-2001 Idiosyncratic Volatility Literature

**Brandt, M. W., Brav, A., Graham, J. R., & Kumar, A. (2010)**
*The Idiosyncratic Volatility Puzzle: Time Trend or Speculative Episodes?*
Review of Financial Studies, 23(2), 863–899.
Status: ✅ — Argues the post-2001 FIRM variance decline is attributable to the end of a speculative retail episode rather than a secular reversal. Sample extends through approximately 2003. Relevant to Explanation C (regime effects). Methodologically independent of CLMX authors.

**Chiah, M., Gharghori, P., & Zhong, A. (2020)**
*Has Idiosyncratic Volatility Increased? Not in Recent Times.*
Critical Finance Review.
Status: ✅ — **Secondary robustness benchmark.** Independent (non-CLMX-author) replication extending to 2016–2017. Confirms no persistent increase in FIRM variance share post-2001. Useful as adversarial check on primary CLMX (2022) benchmark because it is methodologically independent. Relevant to H0.

---

## Cross-Sectional Dispersion Literature

*(Entries to be added as Phase 0 reconnaissance proceeds.)*

Literature targets:
- Cross-sectional equity dispersion measures and their behavior across market regimes
- Dispersion vs. aggregate volatility normalization studies
- Within-sector and within-industry correlation literature

---

## Brinson Attribution Methodology

*(Entries to be added as Phase 3 attribution work begins.)*

Literature targets:
- Brinson, Hood, Beebower (1986) — original Brinson attribution framework
- Brinson, Singer, Beebower (1991) — extension
- Menchero-Davis bridge (Brinson as factor-model special case)

---

## Factor Attribution

*(Entries to be added as Phase 4 work begins.)*

Literature targets:
- Fama, French (1993) — three-factor model
- Fama, French (2015) — five-factor model
- Carhart (1997) — momentum factor
- Fama, French Data Library documentation

---

## Sector Classification

*(Entries to be added as needed.)*

Literature targets:
- GICS vs. SIC classification comparisons
- Industry classification explanatory power for return comovement
- Sector reclassification effects on return attribution

---

*Bibliography grows through Phase 0. All entries are independently assessed; no source is treated as authoritative without review.*

*Phase 0 literature reconnaissance supported by AI-assisted search, August 2026. Primary sources independently verified.*
