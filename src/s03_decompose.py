"""
Step 3. Decompose change in recorded procedure counts.

Notation for a procedure group in year t:
    P_t        total England population
    c_{a,t}    share of the population in age band a, so that sum_a c = 1
    m_{a,t}    recorded procedures per person in band a
    R_t        = sum_a c_{a,t} m_{a,t}, the crude rate
    N_t        = P_t R_t, the recorded count

The change in count between two years is separated into three additive parts
by nesting two symmetric (Kitagawa 1955) two-factor decompositions:

    N_2 - N_1 = (P_2 - P_1) (R_1 + R_2)/2                          population size
              + (P_1 + P_2)/2 * sum_a (c_{a,2} - c_{a,1}) mbar_a   age structure
              + (P_1 + P_2)/2 * sum_a (m_{a,2} - m_{a,1}) cbar_a   age-specific rate

with mbar_a = (m_{a,1} + m_{a,2})/2 and cbar_a = (c_{a,1} + c_{a,2})/2. The
identity is exact: the three parts sum to N_2 - N_1 with no residual, because
the symmetric form absorbs the interaction term equally between factors. The
allocation of that interaction is a convention, not an estimate.

Interpretation. The age-structure part is what would have happened had
age-specific recording rates been fixed at their period average and only the
age composition moved. The rate part is everything else that operates within
age bands: incidence, referral, thresholds for operating, coding depth,
service capacity. It is a residual in the causal sense and should not be read
as clinical incidence.

Uncertainty. Administrative counts are close to complete enumerations of
recorded activity, so no sampling-based intervals are computed. The relevant
uncertainties (coding practice, classification change, age allocation,
endpoint choice and group definition) are examined by the sensitivity
analyses in steps 2, 3, 11 and 12.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg


def three_factor(n1, n2, pop1, pop2):
    """Decompose the change in total count between two years.

    Parameters are band-aligned arrays of counts and populations.
    Returns a dict of the three components and the total change.
    """
    n1, n2 = np.asarray(n1, float), np.asarray(n2, float)
    pop1, pop2 = np.asarray(pop1, float), np.asarray(pop2, float)

    P1, P2 = pop1.sum(), pop2.sum()
    c1, c2 = pop1 / P1, pop2 / P2
    m1, m2 = n1 / pop1, n2 / pop2
    R1, R2 = float((c1 * m1).sum()), float((c2 * m2).sum())

    mbar, cbar, Pbar = (m1 + m2) / 2, (c1 + c2) / 2, (P1 + P2) / 2

    pop_size = (P2 - P1) * (R1 + R2) / 2
    age_struct = Pbar * float(((c2 - c1) * mbar).sum())
    age_rate = Pbar * float(((m2 - m1) * cbar).sum())

    return {
        "n1": float(n1.sum()),
        "n2": float(n2.sum()),
        "total_change": float(n2.sum() - n1.sum()),
        "crude_rate_1": R1 * 1e5,
        "crude_rate_2": R2 * 1e5,
        "population_size": pop_size,
        "age_structure": age_struct,
        "age_specific_rate": age_rate,
        "closure_error": float(n2.sum() - n1.sum())
        - (pop_size + age_struct + age_rate),
    }


def shapley_three_factor(n1, n2, pop1, pop2):
    """Three-factor Shapley decomposition of the change in total count.

    The symmetric (Kitagawa-type) decomposition in three_factor() is exact but
    allocates interaction terms by one convention among several. The Shapley
    decomposition averages the marginal contribution of each factor over all
    six orders in which population size P, age composition c and age-specific
    rates m can move from their first-year to their second-year values. It is
    likewise exact and additive, and serves as a sensitivity analysis for the
    allocation of interactions.
    """
    from itertools import permutations

    n1, n2 = np.asarray(n1, float), np.asarray(n2, float)
    pop1, pop2 = np.asarray(pop1, float), np.asarray(pop2, float)

    P = {0: pop1.sum(), 1: pop2.sum()}
    c = {0: pop1 / pop1.sum(), 1: pop2 / pop2.sum()}
    m = {0: n1 / pop1, 1: n2 / pop2}

    def N(state):
        return P[state["P"]] * float((c[state["c"]] * m[state["m"]]).sum())

    contrib = {"P": 0.0, "c": 0.0, "m": 0.0}
    orders = list(permutations(["P", "c", "m"]))
    for order in orders:
        state = {"P": 0, "c": 0, "m": 0}
        for f in order:
            before = N(state)
            state[f] = 1
            contrib[f] += (N(state) - before) / len(orders)

    return {
        "population_size_shapley": contrib["P"],
        "age_structure_shapley": contrib["c"],
        "age_specific_rate_shapley": contrib["m"],
        "shapley_closure_error": float(n2.sum() - n1.sum())
        - (contrib["P"] + contrib["c"] + contrib["m"]),
    }


def age_standardised(n, pop, std_pop):
    """Directly age-standardised rate per 100,000 using a fixed standard."""
    m = np.asarray(n, float) / np.asarray(pop, float)
    w = np.asarray(std_pop, float)
    return float((m * w).sum() / w.sum() * 1e5)



def run(dataset_path, tag):
    df = pd.read_csv(dataset_path)
    df["band"] = pd.Categorical(df["band"], categories=cfg.AGE_BANDS, ordered=True)

    # Standard population for age-standardised rates: England mid-2012.
    std = (
        df[df["mye_year"] == min(cfg.MYE_YEARS)]
        .drop_duplicates("band")
        .sort_values("band")["population"]
        .to_numpy()
    )

    rows, asr_rows = [], []
    for group in cfg.PROCEDURE_GROUPS:
        g = df[df["group"] == group]

        for fy, sub in g.groupby("fy"):
            sub = sub.sort_values("band")
            asr_rows.append(
                {
                    "group": group,
                    "fy": fy,
                    "count": sub["count"].sum(),
                    "crude_per_100k": sub["count"].sum()
                    / sub["population"].sum() * 1e5,
                    "asr_per_100k": age_standardised(
                        sub["count"], sub["population"], std
                    ),
                }
            )

        for period, (y1, y2) in cfg.PERIODS.items():
            a = g[g["fy"] == y1].sort_values("band")
            b = g[g["fy"] == y2].sort_values("band")
            if a.empty or b.empty:
                continue
            d = three_factor(
                a["count"], b["count"], a["population"], b["population"]
            )
            d |= {
                "group": group,
                "period": period,
                "fy1": y1,
                "fy2": y2,
                "prior": cfg.PROCEDURE_GROUPS[group]["prior"],
                "years": y2 - y1,
            }
            d["pct_change"] = d["total_change"] / d["n1"] * 100
            for k in ["population_size", "age_structure", "age_specific_rate"]:
                d[f"{k}_pct_of_baseline"] = d[k] / d["n1"] * 100
                d[f"{k}_share_of_change"] = (
                    d[k] / d["total_change"] * 100
                    if abs(d["total_change"]) > 0
                    else np.nan
                )
            d["demographic_share"] = (
                (d["population_size"] + d["age_structure"]) / d["total_change"] * 100
                if abs(d["total_change"]) > 0
                else np.nan
            )
            rows.append(d)

    dec = pd.DataFrame(rows)
    asr = pd.DataFrame(asr_rows)
    dec.to_csv(cfg.DERIVED / f"decomposition_{tag}.csv", index=False)
    asr.to_csv(cfg.DERIVED / f"rates_{tag}.csv", index=False)
    return dec, asr


def _bands(df, group, fys):
    """Band-aligned mean counts and populations over one or more years."""
    g = df[(df["group"] == group) & (df["fy"].isin(fys))]
    n = g.groupby("band", observed=True)["count"].mean().reindex(cfg.AGE_BANDS)
    p = g.groupby("band", observed=True)["population"].mean().reindex(cfg.AGE_BANDS)
    return n.to_numpy(), p.to_numpy()


def shapley_comparison(df):
    """Kitagawa against Shapley allocation, primary period, all groups."""
    y1, y2 = cfg.PERIODS[cfg.PRIMARY_PERIOD]
    rows = []
    for group in cfg.PROCEDURE_GROUPS:
        n1, p1 = _bands(df, group, [y1])
        n2, p2 = _bands(df, group, [y2])
        k = three_factor(n1, n2, p1, p2)
        s = shapley_three_factor(n1, n2, p1, p2)
        row = {"group": group, "baseline": k["n1"]}
        for comp, skey in [
            ("population_size", "population_size_shapley"),
            ("age_structure", "age_structure_shapley"),
            ("age_specific_rate", "age_specific_rate_shapley"),
        ]:
            row[f"{comp}_kitagawa_pct"] = k[comp] / k["n1"] * 100
            row[f"{comp}_shapley_pct"] = s[skey] / k["n1"] * 100
            row[f"{comp}_abs_diff_pp"] = abs(
                row[f"{comp}_kitagawa_pct"] - row[f"{comp}_shapley_pct"]
            )
        row["shapley_closure_error"] = s["shapley_closure_error"]
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(cfg.DERIVED / "shapley_comparison.csv", index=False)
    return out


def alternative_endpoints(df):
    """Endpoint sensitivity for the pre-pandemic contrast.

    Three specifications: the primary 2012/13 to 2018/19 contrast, the same
    contrast ending 2019/20, and three-year averages at either end. Each is a
    full three-factor decomposition expressed as a percentage of its baseline.
    """
    specs = [
        ("Primary (2012/13 to 2018/19)", [2013], [2019]),
        ("Alternative endpoint (2012/13 to 2019/20)", [2013], [2020]),
        (
            cfg.ENDPOINT_AVERAGES["label"],
            cfg.ENDPOINT_AVERAGES["start_fys"],
            cfg.ENDPOINT_AVERAGES["end_fys"],
        ),
    ]
    rows = []
    for label, fys1, fys2 in specs:
        for group in cfg.PROCEDURE_GROUPS:
            n1, p1 = _bands(df, group, fys1)
            n2, p2 = _bands(df, group, fys2)
            d = three_factor(n1, n2, p1, p2)
            rows.append(
                {
                    "specification": label,
                    "group": group,
                    "net_change_pct": d["total_change"] / d["n1"] * 100,
                    "population_size_pct": d["population_size"] / d["n1"] * 100,
                    "age_structure_pct": d["age_structure"] / d["n1"] * 100,
                    "age_specific_rate_pct": d["age_specific_rate"] / d["n1"] * 100,
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(cfg.DERIVED / "alternative_endpoints.csv", index=False)
    return out


def cumulative_annual(df):
    """Consecutive-year decompositions cumulated over the pre-pandemic span.

    Tests whether the endpoint contrast is a stable feature of the period:
    components from each pair of consecutive years are summed and expressed as
    a percentage of the span's baseline count, alongside the endpoint result.
    """
    y_start, y_end = cfg.CUMULATE_SPAN
    rows = []
    for group in cfg.PROCEDURE_GROUPS:
        n0, _ = _bands(df, group, [y_start])
        base = n0.sum()
        acc = {"population_size": 0.0, "age_structure": 0.0,
               "age_specific_rate": 0.0, "total_change": 0.0}
        for y in range(y_start, y_end):
            n1, p1 = _bands(df, group, [y])
            n2, p2 = _bands(df, group, [y + 1])
            d = three_factor(n1, n2, p1, p2)
            for k in acc:
                acc[k] += d[k]
        rows.append(
            {"group": group, "span": f"{y_start-1}/{str(y_start)[2:]} to "
                                     f"{y_end-1}/{str(y_end)[2:]}"}
            | {f"{k}_cumulated_pct": v / base * 100 for k, v in acc.items()}
        )
    out = pd.DataFrame(rows)
    out.to_csv(cfg.DERIVED / "cumulative_annual.csv", index=False)
    return out


def variance_decomposition(dec):
    """Exact decomposition of between-group variance in net change.

    Because Y_g = P_g + A_g + R_g exactly for every group, the across-group
    variance of net change decomposes exactly as
    Var(Y) = Cov(P, Y) + Cov(A, Y) + Cov(R, Y). Each covariance term is
    reported as a share of Var(Y). Component standard deviations are
    descriptive quantities and are not additive; this decomposition, not the
    SDs, carries the attribution claim.
    """
    rows = []
    for period in cfg.PERIODS:
        d = dec[dec["period"] == period]
        if d.empty:
            continue
        Y = d["pct_change"]
        V = Y.var(ddof=1)
        shares = {}
        for comp in ["population_size", "age_structure", "age_specific_rate"]:
            X = d[f"{comp}_pct_of_baseline"]
            shares[comp] = float(np.cov(X, Y, ddof=1)[0, 1] / V)
        rows.append(
            {"period": period, "var_net_change_pp2": V,
             "sd_net_change_pp": float(np.sqrt(V))}
            | {f"{k}_share": v for k, v in shares.items()}
            | {"share_sum": sum(shares.values())}
        )
    out = pd.DataFrame(rows)
    out.to_csv(cfg.DERIVED / "variance_decomposition.csv", index=False)
    return out


def demographic_counterfactual(df, dec):
    """Genuine demographic counterfactual per group and period.

    N(P2, c2, m1) - N(P1, c1, m1): the change that would have occurred had
    the population changed as observed while age-specific rates stayed at
    their baseline values. This is distinct from the sum of the two
    demographic components of the symmetric decomposition, which allocate
    interaction terms; both are reported, with the observed change, so the
    two can be compared. Correlations with observed change are descriptive.
    """
    rows = []
    for period, (y1, y2) in cfg.PERIODS.items():
        pre = dec[dec["period"] == period].set_index("group")
        if pre.empty:
            continue
        for group in cfg.PROCEDURE_GROUPS:
            a = df[(df["group"] == group) & (df["fy"] == y1)].set_index("band")
            b = df[(df["group"] == group) & (df["fy"] == y2)].set_index("band")
            m1 = a["count"] / a["population"]
            cf = float((m1 * b["population"]).sum() - a["count"].sum())
            base = a["count"].sum()
            rows.append(
                {
                    "period": period,
                    "group": group,
                    "counterfactual_pct": cf / base * 100,
                    "decomposition_demographic_pct": float(
                        pre.loc[group, "population_size_pct_of_baseline"]
                        + pre.loc[group, "age_structure_pct_of_baseline"]
                    ),
                    "observed_pct": float(pre.loc[group, "pct_change"]),
                }
            )
    out = pd.DataFrame(rows)
    corr_rows = []
    for period, d in out.groupby("period"):
        corr_rows.append(
            {
                "period": period,
                "group": "(correlation with observed, Pearson)",
                "counterfactual_pct": d["counterfactual_pct"].corr(d["observed_pct"]),
                "decomposition_demographic_pct": d[
                    "decomposition_demographic_pct"
                ].corr(d["observed_pct"]),
                "observed_pct": np.nan,
            }
        )
        corr_rows.append(
            {
                "period": period,
                "group": "(correlation with observed, Spearman)",
                "counterfactual_pct": d["counterfactual_pct"].corr(
                    d["observed_pct"], method="spearman"
                ),
                "decomposition_demographic_pct": d[
                    "decomposition_demographic_pct"
                ].corr(d["observed_pct"], method="spearman"),
                "observed_pct": np.nan,
            }
        )
    out = pd.concat([out, pd.DataFrame(corr_rows)], ignore_index=True)
    out.to_csv(cfg.DERIVED / "demographic_counterfactual.csv", index=False)
    return out


def dispersion(dec):
    """Between-group dispersion of net change and of each component.

    Standard deviation, interquartile range and range across the twelve
    groups, per component. These are descriptive; SDs are not additive and
    carry no attribution claim, which belongs to variance_decomposition().
    """
    rows = []
    for period in cfg.PERIODS:
        d = dec[dec["period"] == period]
        if d.empty:
            continue
        cols = {
            "net_change": d["pct_change"],
            "population_size": d["population_size_pct_of_baseline"],
            "age_structure": d["age_structure_pct_of_baseline"],
            "age_specific_rate": d["age_specific_rate_pct_of_baseline"],
        }
        for name, s in cols.items():
            rows.append(
                {
                    "period": period,
                    "quantity": name,
                    "sd_between_groups_pp": s.std(ddof=1),
                    "iqr_pp": s.quantile(0.75) - s.quantile(0.25),
                    "range_pp": s.max() - s.min(),
                    "min_pct": s.min(),
                    "max_pct": s.max(),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(cfg.DERIVED / "dispersion.csv", index=False)
    return out


def main():
    primary_tag = f"{cfg.COUNT_BASIS}__{cfg.UNKNOWN_AGE_HANDLING}"
    dec, asr = run(
        cfg.DERIVED / f"analysis_{primary_tag}.csv", primary_tag
    )
    worst = dec["closure_error"].abs().max()
    print(f"  primary decomposition written; max closure error = {worst:.3e}")

    for basis in ["all_procedures", "main_procedure"]:
        for unk in ["proportional", "oldest", "drop"]:
            tag = f"{basis}__{unk}"
            if tag == primary_tag:
                continue
            run(cfg.DERIVED / f"analysis_{tag}.csv", tag)
    print("  sensitivity decompositions written")

    df = pd.read_csv(cfg.DERIVED / f"analysis_{primary_tag}.csv")
    sh = shapley_comparison(df)
    print(
        "  shapley_comparison.csv; max |Kitagawa - Shapley| = "
        f"{sh[[c for c in sh.columns if c.endswith('_abs_diff_pp')]].max().max():.3f} pp"
    )
    alternative_endpoints(df)
    print("  alternative_endpoints.csv")
    cumulative_annual(df)
    print("  cumulative_annual.csv")
    dispersion(dec)
    print("  dispersion.csv")
    vd = variance_decomposition(dec)
    p = vd[vd["period"] == cfg.PRIMARY_PERIOD].iloc[0]
    print(
        "  variance_decomposition.csv; primary-period shares: rate "
        f"{p['age_specific_rate_share']*100:.1f}%, size "
        f"{p['population_size_share']*100:.1f}%, structure "
        f"{p['age_structure_share']*100:.1f}%"
    )
    demographic_counterfactual(df, dec)
    print("  demographic_counterfactual.csv")


if __name__ == "__main__":
    main()
