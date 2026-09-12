"""
Synthetic test: positive-weight security missing a daily return.
Tests the exact code path of decompose_month_clmx() from wp05_live_diagnostic.py.

Setup:
  2 stocks (A, B), 1 industry (both stocks in it)
  2 trading days (d1, d2)
  Weights: w_A = 0.6, w_B = 0.4  (both positive, prior-month-end)
  Returns:
    d1: r_A = +0.05, r_B = +0.03  (both present)
    d2: r_A = +0.02, r_B = NaN    (stock B missing — positive weight, missing return)

We run THREE calculations:
  (1) Exact diagnostic code path (Option A, skipna default)
  (2) Zero-imputation-throughout (what the docstring implies is intended)
  (3) Observed-only (valid-day-only, what a cleaner "skip" would produce)

Then report whether MKT+IND+FIRM reconciles to each return object.
"""
import numpy as np
import pandas as pd

print("=" * 68)
print("  WP-05 Synthetic Missing-Return Test")
print("  2 stocks · 1 industry · 2 days · stock B missing on day 2")
print("=" * 68)
print()

# ── Setup ─────────────────────────────────────────────────────────────────
dates = pd.to_datetime(["2020-01-02", "2020-01-03"])
tickers = ["A_stk", "B_stk"]

R = pd.DataFrame(
    {"A_stk": [0.05, 0.02], "B_stk": [0.03, np.nan]},
    index=dates,
)

# Prior-month-end VW weights (both positive, renormalised)
W_raw = pd.Series({"A_stk": 0.6, "B_stk": 0.4})
W = W_raw  # already sum to 1.0

# Industry: both stocks in industry 1, W_j = 1.0
W_j = 1.0
w_ij = W / W_j  # within-industry weights

print(f"  Returns matrix:")
print(R.to_string())
print()
print(f"  Weights: A={W['A_stk']:.1f}, B={W['B_stk']:.1f}")
print()

# ── Calculation 1: EXACT DIAGNOSTIC CODE PATH ─────────────────────────────
print("-" * 68)
print("  [1]  EXACT DIAGNOSTIC CODE PATH (wp05_live_diagnostic.py)")
print("-" * 68)

# mu_d: R.mul(W, axis=1).sum(axis=1)  — pandas default skipna=True
mu_d = R.mul(W, axis=1).sum(axis=1)
print(f"  mu_d:")
for dt, v in mu_d.items():
    print(f"    {dt.date()}  {v:.8f}")

MKT_1 = float((mu_d ** 2).sum())

# r_j (1 industry): same as mu_d since W_j = 1.0
r_j = R[tickers].mul(W, axis=1).sum(axis=1)  # same as mu_d here

IND_1 = 0.0
eta_j = r_j - mu_d
print(f"  eta_j (= 0 since 1 industry): {eta_j.tolist()}")
IND_1 = W_j * float((eta_j ** 2).sum())

FIRM_1 = 0.0
for ticker in tickers:
    eps = R[ticker] - r_j
    contrib = W_j * float(w_ij[ticker]) * float((eps ** 2).sum())
    print(f"  eps_{ticker}: {eps.tolist()} → contribution to FIRM: {contrib:.8f}")
    FIRM_1 += contrib

total_1 = MKT_1 + IND_1 + FIRM_1

print()
print(f"  MKT  = {MKT_1:.8f}")
print(f"  IND  = {IND_1:.8f}")
print(f"  FIRM = {FIRM_1:.8f}")
print(f"  SUM  = {total_1:.8f}")

# ── Reference objects ──────────────────────────────────────────────────────

# Reference A: VW sum of squared zero-imputed returns (R_NaN → 0)
R_zero = R.fillna(0.0)
vw_zero = float((R_zero ** 2).mul(W, axis=1).sum().sum())
print()
print(f"  Reference A (VW Σ r² with r_B_d2 = 0): {vw_zero:.8f}")
print(f"  Gap vs zero-imputed: {total_1 - vw_zero:.4e}")

# Reference B: VW sum of squared observed returns only (skip NaN)
vw_obs = float((R ** 2).mul(W, axis=1).sum(skipna=True).sum())
print(f"  Reference B (VW Σ r² observed-only):    {vw_obs:.8f}")
print(f"  Gap vs observed-only: {total_1 - vw_obs:.4e}")


# ── Calculation 2: ZERO IMPUTATION THROUGHOUT ─────────────────────────────
print()
print("-" * 68)
print("  [2]  ZERO IMPUTATION THROUGHOUT (internally consistent)")
print("       r_B_d2 = 0; eps_B_d2 = 0 - r_j_d2 computed, NOT skipped")
print("-" * 68)

R2 = R.fillna(0.0)
mu_d2 = R2.mul(W, axis=1).sum(axis=1)
r_j2  = R2.mul(W, axis=1).sum(axis=1)  # 1 industry
IND_2 = 0.0; FIRM_2 = 0.0

