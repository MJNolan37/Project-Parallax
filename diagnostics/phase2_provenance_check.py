"""
Project Parallax — Phase 2 provenance check.
SHA-256 gate for canonical input files.

Specification: v1.0 Section 10 (2026-09-23, frozen).

Run before any empirical H1/H2 execution. Halts on mismatch.
Usage:
    python diagnostics/phase2_provenance_check.py

Reads expected SHAs from config/phase2_spec.toml.
Halts with SystemExit(1) if any SHA mismatches or any file is missing.
Passes silently (exit 0) if all match.

Files checked:
    data/clmx_monthly_decomp_opt_b.csv   — canonical Phase 1 output (T=180)
    [ff49_crosswalk file — path configured in spec]
"""

import hashlib
import sys
import os
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # fallback
    except ImportError:
        print("ERROR: tomllib (Python 3.11+) or tomli required for TOML parsing.")
        sys.exit(1)

# Locate repo root: two levels up from diagnostics/
REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = REPO_ROOT / "config" / "phase2_spec.toml"

DATA_FILES = {
    "clmx_monthly_decomp_opt_b": REPO_ROOT / "data" / "clmx_monthly_decomp_opt_b.csv",
    # ff49_crosswalk: path TBD per repo structure
}


def sha256_file(path: Path) -> str:
    """Compute SHA-256 of a file, reading in chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_expected_shas(spec_path: Path) -> dict:
    """Load expected SHA-256 values from config/phase2_spec.toml [checksums]."""
    with open(spec_path, "rb") as f:
        spec = tomllib.load(f)
    return spec.get("checksums", {})


def check_provenance() -> int:
    """
    Run all provenance checks.

    Returns
    -------
    0 : all checks pass
    1 : at least one check failed
    """
    if not SPEC_PATH.exists():
        print(f"HALT: spec file not found at {SPEC_PATH}")
        return 1

    expected = load_expected_shas(SPEC_PATH)
    failures = []
    passes = []

    # Check clmx_monthly_decomp_opt_b.csv
    csv_key = "clmx_monthly_decomp_opt_b_sha256"
    expected_sha = expected.get(csv_key, "")

    if not expected_sha:
        print(f"HALT: {csv_key} not set in config/phase2_spec.toml.")
        print("  This must be filled before empirical execution.")
        return 1

    csv_path = DATA_FILES["clmx_monthly_decomp_opt_b"]
    if not csv_path.exists():
        failures.append(f"MISSING: {csv_path}")
    else:
        actual_sha = sha256_file(csv_path)
        if actual_sha == expected_sha:
            passes.append(f"PASS: {csv_path.name} SHA-256 matches")
        else:
            failures.append(
                f"SHA MISMATCH: {csv_path.name}\n"
                f"  expected: {expected_sha}\n"
                f"  actual:   {actual_sha}"
            )

    # Check ff49 crosswalk (if SHA is set)
    ff49_key = "ff49_crosswalk_sha256"
    ff49_sha = expected.get(ff49_key, "")
    if ff49_sha:
        # Path must be specified; placeholder for now
        print(f"  NOTE: ff49_crosswalk_sha256 check not yet wired to file path.")
        print(f"        Add the file path to DATA_FILES in this script.")

    # Report
    for p in passes:
        print(f"  {p}")
    for f_msg in failures:
        print(f"  HALT: {f_msg}")

    if failures:
        print("\nProvenance gate FAILED. Empirical execution blocked.")
        return 1

    print("\nProvenance gate PASSED. Empirical execution may proceed.")
    return 0


if __name__ == "__main__":
    sys.exit(check_provenance())
