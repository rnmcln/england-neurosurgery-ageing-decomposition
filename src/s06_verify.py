"""
Step 6. Verification.

Recomputes the quantities that appear in the results summary by a route
independent of the analysis scripts, and checks internal consistency. Any
failure is printed and the script exits non-zero.

Checks:
  V1  decomposition closure          independently sum component columns
  V2  count reconciliation           group totals reconcile to the raw
                                     opcs4_usage table, independently of the
                                     breakdown table used in the analysis
  V3  population reconciliation      banded population sums to the published
                                     England total for each year
  V4  standardisation identity       ASR equals crude rate in the standard year
  V5  qualitative guardrails         central ordering and selected values in
                                     RESULTS.md agree with derived files
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg

PRIMARY_TAG = f"{cfg.COUNT_BASIS}__{cfg.UNKNOWN_AGE_HANDLING}"
failures = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}  {detail}")
    if not condition:
        failures.append(name)


def main():
    dec = pd.read_csv(cfg.DERIVED / f"decomposition_{PRIMARY_TAG}.csv")
    rates = pd.read_csv(cfg.DERIVED / f"rates_{PRIMARY_TAG}.csv")
    analysis = pd.read_csv(cfg.DERIVED / f"analysis_{PRIMARY_TAG}.csv")

    # V1 closure
    recomputed_closure = dec["total_change"] - dec[
        ["population_size", "age_structure", "age_specific_rate"]
    ].sum(axis=1)
    err = recomputed_closure.abs().max()
    check("V1 decomposition closure", err < 1e-6, f"max |error| = {err:.2e}")

    # V2 reconcile against the independent totals table
    raw = pyreadr.read_r(str(cfg.RAW / "opcs4_usage.rda"))["opcs4_usage"]
    raw["usage"] = pd.to_numeric(raw["usage"])
    raw["fy"] = pd.to_datetime(raw["end_date"]).dt.year
    code_to_group = {
        c: g for g, s in cfg.PROCEDURE_GROUPS.items() for c in s["codes"]
    }
    raw = raw[raw["opcs4_code"].astype(str).isin(code_to_group)].copy()
    raw["group"] = raw["opcs4_code"].astype(str).map(code_to_group)
    ref = raw.groupby(["group", "fy"])["usage"].sum()
    got = rates.set_index(["group", "fy"])["count"]
    joined = pd.concat([ref.rename("ref"), got.rename("got")], axis=1).dropna()
    rel = ((joined["got"] - joined["ref"]).abs() / joined["ref"]).max()
    check(
        "V2 count reconciliation vs opcs4_usage",
        rel < 1e-9,
        f"max relative difference = {rel:.2e}",
    )

    # V3 population totals
    pop = analysis.drop_duplicates(["mye_year", "band"]).groupby("mye_year")[
        "population"
    ].sum()
    check(
        "V3 population magnitude and monotonic growth",
        (pop > 53e6).all() and (pop.diff().dropna() > 0).all(),
        f"2012={pop.min():,.0f} to 2024={pop.max():,.0f}",
    )
    raw_pop = pd.read_csv(cfg.RAW / "ons_mye_england_sya.csv")
    raw_pop.columns = [column.lower() for column in raw_pop.columns]
    raw_totals = raw_pop.groupby("date_name")["obs_value"].sum().sort_index()
    aligned = pd.concat(
        [pop.rename("analysis"), raw_totals.rename("raw")], axis=1, join="inner"
    )
    check(
        "V3b banded population reconciles to raw single-year totals",
        len(aligned) == len(cfg.MYE_YEARS)
        and (aligned["analysis"] - aligned["raw"]).abs().max() < 1e-6,
        f"max |difference| = {(aligned['analysis'] - aligned['raw']).abs().max():.2e}",
    )

    # V4 standardisation identity in the standard year
    std_fy = min(cfg.MYE_YEARS) + 1
    r = rates[rates["fy"] == std_fy]
    d = (r["asr_per_100k"] - r["crude_per_100k"]).abs().max()
    check(
        "V4 ASR equals crude rate in standard year",
        d < 1e-6,
        f"max |difference| = {d:.2e}",
    )

    # V5 qualitative guardrails and selected-value presence in RESULTS.md.
    claims_path = cfg.ROOT / "RESULTS.md"
    if claims_path.exists():
        text = claims_path.read_text()
        pre = dec[dec["period"] == cfg.PRIMARY_PERIOD].set_index("group")

        ps = pre["population_size_pct_of_baseline"]
        check(
            "V5a population-size component near-uniform across groups",
            (ps.max() - ps.min()) < 1.5,
            f"range {ps.min():.1f} to {ps.max():.1f} % of baseline",
        )

        ages = pre["age_structure_pct_of_baseline"]
        check(
            "V5b age-structure component small in every group",
            ages.abs().max() < 5.0,
            f"max |component| = {ages.abs().max():.1f} % of baseline",
        )

        biggest = ages.idxmax()
        check(
            "V5c largest age-structure component is extra-axial haematoma",
            biggest == "Extra-axial haematoma evacuation",
            f"largest = {biggest} ({ages.max():.1f}%)",
        )

        rate = pre["age_specific_rate_pct_of_baseline"]
        check(
            "V5d rate component spans a wider range than age structure",
            (rate.max() - rate.min()) > 5 * (ages.max() - ages.min()),
            f"rate range {rate.max()-rate.min():.1f} vs age-structure range "
            f"{ages.max()-ages.min():.1f}",
        )

        vd = pd.read_csv(cfg.DERIVED / "variance_decomposition.csv")
        vp = vd[vd["period"] == cfg.PRIMARY_PERIOD].iloc[0]
        for token in [f"{ps.min():.1f}", f"{ages.max():.1f}",
                      f"{vp['age_specific_rate_share']*100:.1f}"]:
            check(
                f"V5e RESULTS.md contains derived value {token}",
                token in text,
                "",
            )
    else:
        print("  [SKIP] V5 claim checks: RESULTS.md not present")

    # V7 projection internal consistency
    proj_path = cfg.DERIVED / "projection_2040.csv"
    if proj_path.exists():
        proj = pd.read_csv(proj_path)
        check(
            "V7a projection closure",
            proj["closure_error"].abs().max() < 1e-6,
            f"max |error| = {proj['closure_error'].abs().max():.2e}",
        )
        p = proj[proj["rate_base"] == "2024/25"]
        struct = p.pivot_table(
            index="group", columns="variant", values="age_structure_pct"
        )
        # The ordering of variants tracks each group's age profile rather than
        # following a common direction: an older projected population raises
        # activity in age-weighted groups and lowers it in infancy-weighted
        # ones. Tested on the clearest case at each end.
        check(
            "V7b variant ordering tracks age profile (elderly-weighted group)",
            struct.loc["Extra-axial haematoma evacuation", "Old age structure"]
            > struct.loc["Extra-axial haematoma evacuation", "Young age structure"],
            "",
        )
        check(
            "V7b2 variant ordering tracks age profile (infancy-weighted group)",
            struct.loc["CSF diversion, primary", "Young age structure"]
            > struct.loc["CSF diversion, primary", "Old age structure"],
            "",
        )
        base = proj[
            (proj["rate_base"] == "2024/25")
            & (proj["variant"] == "Principal projection")
        ].set_index("group")
        obs = dec[dec["period"] == cfg.PRIMARY_PERIOD].set_index("group")
        ratio = (base["age_structure_pct"] / 15) / (
            obs["age_structure_pct_of_baseline"] / 6
        )
        g = "Extra-axial haematoma evacuation"
        check(
            "V7c projected age-structure pressure exceeds observed for haematoma",
            ratio.loc[g] > 1,
            f"ratio = {ratio.loc[g]:.2f}",
        )
        npp_checks = pd.read_csv(cfg.DERIVED / "npp_population_checks.csv")
        npp_raw = pd.read_csv(cfg.RAW / "ons_npp_england_sya.csv")
        check(
            "V7d projection extract includes 105+ and reconciles to All Ages",
            npp_raw["C_AGE_NAME"].eq("Age 105+").any()
            and npp_raw["C_AGE_NAME"].eq("All Ages").any()
            and npp_checks["difference"].abs().max() == 0,
            f"max |difference| = {npp_checks['difference'].abs().max():.0f}",
        )
    else:
        print("  [SKIP] V7 projection checks")

    # V9 Shapley allocation leaves the components materially unchanged
    sh_path = cfg.DERIVED / "shapley_comparison.csv"
    if sh_path.exists():
        sh = pd.read_csv(sh_path)
        diff = sh[[c for c in sh.columns if c.endswith("_abs_diff_pp")]].max().max()
        check(
            "V9 Kitagawa vs Shapley allocation materially unchanged",
            diff < 0.5,
            f"max |difference| = {diff:.3f} pp",
        )
        check(
            "V9b Shapley closure",
            sh["shapley_closure_error"].abs().max() < 1e-6,
            f"max |error| = {sh['shapley_closure_error'].abs().max():.2e}",
        )
    else:
        print("  [SKIP] V9 Shapley comparison")

    # V10 endpoint sensitivity: the qualitative result holds under the
    # alternative endpoint and the three-year-average specifications
    alt_path = cfg.DERIVED / "alternative_endpoints.csv"
    if alt_path.exists():
        alt = pd.read_csv(alt_path)
        for spec, d in alt.groupby("specification"):
            ages = d["age_structure_pct"]
            rate_rng = d["age_specific_rate_pct"].max() - d["age_specific_rate_pct"].min()
            age_rng = ages.max() - ages.min()
            check(
                f"V10 age structure small and rate dominant [{spec[:40]}]",
                ages.abs().max() < 5.0 and rate_rng > 5 * age_rng,
                f"max |age structure| = {ages.abs().max():.1f}%, "
                f"rate range {rate_rng:.1f} vs age range {age_rng:.1f}",
            )
    else:
        print("  [SKIP] V10 alternative endpoints")

    # V11 cumulated consecutive-year decompositions agree qualitatively
    cum_path = cfg.DERIVED / "cumulative_annual.csv"
    if cum_path.exists():
        cum = pd.read_csv(cum_path)
        ages = cum["age_structure_cumulated_pct"]
        rates_c = cum["age_specific_rate_cumulated_pct"]
        check(
            "V11 cumulated annual decomposition: age structure small, rate dominant",
            ages.abs().max() < 5.0
            and (rates_c.max() - rates_c.min()) > 5 * (ages.max() - ages.min()),
            f"max |age structure| = {ages.abs().max():.1f}%, "
            f"rate range = {rates_c.max() - rates_c.min():.1f} pp",
        )
    else:
        print("  [SKIP] V11 cumulative annual")

    # V12 dispersion statistics reproduce and order as claimed
    disp_path = cfg.DERIVED / "dispersion.csv"
    if disp_path.exists():
        disp = pd.read_csv(disp_path)
        d = disp[
            (disp["period"] == cfg.PRIMARY_PERIOD)
            & (disp["quantity"] != "corr_demographic_vs_observed")
        ].set_index("quantity")
        check(
            "V12 between-group SD: rate component within 5% of net-change SD",
            abs(
                d.loc["age_specific_rate", "sd_between_groups_pp"]
                - d.loc["net_change", "sd_between_groups_pp"]
            )
            / d.loc["net_change", "sd_between_groups_pp"]
            < 0.05,
            f"net {d.loc['net_change','sd_between_groups_pp']:.2f} vs "
            f"rate {d.loc['age_specific_rate','sd_between_groups_pp']:.2f} pp",
        )
        check(
            "V12b between-group SD of age structure under a tenth of net change",
            d.loc["age_structure", "sd_between_groups_pp"]
            < 0.1 * d.loc["net_change", "sd_between_groups_pp"],
            f"age structure {d.loc['age_structure','sd_between_groups_pp']:.2f} pp",
        )
    else:
        print("  [SKIP] V12 dispersion")

    # V13 exact variance decomposition: shares sum to one, rate dominant
    vd_path = cfg.DERIVED / "variance_decomposition.csv"
    if vd_path.exists():
        vd = pd.read_csv(vd_path)
        p = vd[vd["period"] == cfg.PRIMARY_PERIOD].iloc[0]
        check(
            "V13 variance-decomposition shares sum to 1",
            abs(p["share_sum"] - 1.0) < 1e-9,
            f"sum = {p['share_sum']:.12f}",
        )
        check(
            "V13b rate share of between-group variance dominant",
            p["age_specific_rate_share"] > 0.90,
            f"rate {p['age_specific_rate_share']*100:.1f}%, "
            f"size {p['population_size_share']*100:.1f}%, "
            f"structure {p['age_structure_share']*100:.1f}%",
        )
        # independent recomputation of the covariance identity
        d = dec[dec["period"] == cfg.PRIMARY_PERIOD]
        Y = d["pct_change"]
        recomputed = sum(
            np.cov(d[f"{c}_pct_of_baseline"], Y, ddof=1)[0, 1]
            for c in ["population_size", "age_structure", "age_specific_rate"]
        )
        check(
            "V13c Cov identity: components sum to Var(net change)",
            abs(recomputed - Y.var(ddof=1)) < 1e-9,
            f"|diff| = {abs(recomputed - Y.var(ddof=1)):.2e}",
        )
    else:
        print("  [SKIP] V13 variance decomposition")

    # V14 later-period aggregate: demographic positive, rate negative and
    # larger in magnitude than the net fall
    lat = dec[dec["period"] == cfg.LATER_PERIOD]
    if not lat.empty:
        net = lat["total_change"].sum()
        demo = (lat["population_size"] + lat["age_structure"]).sum()
        rate = lat["age_specific_rate"].sum()
        check(
            "V14 later-period aggregate: demographic +, rate -, |rate| > |net|",
            demo > 0 and rate < 0 and abs(rate) > abs(net) and net < 0,
            f"net {net:,.0f}, demographic {demo:,.0f}, rate {rate:,.0f}",
        )
    else:
        print("  [SKIP] V14 later-period aggregate")

    # V15 Table 1 and Table 2 counts agree (one authoritative rounding)
    t1_path = cfg.TABLES / "tab_procedure_groups.csv"
    t2_path = cfg.TABLES / "tab_decomposition_display_periods.csv"
    if t1_path.exists() and t2_path.exists():
        t1 = pd.read_csv(t1_path).set_index("Procedure group")
        t2 = pd.read_csv(t2_path)
        pre_t2 = t2[t2["Period"] == cfg.PRIMARY_PERIOD].set_index("Procedure group")
        lat_t2 = t2[t2["Period"] == cfg.LATER_PERIOD].set_index("Procedure group")
        ok_start = (t1["Count 2012/13"] == pre_t2["Count, start"]).all()
        ok_end = (t1["Count 2024/25"] == lat_t2["Count, end"]).all()
        check(
            "V15 Table 1 counts agree with Table 2 (2012/13 and 2024/25)",
            bool(ok_start and ok_end),
            "",
        )
    else:
        print("  [SKIP] V15 table count consistency")

    # V8 substitution check reproduces from source
    sub_path = cfg.TABLES / "tab_substitution_check.csv"
    if sub_path.exists():
        sub = pd.read_csv(sub_path)
        older = sub[sub["Age stratum"] == "75 and over"].iloc[0]
        check(
            "V8 substitution check present and internally signed",
            older["Change D"] < 0 and older["Change E"] > 0,
            f"D = {older['Change D']}, E = {older['Change E']}",
        )
    else:
        print("  [SKIP] V8 substitution check")

    # V6 documented checksums match the retrieved files
    import json

    manifest_path = cfg.RAW / "manifest.json"
    readme_path = cfg.ROOT / "README.md"
    if manifest_path.exists() and readme_path.exists():
        manifest = json.load(open(manifest_path))
        readme = readme_path.read_text()
        for fname, meta in manifest["files"].items():
            frag = f"{meta['sha256'][:8]}...{meta['sha256'][-4:]}"
            check(f"V6 README records checksum for {fname}", frag in readme, frag)
    else:
        print("  [SKIP] V6 checksum documentation check")

    # V16 robustness outputs.
    panel_path = cfg.DERIVED / "selected_panel_robustness.csv"
    stable_path = cfg.DERIVED / "stable_code_sensitivity.csv"
    coverage_path = cfg.DERIVED / "code_coverage.csv"
    projection_compare_path = cfg.DERIVED / "projection_per_year_comparison.csv"
    projection_summary_path = cfg.DERIVED / "projection_per_year_summary.csv"
    if all(
        path.exists()
        for path in [
            panel_path,
            stable_path,
            coverage_path,
            projection_compare_path,
            projection_summary_path,
        ]
    ):
        panel = pd.read_csv(panel_path)
        complete_panel = panel[panel["share_sum"].notna()]
        check(
            "V16 panel robustness shares close exactly",
            (complete_panel["share_sum"] - 1).abs().max() < 1e-9,
            f"max |sum-1| = {(complete_panel['share_sum'] - 1).abs().max():.2e}",
        )
        primary_panel = panel[
            panel["specification"].eq("Primary: equal-weight percentage change")
        ]
        stable_panel = panel[
            panel["specification"].str.startswith("Stable-code sensitivity:")
        ]
        leave_one_out = panel[panel["specification"].eq("Leave one group out")]
        check(
            "V16b rate contribution remains dominant across panel, code-set and counting checks",
            len(primary_panel) == 1
            and len(stable_panel) == 2
            and primary_panel["age_specific_rate_share"].iloc[0] > 0.90
            and stable_panel["age_specific_rate_share"].min() > 0.90
            and leave_one_out["age_specific_rate_share"].min() > 0.90,
            f"stable-code minimum {stable_panel['age_specific_rate_share'].min()*100:.1f}%, "
            f"leave-one-out minimum {leave_one_out['age_specific_rate_share'].min()*100:.1f}%",
        )

        stable = pd.read_csv(stable_path)
        coverage = pd.read_csv(coverage_path)
        build_checks = pd.read_csv(cfg.DERIVED / "build_checks.csv")
        build_missing = build_checks[
            build_checks["check"].eq("C1_code_coverage")
        ]["value"].sum()
        check(
            "V16c stable-code outputs have complete group rows and exact closure",
            len(stable) == 2 * len(cfg.PROCEDURE_GROUPS)
            and stable.groupby("stability_definition")["group"].nunique().eq(
                len(cfg.PROCEDURE_GROUPS)
            ).all()
            and stable["stable_closure_error"].abs().max() < 1e-6
            and (stable["n_codes_stable"] > 0).all(),
            f"rows={len(stable)}, max |closure|={stable['stable_closure_error'].abs().max():.2e}",
        )
        check(
            "V16d code-coverage audit reconciles to build check",
            len(coverage) == sum(len(item["codes"]) for item in cfg.PROCEDURE_GROUPS.values())
            and coverage["opcs4_code"].is_unique
            and coverage["n_missing_years"].sum() == build_missing,
            f"absent code-years={coverage['n_missing_years'].sum():.0f}",
        )

        projection_compare = pd.read_csv(projection_compare_path)
        projection_summary = pd.read_csv(projection_summary_path).set_index("statistic")
        recomputed_means = projection_compare.drop(columns="group").mean()
        summary_means = projection_summary.loc["mean"]
        check(
            "V16e projection per-year summary recomputes from group rows",
            len(projection_compare) == len(cfg.PROCEDURE_GROUPS)
            and (recomputed_means - summary_means).abs().max() < 1e-12,
            f"max |difference| = {(recomputed_means - summary_means).abs().max():.2e}",
        )
        check(
            "V16f projected demographic exposure is more dispersed, not higher on average",
            projection_summary.loc[
                "standard deviation", "projected_age_structure_pp_per_year"
            ]
            > projection_summary.loc[
                "standard deviation", "observed_age_structure_pp_per_year"
            ]
            and projection_summary.loc[
                "mean", "projected_total_demographic_pp_per_year"
            ]
            < projection_summary.loc[
                "mean", "observed_total_demographic_pp_per_year"
            ],
            "",
        )
    else:
        print("  [SKIP] V16 robustness outputs")

    # V17 publication display items
    pub = cfg.ROOT / "outputs" / "publication"
    if pub.exists():
        expected = (
            [f"Table{i}.csv" for i in range(1, 4)]
            + [f"TableS{i}.csv" for i in range(1, 20)]
            + [f"Fig{i}.{e}" for i in (1, 2) for e in ("pdf", "eps", "tiff", "png")]
            + [f"FigS{i}.{e}" for i in range(1, 8) for e in ("pdf", "eps", "tiff", "png")]
        )
        missing = [f for f in expected if not (pub / f).exists()]
        check("V17a publication items complete", not missing, f"missing={missing}")
        t2 = pd.read_csv(pub / "Table2.csv").set_index("Procedure group")
        pre = dec[dec["period"] == cfg.PRIMARY_PERIOD].set_index("group")
        diff = (t2.loc[list(cfg.PROCEDURE_GROUPS), "2012/13 to 2018/19: net change, %"]
                - pre.loc[list(cfg.PROCEDURE_GROUPS), "pct_change"].round(1)).abs().max()
        check("V17b Table 2 net change matches decomposition", diff < 1e-9, f"max |diff| = {diff:.2e}")
        Y = pre["pct_change"]
        share = np.cov(pre["age_specific_rate_pct_of_baseline"], Y, ddof=1)[0, 1] / Y.var(ddof=1) * 100
        row = t2.loc["Share of between-group variance in net change, %"]
        check("V17c Table 2 rate variance share recomputes independently",
              abs(row["2012/13 to 2018/19: age-specific rate, %"] - round(share, 1)) < 1e-9,
              f"{share:.2f}%")
        t3 = pd.read_csv(pub / "Table3.csv")
        body = t3[t3["Procedure group"] != "All twelve groups"]
        tot = t3[t3["Procedure group"] == "All twelve groups"].iloc[0]
        check("V17d Table 3 totals equal sum of groups",
              int(body["Change, n"].sum()) - int(tot["Change, n"]) in (-2, -1, 0, 1, 2),
              f"sum {body['Change, n'].sum()} vs total {tot['Change, n']}")
        t1 = pd.read_csv(pub / "Table1.csv")
        check("V17e Table 1 code count equals configuration",
              int(t1.iloc[-1]["OPCS-4 codes, n"]) == sum(len(s["codes"]) for s in cfg.PROCEDURE_GROUPS.values()), "")
    else:
        print("  [SKIP] V17 publication items")

    print()
    if failures:
        print(f"  {len(failures)} check(s) failed: {failures}")
        sys.exit(1)
    print("  all checks passed")


if __name__ == "__main__":
    main()