for ticker in tickers:
    eps = R2[ticker] - r_j2
    contrib = W_j * float(w_ij[ticker]) * float((eps ** 2).sum())
    print(f"  eps_{ticker}: {eps.tolist()} → FIRM contribution: {contrib:.8f}")
    FIRM_2 += contrib

MKT_2  = float((mu_d2 ** 2).sum())
total_2 = MKT_2 + IND_2 + FIRM_2

print()
print(f"  MKT  = {MKT_2:.8f}")
print(f"  IND  = {IND_2:.8f}")
print(f"  FIRM = {FIRM_2:.8f}")
print(f"  SUM  = {total_2:.8f}")
print(f"  Reference A (VW Σ r² zero-imputed): {vw_zero:.8f}")
print(f"  Gap: {total_2 - vw_zero:.4e}  (expected: cross-product terms only)")


# ── Calculation 3: OBSERVED-ONLY CONSISTENT ───────────────────────────────
print()
print("-" * 68)
print("  [3]  OBSERVED-ONLY, RENORMALISED (alternative consistent approach)")
print("       On day 2: only stock A is used; weights renormalised to sum=1")
print("-" * 68)

FIRM_3 = 0.0; MKT_3 = 0.0; IND_3 = 0.0

for day_idx in range(len(R)):
    row = R.iloc[day_idx]
    present = row.dropna().index
    W_day = W.reindex(present)
    W_day = W_day / W_day.sum()  # renormalise
    mu = float((row[present] * W_day).sum())
    MKT_3 += mu ** 2
    r_j_day = float((row[present] * W_day).sum())  # 1 industry
    for t in present:
        eps = row[t] - r_j_day
        FIRM_3 += W_j * float(W_day[t]) * eps ** 2

print(f"  MKT  = {MKT_3:.8f}")
print(f"  IND  = {IND_3:.8f}")
print(f"  FIRM = {FIRM_3:.8f}")
print(f"  SUM  = {MKT_3 + IND_3 + FIRM_3:.8f}")
print(f"  Reference B (VW Σ r² observed-only with day-2 renorm weights): different concept")


# ── Diagnosis ─────────────────────────────────────────────────────────────
print()
print("=" * 68)
print("  DIAGNOSIS")
print("=" * 68)
print()
gap_zero = total_1 - vw_zero
firm_delta = FIRM_2 - FIRM_1
print(f"  Gap between [1] (diagnostic) and zero-imputed reference:")
print(f"    {gap_zero:.6e}")
print()
print(f"  This gap equals exactly the missing FIRM term for stock B day 2:")
print(f"    W_j × w_B × (0 - mu_d2)²  =  1.0 × 0.4 × {mu_d.iloc[1]:.6f}² = {0.4 * mu_d.iloc[1]**2:.6e}")
print()
print(f"  FIRM deficit [1] vs [2]: {firm_delta:.6e}")
print(f"  MKT/IND identical across [1] and [2]: MKT delta = {MKT_2-MKT_1:.0e}, IND delta = {IND_2-IND_1:.0e}")
print()
print("  CONCLUSION:")
print("  The diagnostic code path mixes two interpretations:")
print("   • mu_d and r_j:   zero imputation (NaN treated as 0 via skipna=True)")
print("   • eps and FIRM:   observed-only   (NaN skipped in eps = R[t] - r_j)")
print()
print("  For zero-imputation to be internally consistent, eps for a missing stock")
print("  should be computed as 0 - r_j (not NaN - r_j), and its squared term")
print("  included in FIRM. The current code does NOT do this.")
print()
print("  FIRM is therefore understated by exactly:")
print("    Σ_{(i,d): i positive-wt, d missing} W_j × w_ij × (r_j_d)²")
print()
print("  This is a CODE DEFECT relative to the stated 'zero imputation' intent,")
print("  not a methodology ambiguity. Fixing it is deterministic: impute r=0")
print("  for missing stocks consistently throughout (mu_d, r_j, AND eps).")
print()
print("  IMPACT ON CURRENT CACHED RESULTS: zero.")
print("  All positive-weight A-exclusive stocks have zero prior-month-end weight;")
print("  the defective FIRM branch is never reached with positive W in this cache.")
print()
print("  REQUIRED ACTION:")
print("  This is a code correction, not a new methodology decision.")
print("  It should be registered as a defect in the next CHANGELOG entry and")
print("  fixed before any future run in which Option A produces positive-weight")
print("  partial stock-months (e.g., if historical membership data is added).")
print("  No D-018 adjudication is blocked by it today.")

# ── Pandas version ─────────────────────────────────────────────────────────
print()
print("-" * 68)
print(f"  pandas version: {pd.__version__}")
print(f"  pct_change() fill_method default in this version:")
try:
    import inspect
    sig = inspect.signature(pd.DataFrame.pct_change)
    fill_param = sig.parameters.get('fill_method', None)
    if fill_param is not None:
        print(f"    fill_method default = {fill_param.default!r}")
    else:
        print("    fill_method parameter not found in signature")
except Exception as e:
    print(f"    could not inspect: {e}")
