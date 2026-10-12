/*
 * Project Parallax A1 UDmax core computation (C extension via cffi/ctypes)
 * supF(0|1), supF(0|2) for Bai-Perron Wiener-process limiting law
 *
 * Compiled with: gcc -O3 -march=native -ffast-math -shared -fPIC
 */

#include <float.h>
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/*
 * Compute UDmax(M=2) = max(supF01, supF02) for each path.
 *
 * z          : (n_paths * T) row-major float64 array of iid N(0,1)
 * n_paths    : number of Monte Carlo paths
 * T          : grid points (Wiener process steps)
 * tau_min    : minimum segment length = ceil(eps * T)
 * result     : (n_paths,) float64 output
 */
void compute_udmax_m2(
    const double* z,
    int n_paths,
    int T,
    int tau_min,
    double* result
) {
    int p;
    #pragma omp parallel for schedule(static) private(p)
    for (p = 0; p < n_paths; p++) {
        const double* zp = z + (size_t)p * T;

        /* Compute cumulative sum S[0..T] */
        double* S = (double*)malloc((T + 1) * sizeof(double));
        S[0] = 0.0;
        int t;
        for (t = 0; t < T; t++) S[t+1] = S[t] + zp[t];
        double ST = S[T];
        double ST2T = ST * ST / T;

        /* supF(0|1): max over tau in [tau_min, T-tau_min] */
        double supf1 = -DBL_MAX;
        for (t = tau_min; t <= T - tau_min; t++) {
            double St = S[t];
            double d2 = ST - St;
            double v = St * St / t + d2 * d2 / (T - t) - ST2T;
            if (v > supf1) supf1 = v;
        }

        /* supF(0|2): max over admissible (tau1, tau2) pairs */
        double supf2 = -DBL_MAX;
        int tau1, tau2;
        for (tau1 = tau_min; tau1 <= T - 2 * tau_min; tau1++) {
            double St1 = S[tau1];
            double a1  = St1 * St1 / tau1;
            for (tau2 = tau1 + tau_min; tau2 <= T - tau_min; tau2++) {
                double St2  = S[tau2];
                double d12  = St2 - St1;
                double d2T  = ST  - St2;
                double v = a1
                         + d12 * d12 / (tau2 - tau1)
                         + d2T * d2T / (T - tau2)
                         - ST2T;
                if (v > supf2) supf2 = v;
            }
        }

        /* supF(0|2) = (1/2) * raw: divide by m=2 for F-form normalization */
        double supf2_f = supf2 / 2.0;
        result[p] = (supf1 > supf2_f) ? supf1 : supf2_f;
        free(S);
    }
}

/*
 * UDmax(M=M_max) via nested DP, for benchmark.
 * M_max <= 8.
 */
#define MAX_M 8

void compute_udmax_Mmax(
    const double* z,
    int n_paths,
    int T,
    int tau_min,
    int M_max,
    double* result
) {
    int Tp1 = T + 1;

    int p;
    #pragma omp parallel for schedule(static) private(p)
    for (p = 0; p < n_paths; p++) {
        /* Per-path private allocations (thread-safe) */
        double* S   = (double*)malloc(Tp1 * sizeof(double));
        double* dp  = (double*)malloc(Tp1 * sizeof(double));
        double* dp2 = (double*)malloc(Tp1 * sizeof(double));

        const double* zp = z + (size_t)p * T;

        /* Cumulative sum */
        S[0] = 0.0;
        int t;
        for (t = 0; t < T; t++) S[t+1] = S[t] + zp[t];
        double ST = S[T];
        double ST2T = ST * ST / T;

        /* Level 1: dp[t] = S[t]^2 / t */
        for (t = 0; t < Tp1; t++) dp[t] = -DBL_MAX;
        for (t = tau_min; t <= T - tau_min; t++) dp[t] = S[t] * S[t] / t;

        double best = -DBL_MAX;
        for (t = tau_min; t <= T - tau_min; t++) {
            double d = ST - S[t];
            double v = dp[t] + d * d / (T - t) - ST2T;
            if (v > best) best = v;
        }

        int m;
        for (m = 2; m <= M_max; m++) {
            int t_lo = m * tau_min;
            int t_hi = T - tau_min;
            int s_lo_base = (m - 1) * tau_min;

            for (t = 0; t < Tp1; t++) dp2[t] = -DBL_MAX;

            for (t = t_lo; t <= t_hi; t++) {
                int s_hi = t - tau_min;
                double best_inner = -DBL_MAX;
                int s;
                for (s = s_lo_base; s <= s_hi; s++) {
                    if (dp[s] <= -DBL_MAX * 0.5) continue;
                    double ds = S[t] - S[s];
                    double v  = dp[s] + ds * ds / (t - s);
                    if (v > best_inner) best_inner = v;
                }
                dp2[t] = best_inner;
            }

            /* supF(0|m) = (1/m) * raw functional: divide by m for F-form */
            for (t = t_lo; t <= t_hi; t++) {
                if (dp2[t] <= -DBL_MAX * 0.5) continue;
                double d = ST - S[t];
                double v = (dp2[t] + d * d / (T - t) - ST2T) / m;
                if (v > best) best = v;
            }

            /* swap dp and dp2 */
            double* tmp = dp; dp = dp2; dp2 = tmp;
        }

        result[p] = best;
        free(S); free(dp); free(dp2);
    }
}
