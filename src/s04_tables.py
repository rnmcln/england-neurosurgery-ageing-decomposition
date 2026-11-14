"""
Step 4. Assemble tables.

Components are expressed as a percentage of the baseline-year count. This
denominator is used in preference to the share of net change because net change
can be arbitrarily close to zero, at which point shares of change diverge
without the components themselves being unstable. Shares of net change are not
reported: when demographic and rate components oppose each other they exceed
100 per cent or fall below zero, which invites misreading.

Naming convention. Working tables carry a tab_ prefix and descriptive names.
Numbered publication tables and figures are assembled from them in step 13.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg

PRIMARY_TAG = f"{cfg.COUNT_BASIS}__{cfg.UNKNOWN_AGE_HANDLING}"


def table1_groups(rates):
    rows = []
    for g, spec in cfg.PROCEDURE_GROUPS.items():
        r = rates[rates["group"] == g]
        rows.append(
            {
                "Procedure group": g,
                "OPCS-4 codes": ", ".join(spec["codes"]),
                "n codes": len(spec["codes"]),
                "Count 2012/13": int(round(r[r.fy == 2013]["count"].iloc[0])),
                "Count 2024/25": int(round(r[r.fy == 2025]["count"].iloc[0])),
                "ASR 2012/13": round(r[r.fy == 2013]["asr_per_100k"].iloc[0], 2),
                "ASR 2024/25": round(r[r.fy == 2025]["asr_per_100k"].iloc[0], 2),
                "A priori expectation": spec["prior"],
            }
        )
    return pd.DataFrame(rows)


def tab_decomposition_display_periods(dec):
    """Main decomposition table: the two display periods, components as % of
    baseline. Bootstrap intervals and annualised columns are supplementary."""
    out = []
    sub = dec[dec["period"].isin(cfg.DISPLAY_PERIODS)]
    for _, r in sub.iterrows():
        row = {
            "Procedure group": r["group"],
            "Period": r["period"],
            "Count, start": int(round(r["n1"])),
            "Count, end": int(round(r["n2"])),
            "Net change, n": int(round(r["total_change"])),
            "Net change, %": round(r["pct_change"], 1),
        }
        for k, lab in [
            ("population_size", "Population size"),
            ("age_structure", "Age structure"),
            ("age_specific_rate", "Age-specific rate"),
        ]:
            row[f"{lab}, n"] = int(round(r[k]))
            row[f"{lab}, % of baseline"] = round(r[f"{k}_pct_of_baseline"], 1)
        out.append(row)
    return pd.DataFrame(out)


def tableS2_sensitivity():
    frames = []
    for basis in ["all_procedures", "main_procedure"]:
        for unk in ["proportional", "oldest", "drop"]:
            tag = f"{basis}__{unk}"
            d = pd.read_csv(cfg.DERIVED / f"decomposition_{tag}.csv")
            d = d[d["period"] == cfg.PRIMARY_PERIOD]
            frames.append(
                d.assign(count_basis=basis, unknown_age=unk)[
                    [
                        "group", "count_basis", "unknown_age", "pct_change",
                        "population_size_pct_of_baseline",
                        "age_structure_pct_of_baseline",
                        "age_specific_rate_pct_of_baseline",
                    ]
                ]
            )
    s = pd.concat(frames, ignore_index=True)
    s.columns = [
        "Procedure group", "Count basis", "Unknown-age handling", "Net change, %",
        "Population size, % of baseline", "Age structure, % of baseline",
        "Age-specific rate, % of baseline",
    ]
    for c in s.columns[3:]:
        s[c] = s[c].round(2)
    return s


def tableS3_covid(rates):
    """Fall in recorded activity in 2020/21 relative to 2019/20, by group."""
    rows = []
    for g in cfg.PROCEDURE_GROUPS:
        r = rates[rates["group"] == g].set_index("fy")
        rows.append(
            {
                "Procedure group": g,
                "ASR 2019/20": round(r.loc[2020, "asr_per_100k"], 2),
                "ASR 2020/21": round(r.loc[2021, "asr_per_100k"], 2),
                "Change, %": round(
                    (r.loc[2021, "asr_per_100k"] / r.loc[2020, "asr_per_100k"] - 1)
                    * 100,
                    1,
                ),
                "ASR 2024/25 relative to 2019/20, %": round(
                    (r.loc[2025, "asr_per_100k"] / r.loc[2020, "asr_per_100k"] - 1)
                    * 100,
                    1,
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("Change, %")


def tab_dispersion():
    d = pd.read_csv(cfg.DERIVED / "dispersion.csv").copy()
    d.columns = [
        "Period", "Quantity", "SD between groups, pp", "IQR, pp", "Range, pp",
        "Minimum, %", "Maximum, %",
    ]
    for c in d.columns[2:]:
        d[c] = d[c].round(2)
    return d


def tableS4b_variance():
    v = pd.read_csv(cfg.DERIVED / "variance_decomposition.csv").copy()
    v.columns = [
        "Period", "Variance of net change, pp^2", "SD of net change, pp",
        "Population size share", "Age structure share",
        "Age-specific rate share", "Share sum",
    ]
    for c in v.columns[1:]:
        v[c] = v[c].round(4)
    return v


def tableS13_phases(dec):
    """Decomposition over pre-pandemic, pandemic shock and recovery phases."""
    phases = [
        "Pre-pandemic (2012/13 to 2018/19)",
        "Pandemic shock (2019/20 to 2020/21)",
        "Recovery (2020/21 to 2024/25)",
    ]
    d = dec[dec["period"].isin(phases)][
        ["group", "period", "n1", "n2", "pct_change",
         "population_size_pct_of_baseline", "age_structure_pct_of_baseline",
         "age_specific_rate_pct_of_baseline"]
    ].copy()
    d.columns = [
        "Procedure group", "Phase", "Count, start", "Count, end",
        "Net change, %", "Population size, % of baseline",
        "Age structure, % of baseline", "Age-specific rate, % of baseline",
    ]
    for c in ["Count, start", "Count, end"]:
        d[c] = d[c].round(0).astype(int)
    for c in d.columns[4:]:
        d[c] = d[c].round(1)
    return d


def tableS16_counterfactual():
    cf = pd.read_csv(cfg.DERIVED / "demographic_counterfactual.csv")
    cf = cf[cf["period"].isin(
        ["Pre-pandemic (2012/13 to 2018/19)", cfg.LATER_PERIOD]
    )].copy()
    cf.columns = [
        "Period", "Procedure group", "Demographic counterfactual, %",
        "Combined demographic component (symmetric decomposition), %",
        "Observed net change, %",
    ]
    for c in cf.columns[2:]:
        cf[c] = pd.to_numeric(cf[c]).round(2)
    return cf


def tableS5_shapley():
    s = pd.read_csv(cfg.DERIVED / "shapley_comparison.csv")
    out = s[
        ["group"]
        + [c for c in s.columns if c.endswith(("_kitagawa_pct", "_shapley_pct",
                                               "_abs_diff_pp"))]
    ].copy()
    out.columns = [
        "Procedure group",
        "Population size, Kitagawa %", "Population size, Shapley %",
        "Population size, |difference| pp",
        "Age structure, Kitagawa %", "Age structure, Shapley %",
        "Age structure, |difference| pp",
        "Age-specific rate, Kitagawa %", "Age-specific rate, Shapley %",
        "Age-specific rate, |difference| pp",
    ]
    for c in out.columns[1:]:
        out[c] = out[c].round(3)
    return out


def tableS6_alt_endpoints():
    a = pd.read_csv(cfg.DERIVED / "alternative_endpoints.csv")
    a.columns = [
        "Specification", "Procedure group", "Net change, %",
        "Population size, % of baseline", "Age structure, % of baseline",
        "Age-specific rate, % of baseline",
    ]
    for c in a.columns[2:]:
        a[c] = a[c].round(2)
    return a


def tableS7_cumulative():
    c = pd.read_csv(cfg.DERIVED / "cumulative_annual.csv")
    c.columns = [
        "Procedure group", "Span",
        "Population size, cumulated %", "Age structure, cumulated %",
        "Age-specific rate, cumulated %", "Net change, cumulated %",
    ]
    for col in c.columns[2:]:
        c[col] = c[col].round(2)
    return c



def tab_age_allocation():
    """Where incomplete age allocation is concentrated, from check C2."""
    ch = pd.read_csv(cfg.DERIVED / "build_checks.csv")
    c2 = ch[ch["check"] == "C2_age_allocation"].copy()
    c2["fy"] = c2["metric"].str.extract(r"fy(\d+)").astype(int)
    out = c2.pivot_table(index="group", columns="fy", values="value")
    out.columns = [f"{y-1}/{str(y)[2:]}" for y in out.columns]
    out.insert(0, "Minimum", out.min(axis=1))
    out = out.round(3).reset_index().rename(columns={"group": "Procedure group"})
    return out.sort_values("Minimum")


def tableS17_selected_panel():
    out = pd.read_csv(cfg.DERIVED / "selected_panel_robustness.csv")
    out.columns = [
        "Specification", "Omitted or included groups", "Number of groups",
        "Population size, % of between-group variance",
        "Age structure, % of between-group variance",
        "Age-specific rate, % of between-group variance", "Share sum, %",
    ]
    for column in out.columns[3:]:
        out[column] = (out[column] * 100).round(2)
    return out


def tableS18_stable_codes():
    out = pd.read_csv(cfg.DERIVED / "stable_code_sensitivity.csv")
    keep = [
        "stability_definition", "group", "n_codes_all", "n_codes_stable",
        "excluded_codes",
        "stable_net_change_pct", "stable_population_size_pct",
        "stable_age_structure_pct", "stable_age_specific_rate_pct",
        "difference_population_size_pp", "difference_age_structure_pp",
        "difference_age_specific_rate_pp",
    ]
    out = out[keep]
    out.columns = [
        "Stability definition", "Procedure group", "All codes, n", "Stable codes, n",
        "Excluded codes",
        "Stable-code net change, %", "Stable-code population size, %",
        "Stable-code age structure, %", "Stable-code age-specific rate, %",
        "Stable minus primary population size, pp",
        "Stable minus primary age structure, pp",
        "Stable minus primary age-specific rate, pp",
    ]
    out["Excluded codes"] = out["Excluded codes"].fillna("None")
    for column in out.columns[5:]:
        out[column] = out[column].round(2)
    return out


def tab_projection_per_year():
    out = pd.read_csv(cfg.DERIVED / "projection_per_year_summary.csv")
    out.columns = [
        "Across-group statistic", "Observed age structure, interval-average pp/year",
        "Projected age structure, interval-average pp/year",
        "Observed total demographic, interval-average pp/year",
        "Projected total demographic, interval-average pp/year",
    ]
    for column in out.columns[1:]:
        out[column] = out[column].round(3)
    return out


def main():
    cfg.TABLES.mkdir(parents=True, exist_ok=True)
    dec = pd.read_csv(cfg.DERIVED / f"decomposition_{PRIMARY_TAG}.csv")
    rates = pd.read_csv(cfg.DERIVED / f"rates_{PRIMARY_TAG}.csv")

    tables = {
        "tab_procedure_groups": table1_groups(rates),
        "tab_decomposition_display_periods": tab_decomposition_display_periods(dec),
        "tab_annual_rates": rates.round(3),
        "tab_counting_variants": tableS2_sensitivity(),
        "tab_pandemic_disruption": tableS3_covid(rates),
        "tab_shapley_comparison": tableS5_shapley(),
        "tab_alternative_endpoints": tableS6_alt_endpoints(),
        "tab_cumulative_annual": tableS7_cumulative(),
        "tab_age_allocation": tab_age_allocation(),
        "tab_variance_decomposition": tableS4b_variance(),
        "tab_phase_decomposition": tableS13_phases(dec),
        "tab_demographic_counterfactual": tableS16_counterfactual(),
        "tab_selected_panel_robustness": tableS17_selected_panel(),
        "tab_stable_code_sensitivity": tableS18_stable_codes(),
        "tab_projection_per_year": tab_projection_per_year(),
    }
    for name, t in tables.items():
        t.to_csv(cfg.TABLES / f"{name}.csv", index=False)
        print(f"  {name}.csv  ({len(t)} rows)")


if __name__ == "__main__":
    main()
