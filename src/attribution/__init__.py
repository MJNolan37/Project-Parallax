"""
Project Parallax — Attribution Package
=======================================

This package implements the two primary attribution frameworks used in
Project Parallax: Brinson holdings-based attribution and Fama-French
factor-based attribution.

The frameworks answer different questions and are intentionally kept
conceptually distinct:

    Brinson attribution — describes active return through portfolio hierarchy
        (allocation vs. selection within groups).

    Factor attribution — describes return through modeled systematic exposures
        (what portion of return is explained by known risk factors).

They are complementary descriptions of return, not competing scorecards.
Comparing what each framework reveals — and where they diverge — is one of
the project's primary research objectives.

Modules
-------
brinson
    Brinson-Fachler attribution engine with known-answer validation.
factors
    Fama-French FF6 factor attribution engine.
"""
