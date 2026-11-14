"""Step 12. Panel, weighting, code-set and projection sensitivity analyses.

This step examines three features of the comparative result:

1. the dependence of the signed covariance shares on the selected twelve-group
   panel, equal group weighting and percentage-change scale;
2. the effect of excluding constituent OPCS-4 codes that are not observed in
   every study year; and
3. the distinction between the level and the between-group dispersion of
   observed and projected demographic contributions per year of interval.

The stable-code analysis is an empirical sensitivity analysis. Absence from the
source table may mean that a code was unavailable, unused or recorded as zero;
it does not replace documentary review of OPCS-4 release files.
"""

from itertools import combinations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg
from s02_build import load_breakdowns, load_population
from s03_decompose import three_factor


PRIMARY_TAG = f"{cfg.COUNT_BASIS}__{cfg.UNKNOWN_AGE_HANDLING}"
COMPONENTS = ["population_size", "age_structure", "age_specific_rate"]


def covariance_shares(d, percentage=True, weights=None):
    """Signed covariance contributions to the variance of net change."""
    if d["group"].duplicated().any():
        raise ValueError("each procedure group must appear once")
    if percentage:
        y = d["pct_change"].to_numpy(float)
        xs = [d[f"{component}_pct_of_baseline"].to_numpy(float) for component in COMPONENTS]
    else:
        y = d["total_change"].to_numpy(float)
        xs = [d[component].to_numpy(float) for component in COMPONENTS]

    if weights is None:
        weights = np.ones(len(d), dtype=float)
    weights = np.asarray(weights, dtype=float)
    if not np.isfinite(weights).all() or (weights < 0).any() or weights.sum() <= 0:
        raise ValueError("weights must be finite, non-negative and have positive sum")
    weights = weights / weights.sum()

    y_mean = np.sum(weights * y)
    variance = np.sum(weights * (y - y_mean) ** 2)
    if variance <= 0:
        raise ValueError("net-change variance must be positive")

    shares = {}
    for component, x in zip(COMPONENTS, xs):
        x_mean = np.sum(weights * x)
        covariance = np.sum(weights * (x - x_mean) * (y - y_mean))
        shares[component] = covariance / variance
    return shares | {"share_sum": sum(shares.values())}


