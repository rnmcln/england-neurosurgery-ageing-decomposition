"""
Step 2. Build the analysis dataset.

Output is a long table of procedure counts by group, financial year and age
band, with the matched England mid-year population for the same band.

Three data-integrity checks are run and written to derived/build_checks.csv
rather than being asserted silently:

  C1  code coverage        every code named in config is present in the source
                           data in every year, or is flagged as absent
  C2  age allocation       proportion of each group-year total that the age
                           breakdown accounts for
  C3  positional ratio     main_procedure divided by all_procedures, which
                           indexes how much of the count comes from secondary
                           procedure positions
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg


def load_breakdowns():
    df = pyreadr.read_r(str(cfg.RAW / "opcs4_usage_breakdowns.rda"))[
        "opcs4_usage_breakdowns"
    ]
    df["usage"] = pd.to_numeric(df["usage"])
    df["fy"] = pd.to_datetime(df["end_date"]).dt.year
    df["opcs4_code"] = df["opcs4_code"].astype(str)
    df["breakdown"] = df["breakdown"].astype(str)
    return df


def load_population():
    pop = pd.read_csv(cfg.RAW / "ons_mye_england_sya.csv")
    pop.columns = [c.lower() for c in pop.columns]
    pop = pop.rename(columns={"date_name": "mye_year", "obs_value": "population"})
    age = pop["c_age_name"].str.extract(r"(\d+)")[0].astype(int)
    pop["age"] = age
    pop["band"] = pd.cut(
        pop["age"],
        bins=[-1, 0, 4, 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59, 64, 69, 74,
              79, 84, 89, 200],
        labels=cfg.AGE_BANDS,
    ).astype(str)
    out = pop.groupby(["mye_year", "band"], as_index=False)["population"].sum()
    return out


def build(count_basis, unknown_age):
    bd = load_breakdowns()
    pop = load_population()

    code_to_group = {}
    for g, spec in cfg.PROCEDURE_GROUPS.items():
        for c in spec["codes"]:
            if c in code_to_group:
                raise ValueError(f"code {c} assigned to more than one group")
            code_to_group[c] = g

    bd = bd[bd["opcs4_code"].isin(code_to_group)].copy()
    bd["group"] = bd["opcs4_code"].map(code_to_group)

    checks = []

    # C1: code coverage
    years = sorted(bd["fy"].unique())
    present = set(zip(bd["opcs4_code"], bd["fy"]))
    for g, spec in cfg.PROCEDURE_GROUPS.items():
        missing = [
            (c, y) for c in spec["codes"] for y in years if (c, y) not in present
        ]
        checks.append(
            {
                "check": "C1_code_coverage",
                "group": g,
                "metric": "code_years_absent",
                "value": len(missing),
                "detail": "; ".join(f"{c}:{y}" for c, y in missing[:10]),
            }
        )

    # Totals on the two positional bases
    totals = (
        bd[bd["breakdown"].isin(["all_procedures", "main_procedure"])]
        .pivot_table(index=["group", "fy"], columns="breakdown", values="usage",
                     aggfunc="sum")
        .reset_index()
    )
    for _, r in totals.iterrows():
        checks.append(
            {
                "check": "C3_positional_ratio",
                "group": r["group"],
                "metric": f"main_over_all_fy{int(r['fy'])}",
                "value": round(r["main_procedure"] / r["all_procedures"], 4),
                "detail": f"all={int(r['all_procedures'])}",
            }
        )

    # Age-band counts
    age_bd = bd[bd["breakdown"].isin(cfg.BREAKDOWN_TO_BAND)].copy()
    if count_basis == "main_procedure":
        # Breakdowns are published on the all_procedures basis only. The
        # main_procedure basis is approximated by scaling each group-year age
        # distribution by that year's main/all ratio, which assumes the
        # positional mix does not vary with age. This is a sensitivity analysis
        # only and the assumption is stated in the article.
        ratio = totals.set_index(["group", "fy"])["main_procedure"] / totals.set_index(
            ["group", "fy"]
        )["all_procedures"]
        age_bd["scale"] = list(
            ratio.loc[list(zip(age_bd["group"], age_bd["fy"]))].values
        )
        age_bd["usage"] = age_bd["usage"] * age_bd["scale"]

    age_bd["band"] = age_bd["breakdown"].map(cfg.BREAKDOWN_TO_BAND)
    counts = (
        age_bd.groupby(["group", "fy", "band"], as_index=False)["usage"].sum()
        .rename(columns={"usage": "count"})
    )

    # C2: age allocation
    tot_all = totals.set_index(["group", "fy"])[
        "all_procedures" if count_basis == "all_procedures" else "main_procedure"
    ]
    age_tot = counts.groupby(["group", "fy"])["count"].sum()
    alloc = (age_tot / tot_all).dropna()
    for (g, y), v in alloc.items():
        checks.append(
            {
                "check": "C2_age_allocation",
                "group": g,
                "metric": f"allocated_fraction_fy{int(y)}",
                "value": round(float(v), 4),
                "detail": f"total={int(tot_all.loc[(g, y)])}",
            }
        )

    # Unknown-age handling
    if unknown_age == "proportional":
        counts = counts.merge(
            (tot_all / age_tot).rename("infl").reset_index(), on=["group", "fy"]
        )
        counts["count"] = counts["count"] * counts["infl"]
        counts = counts.drop(columns="infl")
    elif unknown_age == "oldest":
        gap = (tot_all - age_tot).rename("gap").reset_index()
        counts = counts.merge(gap, on=["group", "fy"])
        counts.loc[counts["band"] == "90+", "count"] += counts.loc[
            counts["band"] == "90+", "gap"
        ]
        counts = counts.drop(columns="gap")
    elif unknown_age == "drop":
        pass
    else:
        raise ValueError(unknown_age)

    counts["mye_year"] = counts["fy"].map(cfg.fy_to_mye)
    out = counts.merge(pop, on=["mye_year", "band"], how="left")
    if out["population"].isna().any():
        raise ValueError("unmatched population rows")

    out["band"] = pd.Categorical(out["band"], categories=cfg.AGE_BANDS, ordered=True)
    out = out.sort_values(["group", "fy", "band"]).reset_index(drop=True)
    out["rate_per_100k"] = out["count"] / out["population"] * 1e5
    return out, pd.DataFrame(checks)


def main():
    cfg.DERIVED.mkdir(parents=True, exist_ok=True)
    for basis in ["all_procedures", "main_procedure"]:
        for unk in ["proportional", "oldest", "drop"]:
            df, checks = build(basis, unk)
            tag = f"{basis}__{unk}"
            df.to_csv(cfg.DERIVED / f"analysis_{tag}.csv", index=False)
            if basis == cfg.COUNT_BASIS and unk == cfg.UNKNOWN_AGE_HANDLING:
                checks.to_csv(cfg.DERIVED / "build_checks.csv", index=False)
                print(f"  primary dataset: analysis_{tag}.csv  ({len(df):,} rows)")
    print("  built 6 dataset variants")


if __name__ == "__main__":
    main()
