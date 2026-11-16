"""
Step 14. Recorded expectations, Poisson variation and denominator timing.

Three supplementary analyses of the primary specification (all procedure
positions, proportional redistribution of unallocated age):

1. Expectations and components (derived/expectation_outcomes.csv).
   For 2012/13 to 2018/19, the expectation recorded for each group before the
   decomposition was calculated ("demographic", "rate" or "mixed", see
   config.PROCEDURE_GROUPS) is set against the decomposition. The comparison
   rule was defined after the decomposition had been calculated: change is
   called demographic-dominated when the demographic component (population
   size plus age structure) exceeds the age-specific rate component in
   absolute value, and rate-dominated otherwise. The file also records the
   identity behind the population-size component,

       population size / N1 = g (1 + R2/R1) / 2,   g = P2/P1 - 1,

   so that its variation between groups is shown to arise only from the
   group's change in crude rate R.

2. Poisson variation (derived/poisson_intervals.csv).
   Every component of the decomposition, and every directly standardised
   rate, is a linear function of the age-band counts once populations are
   fixed. Treating each age-band count as an independent Poisson variable
   with variance equal to the count gives exact variances without
   simulation. Intervals for the rate components are normal (+/- 1.96 SE);
   intervals for age-standardised rates use the gamma method of Fay and
   Feuer (1997). Codes recorded more than once for the same patient or
   episode make the counts overdispersed relative to Poisson, so these
   intervals are lower bounds on random variation. They do not represent
   coding, definition or age-allocation uncertainty, which the sensitivity
   analyses address.

3. Denominator timing (derived/denominator_timing.csv).
   The primary analysis matches the financial year ending in March of year Y
   to the mid-year (30 June) estimate for Y-1, three months before the
   financial-year midpoint. The sensitivity analysis instead interpolates
   each age band to 1 October of Y-1, as 0.75 x mid-(Y-1) + 0.25 x mid-Y.
   Mid-2025 estimates are not part of the data, so the comparison covers the
   primary period 2012/13 to 2018/19 only.

Deterministic: no random numbers are drawn.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg

PRIMARY_TAG = f"{cfg.COUNT_BASIS}__{cfg.UNKNOWN_AGE_HANDLING}"
GROUPS = list(cfg.PROCEDURE_GROUPS)
Z = 1.959963984540054


def band_of(age):
    if age == 0:
        return "0"
    if age < 5:
        return "1-4"
    if age >= 90:
        return "90+"
    lo = (age // 5) * 5
    return f"{lo}-{lo + 4}"


def mye_bands():
    m = pd.read_csv(cfg.RAW / "ons_mye_england_sya.csv")
    m["age"] = m["C_AGE_NAME"].str.extract(r"(\d+)").astype(int)
    m["band"] = m["age"].map(band_of)
    return m.groupby(["DATE_NAME", "band"])["OBS_VALUE"].sum()


def components(n1, p1, n2, p2):
    """Three components as counts; arrays aligned on age band."""
    P1, P2 = p1.sum(), p2.sum()
    c1, c2 = p1 / P1, p2 / P2
    m1, m2 = n1 / p1, n2 / p2
    R1, R2 = (c1 * m1).sum(), (c2 * m2).sum()
    pop = (P2 - P1) * (R1 + R2) / 2
    age = (P1 + P2) / 2 * ((c2 - c1) * (m1 + m2) / 2).sum()
    rate = (P1 + P2) / 2 * ((m2 - m1) * (c1 + c2) / 2).sum()
    return pop, age, rate, R1, R2, P1, P2


def component_se(n1, p1, n2, p2):
    """Poisson standard errors of the three components (counts).

    Each component is sum_a (u_a n1_a + v_a n2_a); its Poisson variance is
    sum_a (u_a^2 n1_a + v_a^2 n2_a).
    """
    P1, P2 = p1.sum(), p2.sum()
    c1, c2 = p1 / P1, p2 / P2
    # population size: (P2 - P1)/2 * (sum c1 n1/p1 + sum c2 n2/p2); c/p = 1/P
    u_pop = (P2 - P1) / 2 / P1 * np.ones_like(n1)
    v_pop = (P2 - P1) / 2 / P2 * np.ones_like(n2)
    # age structure: (P1 + P2)/4 * sum (c2 - c1)(n1/p1 + n2/p2)
    k = (P1 + P2) / 4 * (c2 - c1)
    u_age, v_age = k / p1, k / p2
    # age-specific rate: (P1 + P2)/4 * sum (c1 + c2)(n2/p2 - n1/p1)
    h = (P1 + P2) / 4 * (c1 + c2)
    u_rate, v_rate = -h / p1, h / p2
    out = []
    for u, v in [(u_pop, v_pop), (u_age, v_age), (u_rate, v_rate)]:
        out.append(np.sqrt((u ** 2 * n1).sum() + (v ** 2 * n2).sum()))
    return out


def asr_fay_feuer(n, pop, std):
    """Directly standardised rate per 100,000 with Fay-Feuer 95% interval."""
    w = std / std.sum() / pop * 1e5
    y = (w * n).sum()
    v = (w ** 2 * n).sum()
    wm = w.max()
    lo = v / (2 * y) * chi2.ppf(0.025, 2 * y ** 2 / v) if y > 0 else 0.0
    hi = (v + wm ** 2) / (2 * (y + wm)) * chi2.ppf(0.975, 2 * (y + wm) ** 2 / (v + wm ** 2))
    return y, lo, hi


def main():
    a = pd.read_csv(cfg.DERIVED / f"analysis_{PRIMARY_TAG}.csv")
    a["band"] = pd.Categorical(a["band"], cfg.AGE_BANDS, ordered=True)
    a = a.sort_values(["group", "fy", "band"])
    dec = pd.read_csv(cfg.DERIVED / f"decomposition_{PRIMARY_TAG}.csv")
    bp = mye_bands()
    std = (a[a["fy"] == cfg.STANDARD_POP_MYE_YEAR + 1]
           .drop_duplicates("band").set_index("band")["population"]
           .reindex(cfg.AGE_BANDS).to_numpy(float))

    def series(g, fy):
        d = a[(a["group"] == g) & (a["fy"] == fy)].set_index("band").reindex(cfg.AGE_BANDS)
        return d["count"].to_numpy(float), d["population"].to_numpy(float)

    def interp_pop(fy):
        y = cfg.fy_to_mye(fy)
        return (0.75 * bp.loc[y].reindex(cfg.AGE_BANDS)
                + 0.25 * bp.loc[y + 1].reindex(cfg.AGE_BANDS)).to_numpy(float)

    f1, f2 = cfg.PERIODS[cfg.PRIMARY_PERIOD]
    l1, l2 = cfg.PERIODS[cfg.LATER_PERIOD]
    exp_rows, pois_rows, timing_rows = [], [], []
    for g in GROUPS:
        n1, p1 = series(g, f1)
        n2, p2 = series(g, f2)
        N1 = n1.sum()
        pop, age, rate, R1, R2, P1, P2 = components(n1, p1, n2, p2)
        demo = pop + age
        growth = P2 / P1 - 1
        prior = cfg.PROCEDURE_GROUPS[g]["prior"]
        dominant = "demographic" if abs(demo) > abs(rate) else "rate"
        exp_rows.append({
            "group": g,
            "expectation": prior,
            "net_pct": (n2.sum() - N1) / N1 * 100,
            "demographic_pct": demo / N1 * 100,
            "population_size_pct": pop / N1 * 100,
            "age_structure_pct": age / N1 * 100,
            "age_specific_rate_pct": rate / N1 * 100,
            "dominant_component": dominant,
            "expectation_met": (dominant == prior) if prior != "mixed" else np.nan,
            "population_growth_pct": growth * 100,
            "crude_rate_ratio": R2 / R1,
            "population_size_identity_pct": growth * (1 + R2 / R1) / 2 * 100,
        })

        se_pre = component_se(n1, p1, n2, p2)
        m1_, q1 = series(g, l1)
        m2_, q2 = series(g, l2)
        _, _, rate_l, *_ = components(m1_, q1, m2_, q2)
        se_lat = component_se(m1_, q1, m2_, q2)
        row = {"group": g}
        for fy in (f1, f2, l2):
            n, p = series(g, fy)
            y, lo, hi = asr_fay_feuer(n, p, std)
            row[f"asr_{fy}"], row[f"asr_{fy}_lo"], row[f"asr_{fy}_hi"] = y, lo, hi
        for tag, r, se, base in [("pre", rate, se_pre[2], N1),
                                 ("later", rate_l, se_lat[2], m1_.sum())]:
            row[f"rate_{tag}_pct"] = r / base * 100
            row[f"rate_{tag}_se_pct"] = se / base * 100
            row[f"rate_{tag}_lo_pct"] = (r - Z * se) / base * 100
            row[f"rate_{tag}_hi_pct"] = (r + Z * se) / base * 100
        row["pop_pre_se_pct"] = se_pre[0] / N1 * 100
        row["age_pre_se_pct"] = se_pre[1] / N1 * 100
        pois_rows.append(row)

        ip1, ip2 = interp_pop(f1), interp_pop(f2)
        ipop, iage, irate, *_ = components(n1, ip1, n2, ip2)
        timing_rows.append({
            "group": g,
            "population_size_pct": pop / N1 * 100,
            "population_size_interp_pct": ipop / N1 * 100,
            "age_structure_pct": age / N1 * 100,
            "age_structure_interp_pct": iage / N1 * 100,
            "age_specific_rate_pct": rate / N1 * 100,
            "age_specific_rate_interp_pct": irate / N1 * 100,
        })

    exp = pd.DataFrame(exp_rows)
    pois = pd.DataFrame(pois_rows)
    tim = pd.DataFrame(timing_rows)

    # agreement with the main decomposition
    pre = dec[dec["period"] == cfg.PRIMARY_PERIOD].set_index("group").loc[GROUPS]
    gap = max(
        (exp.set_index("group")["population_size_pct"] - pre["population_size_pct_of_baseline"]).abs().max(),
        (exp.set_index("group")["age_structure_pct"] - pre["age_structure_pct_of_baseline"]).abs().max(),
        (exp.set_index("group")["age_specific_rate_pct"] - pre["age_specific_rate_pct_of_baseline"]).abs().max(),
    )
    print(f"  components agree with step 3 to {gap:.1e} percentage points")
    ident = (exp["population_size_identity_pct"] - exp["population_size_pct"]).abs().max()
    print(f"  population-size identity holds to {ident:.1e} percentage points")

    # variance shares with interpolated denominators
    def shares(df, p, ag, rt):
        Y = df[p] + df[ag] + df[rt]
        return [df[c].cov(Y) / Y.var() * 100 for c in (p, ag, rt)]

    sm = shares(tim, "population_size_pct", "age_structure_pct", "age_specific_rate_pct")
    si = shares(tim, "population_size_interp_pct", "age_structure_interp_pct",
                "age_specific_rate_interp_pct")
    tim_summary = pd.DataFrame({
        "group": ["Share of between-group variance, %"],
        "population_size_pct": [sm[0]], "population_size_interp_pct": [si[0]],
        "age_structure_pct": [sm[1]], "age_structure_interp_pct": [si[1]],
        "age_specific_rate_pct": [sm[2]], "age_specific_rate_interp_pct": [si[2]],
    })
    tim = pd.concat([tim, tim_summary], ignore_index=True)

    exp.to_csv(cfg.DERIVED / "expectation_outcomes.csv", index=False)
    pois.to_csv(cfg.DERIVED / "poisson_intervals.csv", index=False)
    tim.to_csv(cfg.DERIVED / "denominator_timing.csv", index=False)
    print("  expectation_outcomes.csv, poisson_intervals.csv, denominator_timing.csv written")


if __name__ == "__main__":
    main()