def selected_panel_robustness():
    primary = pd.read_csv(cfg.DERIVED / f"decomposition_{PRIMARY_TAG}.csv")
    primary = primary[primary["period"] == cfg.PRIMARY_PERIOD].reset_index(drop=True)
    rows = []

    def add(specification, d, percentage=True, weights=None, omitted_group=""):
        shares = covariance_shares(d, percentage=percentage, weights=weights)
        rows.append(
            {
                "specification": specification,
                "omitted_group": omitted_group,
                "n_groups": len(d),
                "population_size_share": shares["population_size"],
                "age_structure_share": shares["age_structure"],
                "age_specific_rate_share": shares["age_specific_rate"],
                "share_sum": shares["share_sum"],
            }
        )

    add("Primary: equal-weight percentage change", primary)

    for group in primary["group"]:
        add(
            "Leave one group out",
            primary[primary["group"] != group],
            omitted_group=group,
        )

    add(
        "Baseline-volume-weighted percentage change",
        primary,
        weights=primary["n1"],
    )
    add("Equal-weight absolute count change", primary, percentage=False)

    stable_path = cfg.DERIVED / "stable_code_sensitivity.csv"
    if stable_path.exists():
        stable = pd.read_csv(stable_path)
        for definition, data in stable.groupby("stability_definition", sort=False):
            d = pd.DataFrame(
                {
                    "group": data["group"],
                    "n1": data["stable_baseline_count"],
                    "pct_change": data["stable_net_change_pct"],
                    "population_size_pct_of_baseline": data["stable_population_size_pct"],
                    "age_structure_pct_of_baseline": data["stable_age_structure_pct"],
                    "age_specific_rate_pct_of_baseline": data[
                        "stable_age_specific_rate_pct"
                    ],
                }
            )
            add(f"Stable-code sensitivity: {definition}", d)

    for basis in ["all_procedures", "main_procedure"]:
        for unknown in ["proportional", "oldest", "drop"]:
            tag = f"{basis}__{unknown}"
            d = pd.read_csv(cfg.DERIVED / f"decomposition_{tag}.csv")
            d = d[d["period"] == cfg.PRIMARY_PERIOD]
            add(f"Counting variant: {tag}", d)

    subset_rows = []
    for indices in combinations(range(len(primary)), len(primary) // 2):
        d = primary.iloc[list(indices)]
        shares = covariance_shares(d)
        subset_rows.append(
            (
                shares["age_specific_rate"],
                "; ".join(d["group"]),
                d,
            )
        )
    for label, item in [
        ("Six-group subsets: minimum rate share", min(subset_rows, key=lambda x: x[0])),
        ("Six-group subsets: maximum rate share", max(subset_rows, key=lambda x: x[0])),
    ]:
        _, groups, d = item
        add(label, d, omitted_group=f"Included: {groups}")

    subset_rate_shares = np.array([item[0] for item in subset_rows])
    for label, quantile in [
        ("Six-group subset rate-share 5th percentile", 0.05),
        ("Six-group subset rate-share median", 0.50),
        ("Six-group subset rate-share 95th percentile", 0.95),
    ]:
        rows.append(
            {
                "specification": label,
                "omitted_group": "",
                "n_groups": len(primary) // 2,
                "population_size_share": np.nan,
                "age_structure_share": np.nan,
                "age_specific_rate_share": float(np.quantile(subset_rate_shares, quantile)),
                "share_sum": np.nan,
            }
        )

    out = pd.DataFrame(rows)
    out.to_csv(cfg.DERIVED / "selected_panel_robustness.csv", index=False)
    return out


def stable_code_sensitivity():
    breakdowns = load_breakdowns()
    population = load_population()
    years = list(range(min(cfg.MYE_YEARS) + 1, max(cfg.MYE_YEARS) + 2))
    code_to_group = {
        code: group
        for group, specification in cfg.PROCEDURE_GROUPS.items()
        for code in specification["codes"]
    }
    selected_codes = set(code_to_group)
    totals_rows = breakdowns[
        breakdowns["breakdown"].eq("all_procedures")
        & breakdowns["opcs4_code"].isin(selected_codes)
    ]
    source_years = sorted(totals_rows["fy"].unique())
    if source_years != years:
        raise ValueError(f"source years {source_years} do not match expected {years}")
    present = set(zip(totals_rows["opcs4_code"], totals_rows["fy"]))

    coverage_rows = []
    stable_codes_full = set()
    stable_codes_primary = set()
    primary_start, primary_end = cfg.PERIODS[cfg.PRIMARY_PERIOD]
    primary_years = list(range(primary_start, primary_end + 1))
    for code in sorted(selected_codes):
        missing_years = [year for year in years if (code, year) not in present]
        missing_primary_years = [
            year for year in primary_years if (code, year) not in present
        ]
        if not missing_years:
            stable_codes_full.add(code)
        if not missing_primary_years:
            stable_codes_primary.add(code)
        coverage_rows.append(
            {
                "group": code_to_group[code],
                "opcs4_code": code,
                "present_all_years": not missing_years,
                "n_missing_years": len(missing_years),
                "missing_financial_year_end": ";".join(map(str, missing_years)),
                "present_primary_window": not missing_primary_years,
                "n_missing_primary_years": len(missing_primary_years),
                "missing_primary_financial_year_end": ";".join(
                    map(str, missing_primary_years)
                ),
            }
        )
    coverage = pd.DataFrame(coverage_rows)
    coverage.to_csv(cfg.DERIVED / "code_coverage.csv", index=False)

    main = pd.read_csv(cfg.DERIVED / f"decomposition_{PRIMARY_TAG}.csv")
    main = main[main["period"] == cfg.PRIMARY_PERIOD].set_index("group")
    y1, y2 = cfg.PERIODS[cfg.PRIMARY_PERIOD]
    rows = []
    for definition, stable_codes in [
        ("Present in every study year", stable_codes_full),
        ("Present throughout primary window", stable_codes_primary),
    ]:
        stable = breakdowns[breakdowns["opcs4_code"].isin(stable_codes)].copy()
        stable["group"] = stable["opcs4_code"].map(code_to_group)
        totals = (
            stable[stable["breakdown"].eq("all_procedures")]
            .groupby(["group", "fy"], as_index=True)["usage"]
            .sum()
        )
        ages = stable[stable["breakdown"].isin(cfg.BREAKDOWN_TO_BAND)].copy()
        ages["band"] = ages["breakdown"].map(cfg.BREAKDOWN_TO_BAND)
        counts = ages.groupby(["group", "fy", "band"], as_index=True)["usage"].sum()
        complete_index = pd.MultiIndex.from_product(
            [list(cfg.PROCEDURE_GROUPS), years, cfg.AGE_BANDS],
            names=["group", "fy", "band"],
        )
        counts = counts.reindex(complete_index, fill_value=0).rename("usage").reset_index()
        age_totals = counts.groupby(["group", "fy"], as_index=True)["usage"].sum()
        inflation = (totals / age_totals).rename("inflation").reset_index()
        counts = counts.merge(inflation, on=["group", "fy"], validate="many_to_one")
        counts["count"] = counts["usage"] * counts["inflation"]
        counts["mye_year"] = counts["fy"].map(cfg.fy_to_mye)
        counts = counts.merge(
            population, on=["mye_year", "band"], how="left", validate="many_to_one"
        )
        if counts["population"].isna().any():
            raise ValueError("stable-code sensitivity has unmatched population rows")

        for group, specification in cfg.PROCEDURE_GROUPS.items():
            g = counts[counts["group"] == group]
            a = g[g["fy"] == y1].set_index("band").reindex(cfg.AGE_BANDS)
            b = g[g["fy"] == y2].set_index("band").reindex(cfg.AGE_BANDS)
            result = three_factor(
                a["count"], b["count"], a["population"], b["population"]
            )
            excluded = [code for code in specification["codes"] if code not in stable_codes]
            row = {
                "stability_definition": definition,
                "group": group,
                "n_codes_all": len(specification["codes"]),
                "n_codes_stable": len(specification["codes"]) - len(excluded),
                "excluded_codes": "; ".join(excluded) or "None",
                "stable_baseline_count": result["n1"],
                "stable_net_change_pct": result["total_change"] / result["n1"] * 100,
                "stable_closure_error": result["closure_error"],
            }
            for component in COMPONENTS:
                stable_pct = result[component] / result["n1"] * 100
                main_pct = main.loc[group, f"{component}_pct_of_baseline"]
                row[f"stable_{component}_pct"] = stable_pct
                row[f"main_{component}_pct"] = main_pct
                row[f"difference_{component}_pp"] = stable_pct - main_pct
            rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(cfg.DERIVED / "stable_code_sensitivity.csv", index=False)
    return coverage, out


def projection_per_year_comparison():
    decomposition = pd.read_csv(cfg.DERIVED / f"decomposition_{PRIMARY_TAG}.csv")
    observed = decomposition[decomposition["period"] == cfg.PRIMARY_PERIOD].set_index("group")
    projection = pd.read_csv(cfg.DERIVED / "projection_2040.csv")
    projected = projection[
        projection["rate_base"].eq("2024/25")
        & projection["variant"].eq("Principal projection")
    ].set_index("group")

    observed_years = cfg.PERIODS[cfg.PRIMARY_PERIOD][1] - cfg.PERIODS[cfg.PRIMARY_PERIOD][0]
    projected_years = cfg.PROJECTION_TARGET_FY - cfg.PROJECTION_BASE_FY
    rows = []
    for group in cfg.PROCEDURE_GROUPS:
        rows.append(
            {
                "group": group,
                "observed_age_structure_pp_per_year": observed.loc[
                    group, "age_structure_pct_of_baseline"
                ] / observed_years,
                "projected_age_structure_pp_per_year": projected.loc[
                    group, "age_structure_pct"
                ] / projected_years,
                "observed_total_demographic_pp_per_year": (
                    observed.loc[group, "population_size_pct_of_baseline"]
                    + observed.loc[group, "age_structure_pct_of_baseline"]
                ) / observed_years,
                "projected_total_demographic_pp_per_year": (
                    projected.loc[group, "population_size_pct"]
                    + projected.loc[group, "age_structure_pct"]
                ) / projected_years,
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(cfg.DERIVED / "projection_per_year_comparison.csv", index=False)

    metrics = [column for column in out if column != "group"]
    summary_rows = []
    for statistic, function in [
        ("mean", pd.Series.mean),
        ("standard deviation", lambda x: x.std(ddof=1)),
        ("minimum", pd.Series.min),
        ("maximum", pd.Series.max),
    ]:
        summary_rows.append(
            {"statistic": statistic}
            | {metric: float(function(out[metric])) for metric in metrics}
        )
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(cfg.DERIVED / "projection_per_year_summary.csv", index=False)
    return out, summary


def main():
    coverage, stable = stable_code_sensitivity()
    panel = selected_panel_robustness()
    _, projection_summary = projection_per_year_comparison()

    leave_one_out = panel[panel["specification"].eq("Leave one group out")]
    print(
        "  selected_panel_robustness.csv; leave-one-out rate share "
        f"{leave_one_out['age_specific_rate_share'].min() * 100:.1f}% to "
        f"{leave_one_out['age_specific_rate_share'].max() * 100:.1f}%"
    )
    print(
        f"  code_coverage.csv; {(~coverage['present_all_years']).sum()} of "
        f"{len(coverage)} codes absent in at least one study year"
    )
    print(
        "  stable_code_sensitivity.csv; max component difference "
        f"{stable.filter(like='difference_').abs().max().max():.2f} pp"
    )
    means = projection_summary.set_index("statistic").loc["mean"]
    print(
        "  projection_per_year_summary.csv; mean total demographic contribution "
        f"observed {means['observed_total_demographic_pp_per_year']:.2f} vs "
        f"projected {means['projected_total_demographic_pp_per_year']:.2f} pp/year"
    )


if __name__ == "__main__":
    main()
