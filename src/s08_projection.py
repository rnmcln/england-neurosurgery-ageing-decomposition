"""
Step 8. Fixed-rate demographic scenario to 2039/40.

Terminology. This is a scenario, not a forecast of workload, demand or need:
it projects what recorded procedure volume would be if contemporary
age-specific recorded rates persisted while the population changed as
projected.

The age-structure component of the decomposition describes what demography did.
Capacity planning needs the forward version of the same quantity: what
demography alone would do to recorded activity if age-specific rates were
unchanged.

Method. Age-specific recording rates are held fixed at their observed 2024/25
values and applied to ONS 2024-based national population projections for
England. Projected count for year t is sum_a m_{a,2025} * P_{a,t}. The
difference from the 2024/25 count is therefore attributable to projected
population size and age structure alone.

This is a counterfactual accounting statement, not a forecast. It is the
quantity that answers "how much additional activity would arise from
demographic change alone", and nothing more. Age-specific rates have moved
substantially over the observed period in most groups, in both directions, so
the assumption that they hold constant is known to be false. Its purpose is to
isolate the demographic contribution, which is exactly why it is imposed.

Three population variants are carried: the principal projection and the old and
young age structure variants. These bundle fertility, mortality and migration
assumptions and therefore differ in total size as well as in composition; the
projected change is decomposed into size and structure so that the two are not
conflated. The direction in which the variants move the structure component
differs by group and follows each group's age profile: an older projected
population raises projected activity in age-weighted groups such as extra-axial
haematoma evacuation and lowers it in infancy-weighted groups such as primary
CSF diversion.

Rate-base sensitivity. Fixing rates at a single year propagates that year's
idiosyncrasies. Two alternative bases are reported: the mean of 2023/24 and
2024/25, and the pre-pandemic 2018/19 rates.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg

TAG = f"{cfg.COUNT_BASIS}__{cfg.UNKNOWN_AGE_HANDLING}"

RATE_BASES = {
    "2024/25": [2025],
    "mean of 2023/24 and 2024/25": [2024, 2025],
    "2018/19 (pre-pandemic)": [2019],
}


def load_projections():
    df = pd.read_csv(cfg.RAW / "ons_npp_england_sya.csv")
    df.columns = [c.lower() for c in df.columns]
    df = df.rename(
        columns={
            "projected_year_name": "year",
            "projvar_name": "variant",
            "obs_value": "population",
        }
    )
    all_ages = df[df["c_age_name"].eq("All Ages")][
        ["variant", "year", "population"]
    ].rename(columns={"population": "published_all_ages"})
    detail = df[~df["c_age_name"].eq("All Ages")].copy()
    detail_totals = (
        detail.groupby(["variant", "year"], as_index=False)["population"]
        .sum()
        .rename(columns={"population": "sum_single_ages"})
    )
    checks = all_ages.merge(
        detail_totals, on=["variant", "year"], how="outer", validate="one_to_one"
    )
    checks["difference"] = checks["sum_single_ages"] - checks["published_all_ages"]
    if checks.isna().any().any() or checks["difference"].abs().max() != 0:
        raise ValueError("projected single-year ages do not reconcile to All Ages")
    cfg.DERIVED.mkdir(parents=True, exist_ok=True)
    checks.to_csv(cfg.DERIVED / "npp_population_checks.csv", index=False)

    detail["age"] = detail["c_age_name"].str.extract(r"(\d+)")[0].astype(int)
    detail["band"] = pd.cut(
        detail["age"],
        bins=[-1, 0, 4, 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59, 64, 69, 74,
              79, 84, 89, 200],
        labels=cfg.AGE_BANDS,
    ).astype(str)
    return detail.groupby(["variant", "year", "band"], as_index=False)[
        "population"
    ].sum()


def primary_change(proj):
    pr = proj[(proj["rate_base"] == "2024/25")
              & (proj["variant"] == "Principal projection")]
    return pr.set_index("group")["change_n"]


def main():
    analysis = pd.read_csv(cfg.DERIVED / f"analysis_{TAG}.csv")
    npp = load_projections()

    # Financial year ending Y is matched to mid-year population for Y-1.
    base_pop_year = cfg.PROJECTION_BASE_FY - 1
    target_pop_year = cfg.PROJECTION_TARGET_FY - 1

    rows = []
    for group in cfg.PROCEDURE_GROUPS:
        g = analysis[analysis["group"] == group]
        for base_label, base_years in RATE_BASES.items():
            b = g[g["fy"].isin(base_years)]
            rates = (
                b.groupby("band")["count"].sum() / b.groupby("band")["population"].sum()
            ).reindex(cfg.AGE_BANDS)

            for variant, v in npp.groupby("variant"):
                p0 = v[v["year"] == base_pop_year].set_index("band")["population"]
                p1 = v[v["year"] == target_pop_year].set_index("band")["population"]
                p0, p1 = p0.reindex(cfg.AGE_BANDS), p1.reindex(cfg.AGE_BANDS)

                n0 = float((rates * p0).sum())
                n1 = float((rates * p1).sum())

                # Split the projected change into size and structure, using the
                # same symmetric decomposition as the retrospective analysis.
                P0, P1 = p0.sum(), p1.sum()
                c0, c1 = p0 / P0, p1 / P1
                R0, R1 = float((c0 * rates).sum()), float((c1 * rates).sum())
                size = (P1 - P0) * (R0 + R1) / 2
                struct = (P0 + P1) / 2 * float(((c1 - c0) * rates).sum())

                rows.append(
                    {
                        "group": group,
                        "rate_base": base_label,
                        "variant": variant,
                        "count_2024_25": n0,
                        "count_2039_40": n1,
                        "change_n": n1 - n0,
                        "change_pct": (n1 - n0) / n0 * 100,
                        "annualised_pct": ((n1 / n0) ** (1 / 15) - 1) * 100,
                        "population_size_pct": size / n0 * 100,
                        "age_structure_pct": struct / n0 * 100,
                        "closure_error": (n1 - n0) - (size + struct),
                    }
                )

    proj = pd.DataFrame(rows)
    proj.to_csv(cfg.DERIVED / "projection_2040.csv", index=False)

    # Age distribution of the primary scenario. The scenario change is split
    # by broad age at the time of the procedure (0-64, 65-79, 80 and over), so
    # that the share of projected demographic pressure falling on older people
    # can be reported. Primary specification only: 2024/25 rates, principal
    # projection.
    broad = {b: ("0-64" if i < cfg.AGE_BANDS.index("65-69")
                 else "65-79" if i < cfg.AGE_BANDS.index("80-84") else "80+")
             for i, b in enumerate(cfg.AGE_BANDS)}
    v = npp[npp["variant"] == "Principal projection"]
    p0 = v[v["year"] == base_pop_year].set_index("band")["population"].reindex(cfg.AGE_BANDS)
    p1 = v[v["year"] == target_pop_year].set_index("band")["population"].reindex(cfg.AGE_BANDS)
    age_rows = []
    for group in cfg.PROCEDURE_GROUPS:
        b = analysis[(analysis["group"] == group) & (analysis["fy"] == 2025)]
        rates = (b.groupby("band")["count"].sum()
                 / b.groupby("band")["population"].sum()).reindex(cfg.AGE_BANDS)
        n0 = (rates * p0).groupby(broad).sum()
        n1 = (rates * p1).groupby(broad).sum()
        for age in ["0-64", "65-79", "80+"]:
            age_rows.append({"group": group, "age": age,
                             "count_2024_25": float(n0[age]),
                             "count_2039_40": float(n1[age]),
                             "change_n": float(n1[age] - n0[age])})
    by_age = pd.DataFrame(age_rows)
    check = (by_age.groupby("group")["change_n"].sum()
             - primary_change(proj)).abs().max()
    if check > 1e-6:
        raise ValueError("age-split scenario does not reconcile to the scenario total")
    by_age.to_csv(cfg.DERIVED / "projection_2040_by_age.csv", index=False)

    # Main scenario table. Absolute counts are reported alongside percentages
    # because planning uses absolute volumes: the observed 2024/25 recorded
    # count, the scenario base and 2039/40 counts, and the absolute difference.
    # The scenario base differs marginally from the observed count because the
    # base-year population comes from the projection series rather than the
    # mid-year estimates.
    rates_obs = pd.read_csv(cfg.DERIVED / f"rates_{TAG}.csv")
    obs_2025 = rates_obs[rates_obs["fy"] == 2025].set_index("group")["count"]

    primary = proj[
        (proj["rate_base"] == "2024/25") & (proj["variant"] == "Principal projection")
    ]
    tbl = primary[
        ["group", "count_2024_25", "count_2039_40", "change_n", "change_pct",
         "population_size_pct", "age_structure_pct"]
    ].copy()
    tbl.insert(1, "obs", tbl["group"].map(obs_2025))
    tbl.columns = [
        "Procedure group", "Recorded count 2024/25", "Scenario base 2024/25",
        "Scenario count 2039/40", "Scenario change, n", "Scenario change, %",
        "Population size, %", "Age structure, %",
    ]
    for c in tbl.columns[1:5]:
        tbl[c] = tbl[c].round(0).astype(int)
    for c in tbl.columns[5:]:
        tbl[c] = tbl[c].round(2)
    tbl.to_csv(cfg.TABLES / "tab_projection_scenario.csv", index=False)

    rng = (
        proj.groupby("group")["change_pct"].agg(["min", "max"]).round(1)
        .rename(columns={"min": "Lowest, %", "max": "Highest, %"})
    )
    rng.to_csv(cfg.TABLES / "tab_projection_range.csv")

    print(tbl.to_string(index=False))
    print()
    print(f"  max closure error = {proj['closure_error'].abs().max():.2e}")
    print("  tab_projection_scenario.csv, tab_projection_range.csv")


if __name__ == "__main__":
    main()
