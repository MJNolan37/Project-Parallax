# Project Parallax — Live Data Execution Handoff

**Issued:** 2026-08-25  
**For:** Local execution of `notebooks/02_historical_replication.ipynb` (Phase 1 / WP-05 live pass)  
**Prerequisite:** v0.1.4 committed and clean working tree confirmed

---

## Context

The CLMX variance decomposition engine has passed 24/24 synthetic validation tests (WP-05). The notebook implementation is correct mathematically. The next task is to run the notebook against live historical data to produce the first empirical output of the project.

Live execution requires network access to three external sources:
- **Yahoo Finance** (via `yfinance`) — daily return data for S&P 500 constituents
- **SEC EDGAR API** — historical SIC codes for FF49 industry classification
- **Kenneth French Data Library** — FF6 factor data and Siccodes49 SIC crosswalk

These sources are blocked in the cloud environment. All live execution must happen on your local machine.

---

## Setup

### 1. Confirm environment

```bash
cd /path/to/project-parallax
git log --oneline -3          # should show 1a0bfd3 v0.1.4 at HEAD
git status                    # should be clean
python --version              # 3.9+ required
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
# or if using a virtual environment:
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Verify network access before opening the notebook

```bash
python -c "import yfinance; t = yfinance.Ticker('AAPL'); print(t.info.get('shortName', 'CHECK FAILED'))"
python -c "import requests; r = requests.get('https://efts.sec.gov/LATEST/search-index?q=%22AAPL%22&dateRange=custom&startdt=2010-01-01&enddt=2010-01-31', timeout=10); print(r.status_code)"
python -c "import requests; r = requests.get('https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html', timeout=10); print(r.status_code)"
```

All three should succeed before proceeding.

### 4. Launch the notebook

```bash
jupyter notebook notebooks/02_historical_replication.ipynb
```

---

## Execution Order

Run steps in sequence. Do **not** skip ahead. Each step produces output that the next step depends on.

| Step | Title | Expected Output | Decision Required |
|---|---|---|---|
| 1 | Mathematical framework | Decomposition identity printed | None |
| 2 | Raw data inspection | Coverage heatmap; missingness summary; D-020 range diagnostic | **See Decision 1 below** |
| 3 | Industry classification | FF49 SIC crosswalk loaded; EDGAR SIC snapshot retrieved | Populate `SIC_SNAPSHOT_META['retrieval_date']` with today's date |
| 4 | Weight construction | Prior-month-end VW weights computed | None |
| 5 | MKT component | Market variance component computed for one sample month | None |
| 6 | IND component | Industry variance component computed for one sample month | None |
| 7 | FIRM component | Residual variance computed; MKT + IND + FIRM ≈ total | None |
| 8 | Full period + D-018 | Full 2010–2024 time series; Option A vs Option B overlay | **See Decision 2 below** |
| 9 | Reconciliation | Per-month n_stocks chart; non-negativity assertion | None |
| 10 | Visualization | FIRM variance share series; directional comparison to CLMX (2022) | None |
| 11 | Limitations | Documented by priority | None |
| 12 | Function definitions | (Reference only — all functions appear here for the notebook) | None |

---

## Decision Capture Points

### Decision 1 — D-020: Study Window Confirmation or Extension

**Where:** Step 2, after coverage heatmap renders

**What to look at:** The coverage diagnostic shows the fraction of S&P 500 constituents with retrievable price history by year. Focus on 2005–2009.

**Criteria for extension to 2005–2024:**
- Coverage rate ≥ 85% in every year 2005–2009
- No evidence of systematic survivorship distortion in pre-2010 data (i.e., companies that delisted in 2005–2009 are still retrievable, not silently missing)
- The survivorship-exposure metric (fraction of historical panel composed exclusively of current constituents) remains at an acceptable level

**If criteria are met:** D-020 can be extended to 2005–2024. Record the extension in `RESEARCH_LOG.md` with the diagnostic evidence. Update `STUDY_START` in the notebook imports cell to `'2005-01-01'`.

**If criteria are not met:** Keep 2010–2024. Document the specific coverage failure in `RESEARCH_LOG.md`.

**Do not extend the window to produce more data without this diagnostic gate.**

---

### Decision 2 — D-018: Missing Data Treatment (Option A vs Option B)

**Where:** Step 8, D-018 overlay chart

**What to look at:** The overlay chart shows all three CLMX components (MKT, IND, FIRM) and universe composition under Option A (valid-day inclusion, VW portfolio composition changes day-by-day) vs Option B (complete-month basket, fixed for the month). WP-05 synthetic validation showed a 21.79% MKT-level gap and a 2.09% FIRM-level gap between the options on synthetic data. Live data may behave differently.

**D-018 adjudication requires evaluating two dimensions together:**

*Methodological defensibility:* Option A allows the VW portfolio composition to change day-by-day within each month, meaning a stock entering or exiting valid-return status mid-month shifts its weight. Option B fixes the basket at month open, producing a stable within-month universe at the cost of excluding companies whose data arrives or drops mid-month. Neither is definitively correct — the choice must be justified on the grounds of which construction more faithfully represents the CLMX estimator intent and the research question, not on which produces a cleaner series.

*Empirical sensitivity:* Examine MKT, IND, and FIRM component shares separately under both options. Also examine (a) the distribution of universe size (n_stocks per month) under each option, and (b) the missingness pattern — whether the stocks excluded under Option B cluster by sector, size, or time period in ways that would bias composition. If the options diverge materially on any component, not just FIRM, or if the universe-composition difference is systematic rather than random, that is relevant evidence for the adjudication.

**Register the decision in `RESEARCH_LOG.md` as D-018 ACCEPTED (Option A) or D-018 ACCEPTED (Option B), with the methodological rationale stated explicitly and the empirical sensitivity across all three components summarised.**

**Do not resolve D-018 based on which option produces a more favorable FIRM variance trend. Do not adopt Option A as a default on the basis of the WP-05 synthetic sensitivity result alone — that result is a prior on synthetic data, not a finding on the live series.**

---

## What to Record After Execution

After running the full notebook, add an entry to `RESEARCH_LOG.md` with the following:

1. **Execution date and environment** (local machine, Python version, yfinance version)
2. **SIC snapshot retrieval date** (populate `SIC_SNAPSHOT_META['retrieval_date']` in Step 3)
3. **Coverage diagnostic result** (D-020 confirmation or extension, with evidence)
4. **D-018 resolution** (Option A or Option B, with visual evidence summary)
5. **FIRM variance share: qualitative description** (rising / flat / declining / regime-dependent) — this is the WP-05 empirical replication result and may inform later research design decisions, but is not entered as Parallax H1 evidence; WP-05 remains methodology and replication validation
6. **Directional comparison to CLMX (2022)** — does the 2010–2024 FIRM series broadly track Figures 2–4 from NBER WP 29916 for the overlapping period? This is a replication sanity check, not a test of H1.
7. **Any anomalies or data quality flags** encountered during execution
8. **Next question** per the standard research log format

---

## What NOT to Do During This Pass

- **Do not begin Phase 2** (dispersion/correlation analysis) before the Phase 1 feasibility gate is recorded.
- **Do not resolve D-018 based on which option produces a more interesting trend.**
- **Do not extend D-020 without the Step 2 coverage diagnostic evidence.**
- **Do not commit notebook outputs** with all cells executed — the notebook cells are intentionally clean in the repository. If you want to preserve a specific run, save the rendered HTML via `File → Download as → HTML` and keep it locally; do not commit executed notebook state.
- **Do not treat the directional comparison to CLMX (2022) as a hypothesis test.** It is a sanity check that the engine is producing plausible results, not a test of H1.

---

## If Data Quality Problems Are Found

The project has documented escalation paths. Revisit `PROJECT_CHARTER.md` §10 and `RESEARCH_LOG.md`. If yfinance data materially distorts inference (e.g., consistent coverage below 80%, systematic missing histories for companies that delisted before 2020), document the failure specifically and evaluate the escalation candidate: **Sharadar / Nasdaq Data Link**.

Discovering that a dataset cannot answer the question reliably is itself a research result. Do not work around a material data problem — document it.

---

## Files Modified by Live Execution

| File | Change |
|---|---|
| `notebooks/02_historical_replication.ipynb` | `SIC_SNAPSHOT_META['retrieval_date']` populated in Step 3 |
| `RESEARCH_LOG.md` | New entry: execution date, D-018/D-020 decisions, WP-05 replication results |

No other files should be modified during the live execution pass.

---

*Handoff issued 2026-08-25. Commit HEAD at issuance: 1a0bfd3 (v0.1.4).*
