"""
Step 13. Publication display items and key results.

Assembles the numbered tables and figures reported in the article and its
supplementary material from the working outputs of steps 3 to 12, and writes
every quantity quoted in the text to derived/key_results.json so that the
article can be checked against the pipeline.

Outputs (outputs/publication/):
  Table1.csv to Table3.csv          main tables
  Fig1.*, Fig2.*                    main figures (PDF, EPS, TIFF, PNG)
  TableS1.csv to TableS19.csv       supplementary tables
  FigS1.* to FigS7.*                supplementary figures
  CAPTIONS.md                       short description of every item
"""

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg

PUB = cfg.ROOT / "outputs" / "publication"
PRIMARY_TAG = f"{cfg.COUNT_BASIS}__{cfg.UNKNOWN_AGE_HANDLING}"
GROUPS = list(cfg.PROCEDURE_GROUPS)
PRE, LATER = cfg.PRIMARY_PERIOD, cfg.LATER_PERIOD
OLD_BANDS = ["65-69", "70-74", "75-79", "80-84", "85-89", "90+"]

CONTENT = {
    "Extra-axial haematoma evacuation": "Evacuation of extradural or subdural haematoma",
    "Intracerebral haematoma evacuation": "Evacuation of intracerebral or cerebellar haematoma",
    "Intracranial tumour resection and biopsy": "Excision and biopsy of brain, ventricular and meningeal lesions",
    "CSF diversion, primary": "Creation of ventricular shunt or reservoir; endoscopic third ventriculostomy",
    "CSF diversion, revision and maintenance": "Maintenance, revision, renewal and removal of ventricular shunts",
    "Peripheral nerve entrapment release": "Carpal, cubital and other nerve entrapment release",
    "Neuromodulation implantation": "Implantation of brain, cranial and peripheral nerve stimulators",
    "Spinal nerve root injection and denervation": "Injection around, or destruction of, spinal nerve roots",
    "Lumbar decompression without fusion": "Primary lumbar decompression and discectomy without fusion",
    "Spinal fusion and instrumentation": "Primary cervical, thoracic and lumbar fusion",
    "Spinal deformity correction": "Instrumental correction of spinal deformity, growing systems",
    "Spinal facet joint denervation": "Denervation of cervical, thoracic and lumbar facet joints",
}


def r1(x):
    return float(np.round(x, 1))


def table1(rates, analysis):
    rows = []
    for g in GROUPS:
        r = rates[rates["group"] == g].set_index("fy")
        a = analysis[(analysis["group"] == g) & (analysis["fy"] == 2025)]
        old = a[a["band"].isin(OLD_BANDS)]["count"].sum() / a["count"].sum() * 100
        rows.append({
            "Procedure group": g,
            "Content": CONTENT[g],
            "OPCS-4 codes, n": len(cfg.PROCEDURE_GROUPS[g]["codes"]),
            "Recorded 2012/13": int(round(r.loc[2013, "count"])),
            "Recorded 2024/25": int(round(r.loc[2025, "count"])),
            "ASR 2012/13": round(r.loc[2013, "asr_per_100k"], 1),
            "ASR 2024/25": round(r.loc[2025, "asr_per_100k"], 1),
            "Aged 65 or over 2024/25, %": round(old, 1),
        })
    t = pd.DataFrame(rows)
    total = {
        "Procedure group": "All twelve groups", "Content": "",
        "OPCS-4 codes, n": int(t["OPCS-4 codes, n"].sum()),
        "Recorded 2012/13": int(t["Recorded 2012/13"].sum()),
        "Recorded 2024/25": int(t["Recorded 2024/25"].sum()),
        "ASR 2012/13": "", "ASR 2024/25": "", "Aged 65 or over 2024/25, %": "",
    }
    return pd.concat([t, pd.DataFrame([total])], ignore_index=True)


def table2(dec, var):
    rows = []
    for g in GROUPS:
        row = {"Procedure group": g}
        for tag, period in [("2012/13 to 2018/19", PRE), ("2018/19 to 2024/25", LATER)]:
            d = dec[(dec["group"] == g) & (dec["period"] == period)].iloc[0]
            row[f"{tag}: net change, %"] = round(d["pct_change"], 1)
            row[f"{tag}: population size, %"] = round(d["population_size_pct_of_baseline"], 1)
            row[f"{tag}: age structure, %"] = round(d["age_structure_pct_of_baseline"], 1)
            row[f"{tag}: age-specific rate, %"] = round(d["age_specific_rate_pct_of_baseline"], 1)
        rows.append(row)
    share = {"Procedure group": "Share of between-group variance in net change, %"}
    for tag, period in [("2012/13 to 2018/19", PRE), ("2018/19 to 2024/25", LATER)]:
        v = var[var["period"] == period].iloc[0]
        share[f"{tag}: net change, %"] = 100.0
        share[f"{tag}: population size, %"] = round(v["population_size_share"] * 100, 1)
        share[f"{tag}: age structure, %"] = round(v["age_structure_share"] * 100, 1)
        share[f"{tag}: age-specific rate, %"] = round(v["age_specific_rate_share"] * 100, 1)
    return pd.concat([pd.DataFrame(rows), pd.DataFrame([share])], ignore_index=True)


def table3(proj, by_age):
    pr = proj[(proj["rate_base"] == "2024/25")
              & (proj["variant"] == "Principal projection")].set_index("group")
    ages = by_age.pivot(index="group", columns="age", values="change_n")
    rng = proj.groupby("group")["change_pct"].agg(["min", "max"])
    rows = []
    for g in pr.sort_values("change_pct", ascending=False).index:
        p = pr.loc[g]
        rows.append({
            "Procedure group": g,
            "Scenario base 2024/25": int(round(p["count_2024_25"])),
            "Change, n": int(round(p["change_n"])),
            "Change, %": round(p["change_pct"], 1),
            "Change aged 65 to 79, n": int(round(ages.loc[g, "65-79"])),
            "Change aged 80 and over, n": int(round(ages.loc[g, "80+"])),
            "Population size, %": round(p["population_size_pct"], 1),
            "Age structure, %": round(p["age_structure_pct"], 1),
            "Range across variants and rate bases, %":
                f"{rng.loc[g, 'min']:.1f} to {rng.loc[g, 'max']:.1f}",
        })
    t = pd.DataFrame(rows)
    tot = {
        "Procedure group": "All twelve groups",
        "Scenario base 2024/25": int(round(pr["count_2024_25"].sum())),
        "Change, n": int(round(pr["change_n"].sum())),
        "Change, %": round(pr["change_n"].sum() / pr["count_2024_25"].sum() * 100, 1),
        "Change aged 65 to 79, n": int(round(ages["65-79"].sum())),
        "Change aged 80 and over, n": int(round(ages["80+"].sum())),
        "Population size, %": "", "Age structure, %": "",
        "Range across variants and rate bases, %": "",
    }
    return pd.concat([t, pd.DataFrame([tot])], ignore_index=True)


def code_list():
    u = pyreadr.read_r(str(cfg.RAW / "opcs4_usage.rda"))["opcs4_usage"]
    u["fy"] = pd.to_datetime(u["end_date"]).dt.year
    u["opcs4_code"] = u["opcs4_code"].astype(str)
    latest = (u.sort_values("fy").groupby("opcs4_code")["description"].last())
    rows = []
    for g, spec in cfg.PROCEDURE_GROUPS.items():
        for c in spec["codes"]:
            rows.append({
                "Procedure group": g,
                "Expectation recorded before decomposition": spec["prior"],
                "OPCS-4 code": f"{c[:3]}.{c[3]}",
                "Description (most recent release)": latest.get(c, ""),
            })
    return pd.DataFrame(rows)


def copy_fig(src, dst):
    for ext in ("pdf", "eps", "tiff", "png"):
        s = cfg.FIGURES / f"{src}.{ext}"
        if s.exists():
            shutil.copy2(s, PUB / f"{dst}.{ext}")


def key_results(dec, var, proj, rates, analysis, panel, stable, cf, summ, sub, by_age):
    k = {}
    pre = dec[dec["period"] == PRE].set_index("group")
    lat = dec[dec["period"] == LATER].set_index("group")
    for tag, d in [("pre", pre), ("later", lat)]:
        demo = d["population_size_pct_of_baseline"] + d["age_structure_pct_of_baseline"]
        k[f"{tag}_net_min"] = r1(d["pct_change"].min())
        k[f"{tag}_net_max"] = r1(d["pct_change"].max())
        k[f"{tag}_net_min_group"] = d["pct_change"].idxmin()
        k[f"{tag}_net_max_group"] = d["pct_change"].idxmax()
        k[f"{tag}_pop_min"] = r1(d["population_size_pct_of_baseline"].min())
        k[f"{tag}_pop_max"] = r1(d["population_size_pct_of_baseline"].max())
        k[f"{tag}_age_min"] = r1(d["age_structure_pct_of_baseline"].min())
        k[f"{tag}_age_max"] = r1(d["age_structure_pct_of_baseline"].max())
        k[f"{tag}_age_max_group"] = d["age_structure_pct_of_baseline"].idxmax()
        k[f"{tag}_age_min_group"] = d["age_structure_pct_of_baseline"].idxmin()
        k[f"{tag}_rate_min"] = r1(d["age_specific_rate_pct_of_baseline"].min())
        k[f"{tag}_rate_max"] = r1(d["age_specific_rate_pct_of_baseline"].max())
        k[f"{tag}_demo_min"] = r1(demo.min())
        k[f"{tag}_demo_max"] = r1(demo.max())
        k[f"{tag}_n_age_exceeds_rate_abs"] = int(
            (d["age_structure_pct_of_baseline"].abs()
             > d["age_specific_rate_pct_of_baseline"].abs()).sum())
        k[f"{tag}_n_net_outside_demo_range"] = int(
            ((d["pct_change"] < demo.min()) | (d["pct_change"] > demo.max())).sum())
        v = var[var["period"] == (PRE if tag == "pre" else LATER)].iloc[0]
        k[f"{tag}_share_pop"] = r1(v["population_size_share"] * 100)
        k[f"{tag}_share_age"] = r1(v["age_structure_share"] * 100)
        k[f"{tag}_share_rate"] = r1(v["age_specific_rate_share"] * 100)
        k[f"{tag}_sd_net"] = r1(v["sd_net_change_pp"])
    ea = pre.loc["Extra-axial haematoma evacuation"]
    k["pre_extra_axial_net"] = r1(ea["pct_change"])
    k["pre_extra_axial_pop"] = r1(ea["population_size_pct_of_baseline"])
    k["pre_extra_axial_age"] = r1(ea["age_structure_pct_of_baseline"])
    k["pre_extra_axial_rate"] = r1(ea["age_specific_rate_pct_of_baseline"])
    for g, short in [("Spinal facet joint denervation", "facet"),
                     ("Spinal nerve root injection and denervation", "root"),
                     ("Peripheral nerve entrapment release", "entrapment"),
                     ("CSF diversion, revision and maintenance", "csfrev"),
                     ("Lumbar decompression without fusion", "lumbar"),
                     ("Intracerebral haematoma evacuation", "ich"),
                     ("Neuromodulation implantation", "neuromod"),
                     ("Spinal deformity correction", "deformity")]:
        k[f"pre_{short}_net"] = r1(pre.loc[g, "pct_change"])
        k[f"pre_{short}_rate"] = r1(pre.loc[g, "age_specific_rate_pct_of_baseline"])
        k[f"later_{short}_rate"] = r1(lat.loc[g, "age_specific_rate_pct_of_baseline"])
    # later-period aggregate
    k["later_agg_net_n"] = int(round(lat["total_change"].sum()))
    k["later_agg_demo_n"] = int(round((lat["population_size"] + lat["age_structure"]).sum()))
    k["later_agg_rate_n"] = int(round(lat["age_specific_rate"].sum()))
    base = lat["n1"].sum()
    k["later_agg_base_n"] = int(round(base))
    k["later_agg_net_pct"] = r1(lat["total_change"].sum() / base * 100)
    k["later_agg_demo_pct"] = r1((lat["population_size"] + lat["age_structure"]).sum() / base * 100)
    k["later_agg_rate_pct"] = r1(lat["age_specific_rate"].sum() / base * 100)
    # pre aggregate
    k["pre_agg_net_pct"] = r1(pre["total_change"].sum() / pre["n1"].sum() * 100)
    k["pre_agg_demo_pct"] = r1((pre["population_size"] + pre["age_structure"]).sum() / pre["n1"].sum() * 100)
    # counts
    k["total_occurrences_all_years"] = int(round(rates["count"].sum()))
    k["total_occurrences_2025"] = int(round(rates[rates.fy == 2025]["count"].sum()))
    k["total_occurrences_2013"] = int(round(rates[rates.fy == 2013]["count"].sum()))
    k["n_codes"] = sum(len(s["codes"]) for s in cfg.PROCEDURE_GROUPS.values())
    # pandemic
    r = rates.set_index(["group", "fy"])["asr_per_100k"]
    fall = {g: (r[(g, 2021)] / r[(g, 2020)] - 1) * 100 for g in GROUPS}
    for g, short in [("Neuromodulation implantation", "neuromod"),
                     ("Spinal nerve root injection and denervation", "root"),
                     ("Spinal facet joint denervation", "facet"),
                     ("Peripheral nerve entrapment release", "entrapment"),
                     ("Extra-axial haematoma evacuation", "extra_axial"),
                     ("Intracerebral haematoma evacuation", "ich")]:
        k[f"pandemic_fall_{short}"] = r1(fall[g])
    k["n_groups_below_2019_20_in_2024_25"] = int(sum(r[(g, 2025)] < r[(g, 2020)] for g in GROUPS))
    for g, short in [("Spinal facet joint denervation", "facet"),
                     ("Spinal nerve root injection and denervation", "root"),
                     ("Peripheral nerve entrapment release", "entrapment")]:
        for fy in (2013, 2016, 2017, 2019, 2020, 2025):
            k[f"asr_{short}_{fy}"] = r1(r[(g, fy)])
    conc = pd.read_csv(cfg.TABLES / "tab_code_concentration.csv")
    c25 = conc[conc["fy"] == 2025].set_index("group")["top_code_share"]
    k["groups_top_code_share_ge_85pct_2025"] = {g: r1(v * 100) for g, v in c25.items() if v >= 0.85}
    cm = conc[conc["fy"] == -1].set_index("group")
    k["facet_top_change_code"] = cm.loc["Spinal facet joint denervation", "top_change_code"]
    k["facet_top_change_share_pct"] = r1(cm.loc["Spinal facet joint denervation", "top_change_share_of_group_change"] * 100)
    # scenario
    pr = proj[(proj["rate_base"] == "2024/25") & (proj["variant"] == "Principal projection")].set_index("group")
    k["scen_change_min"] = r1(pr["change_pct"].min())
    k["scen_change_min_group"] = pr["change_pct"].idxmin()
    k["scen_change_max"] = r1(pr["change_pct"].max())
    k["scen_change_max_group"] = pr["change_pct"].idxmax()
    k["scen_age_min"] = r1(pr["age_structure_pct"].min())
    k["scen_age_max"] = r1(pr["age_structure_pct"].max())
    k["scen_pop_min"] = r1(pr["population_size_pct"].min())
    k["scen_pop_max"] = r1(pr["population_size_pct"].max())
    k["scen_total_change_n"] = int(round(pr["change_n"].sum()))
    k["scen_total_base_n"] = int(round(pr["count_2024_25"].sum()))
    k["scen_total_change_pct"] = r1(pr["change_n"].sum() / pr["count_2024_25"].sum() * 100)
    k["scen_n_contract"] = int((pr["change_pct"] < 0).sum())
    # age distribution of the scenario (primary specification)
    tot_age = by_age.groupby("age")[["count_2024_25", "change_n"]].sum()
    base_all, chg_all = tot_age["count_2024_25"].sum(), tot_age["change_n"].sum()
    for a, short in [("0-64", "u65"), ("65-79", "65_79"), ("80+", "80p")]:
        k[f"scen_age_{short}_change_n"] = int(round(tot_age.loc[a, "change_n"]))
        k[f"scen_age_{short}_base_share_pct"] = r1(tot_age.loc[a, "count_2024_25"] / base_all * 100)
        k[f"scen_age_{short}_change_share_pct"] = r1(tot_age.loc[a, "change_n"] / chg_all * 100)
    old_base = tot_age.loc[["65-79", "80+"], "count_2024_25"].sum()
    old_chg = tot_age.loc[["65-79", "80+"], "change_n"].sum()
    k["scen_age_65p_base_share_pct"] = r1(old_base / base_all * 100)
    k["scen_age_65p_change_share_pct"] = r1(old_chg / chg_all * 100)
    k["scen_age_65p_change_n"] = int(round(old_chg))
    eag = by_age[by_age["group"] == "Extra-axial haematoma evacuation"].set_index("age")
    k["scen_extra_axial_80p_change_n"] = int(round(eag.loc["80+", "change_n"]))
    k["scen_extra_axial_80p_change_share_pct"] = r1(eag.loc["80+", "change_n"] / eag["change_n"].sum() * 100)
    k["scen_extra_axial_80p_base_share_pct"] = r1(eag.loc["80+", "count_2024_25"] / eag["count_2024_25"].sum() * 100)
    g80 = by_age[by_age["age"] == "80+"].set_index("group")["change_n"]
    k["scen_80p_change_top_group"] = g80.idxmax()
    k["scen_80p_change_top_n"] = int(round(g80.max()))
    for g, short in [("Extra-axial haematoma evacuation", "extra_axial"),
                     ("Peripheral nerve entrapment release", "entrapment"),
                     ("Spinal nerve root injection and denervation", "root"),
                     ("Spinal deformity correction", "deformity"),
                     ("CSF diversion, revision and maintenance", "csfrev")]:
        k[f"scen_{short}_n"] = int(round(pr.loc[g, "change_n"]))
        k[f"scen_{short}_pct"] = r1(pr.loc[g, "change_pct"])
        k[f"scen_{short}_base"] = int(round(pr.loc[g, "count_2024_25"]))
    rng = proj.groupby("group")["change_pct"].agg(["min", "max"])
    k["scen_range_extra_axial"] = [r1(rng.loc["Extra-axial haematoma evacuation", "min"]),
                                   r1(rng.loc["Extra-axial haematoma evacuation", "max"])]
    k["scen_range_deformity"] = [r1(rng.loc["Spinal deformity correction", "min"]),
                                 r1(rng.loc["Spinal deformity correction", "max"])]
    k["scen_extra_axial_age_per_year"] = round(pr.loc["Extra-axial haematoma evacuation", "age_structure_pct"] / 15, 2)
    k["pre_extra_axial_age_per_year"] = round(ea["age_structure_pct_of_baseline"] / 6, 2)
    s = summ.set_index("statistic")
    for col, name in [("observed_age_structure_pp_per_year", "obs_age_py"),
                      ("projected_age_structure_pp_per_year", "proj_age_py"),
                      ("observed_total_demographic_pp_per_year", "obs_demo_py"),
                      ("projected_total_demographic_pp_per_year", "proj_demo_py")]:
        k[f"{name}_mean"] = round(s.loc["mean", col], 2)
        k[f"{name}_sd"] = round(s.loc["standard deviation", col], 2)
        k[f"{name}_min"] = round(s.loc["minimum", col], 2)
        k[f"{name}_max"] = round(s.loc["maximum", col], 2)
    # robustness
    loo = panel[panel["specification"] == "Leave one group out"]["age_specific_rate_share"]
    k["loo_rate_share_min"] = r1(loo.min() * 100)
    k["loo_rate_share_max"] = r1(loo.max() * 100)
    pick = lambda spec: r1(panel[panel["specification"] == spec]["age_specific_rate_share"].iloc[0] * 100)
    k["weighted_rate_share"] = pick("Baseline-volume-weighted percentage change")
    k["absolute_rate_share"] = pick("Equal-weight absolute count change")
    k["subset_rate_share_min"] = pick("Six-group subsets: minimum rate share")
    k["subset_rate_share_max"] = pick("Six-group subsets: maximum rate share")
    k["subset_rate_share_p05"] = pick("Six-group subset rate-share 5th percentile")
    k["subset_rate_share_median"] = pick("Six-group subset rate-share median")
    k["subset_rate_share_p95"] = pick("Six-group subset rate-share 95th percentile")
    cv = panel[panel["specification"].str.startswith("Counting variant")]["age_specific_rate_share"]
    sc = panel[panel["specification"].str.startswith("Stable-code")]["age_specific_rate_share"]
    k["counting_variant_rate_share_min"] = r1(cv.min() * 100)
    k["counting_variant_rate_share_max"] = r1(cv.max() * 100)
    k["stable_code_rate_share_min"] = r1(sc.min() * 100)
    k["stable_code_max_component_diff_pp"] = r1(stable[["difference_population_size_pp",
                                                        "difference_age_structure_pp",
                                                        "difference_age_specific_rate_pp"]].abs().max().max())
    sh = pd.read_csv(cfg.DERIVED / "shapley_comparison.csv")
    k["shapley_max_diff_pp"] = round(sh[[c for c in sh.columns if c.endswith("_abs_diff_pp")]].max().max(), 3)
    alt = pd.read_csv(cfg.DERIVED / "alternative_endpoints.csv")
    cum = pd.read_csv(cfg.DERIVED / "cumulative_annual.csv")
    agecols = [c for c in alt.columns if "age_structure" in c]
    ratecols = [c for c in alt.columns if "age_specific_rate" in c]
    ages = pd.concat([alt[agecols[0]], cum[[c for c in cum.columns if "age_structure" in c][0]]])
    rates_ = pd.concat([alt[ratecols[0]], cum[[c for c in cum.columns if "age_specific_rate" in c][0]]])
    k["endpoint_age_min"] = r1(ages.min())
    k["endpoint_age_max"] = r1(ages.max())
    k["endpoint_rate_min"] = r1(rates_.min())
    k["endpoint_rate_max"] = r1(rates_.max())
    cov = pd.read_csv(cfg.DERIVED / "code_coverage.csv")
    k["n_codes_absent_any_year"] = int((cov["n_missing_years"] > 0).sum())
    k["absent_code_years"] = int(cov["n_missing_years"].sum())
    checks = pd.read_csv(cfg.DERIVED / "build_checks.csv")
    c2 = checks[checks["check"] == "C2_age_allocation"]["value"]
    k["age_allocation_min_pct"] = r1(c2.min() * 100)
    k["age_allocation_median_pct"] = r1(c2.median() * 100)
    scr = pd.read_csv(cfg.TABLES / "tab_revision_screen.csv")
    flagged = scr[(scr["flagged"]) & (~scr["pandemic_confounded"])]
    k["revision_flags_code_level"] = int((flagged["opcs4_code"] != "(group total)").sum())
    k["revision_flags_group_level"] = flagged[flagged["opcs4_code"] == "(group total)"]["group"].tolist()
    k["sub_d_75plus"] = int(sub.iloc[0]["Change D"])
    k["sub_e_75plus"] = int(sub.iloc[0]["Change E"])
    cvt = pd.read_csv(cfg.TABLES / "tab_counting_variants.csv")
    for g, short in [("Intracerebral haematoma evacuation", "ich"),
                     ("CSF diversion, revision and maintenance", "csfrev")]:
        x = cvt[cvt["Procedure group"] == g]["Age-specific rate, % of baseline"]
        k[f"counting_variant_rate_range_{short}"] = [r1(x.min()), r1(x.max())]
    demo_cols = ["Population size, % of baseline", "Age structure, % of baseline"]
    spread = cvt.groupby("Procedure group")[demo_cols].agg(lambda s: s.max() - s.min())
    k["counting_variant_demo_max_spread_pp"] = round(float(spread.max().max()), 2)
    return k


def write_results_summary(k):
    """RESULTS.md: plain-language summary generated from key_results.json."""
    txt = f"""# Results summary

This file is generated by `src/s13_publication.py` from
`derived/key_results.json`. Do not edit by hand.

## Data

Twelve groups of OPCS-4 procedure codes ({k['n_codes']} four-character codes)
recorded in NHS admitted patient care in England contributed
{k['total_occurrences_all_years']:,} code occurrences between 2012/13 and
2024/25 ({k['total_occurrences_2025']:,} in 2024/25). Age bands were allocated
for {k['age_allocation_min_pct']} to 100 per cent of each group-year total
(median {k['age_allocation_median_pct']}).

## Observed change, 2012/13 to 2018/19

- Net change ranged from {k['pre_net_min']} per cent ({k['pre_net_min_group']})
  to {k['pre_net_max']} per cent ({k['pre_net_max_group']}).
- Population growth contributed {k['pre_pop_min']} to {k['pre_pop_max']} per
  cent and age structure {k['pre_age_min']} to {k['pre_age_max']} per cent;
  demographic change together contributed {k['pre_demo_min']} to
  {k['pre_demo_max']} per cent.
- The age-specific rate component ranged from {k['pre_rate_min']} to
  {k['pre_rate_max']} per cent.
- Shares of between-group variance in net change: age-specific rate
  {k['pre_share_rate']} per cent, population size {k['pre_share_pop']} per
  cent, age structure {k['pre_share_age']} per cent.

## Later period, 2018/19 to 2024/25

Across all groups, demographic change would have added
{k['later_agg_demo_n']:,} code occurrences ({k['later_agg_demo_pct']} per cent
of the 2018/19 total); the age-specific rate component was
{k['later_agg_rate_n']:,} ({k['later_agg_rate_pct']} per cent) and net change
{k['later_agg_net_n']:,} ({k['later_agg_net_pct']} per cent).

## Fixed-rate demographic scenario, 2024/25 to 2039/40

With age-specific rates held at 2024/25 values and the ONS 2024-based
principal projection, scenario change ranged from {k['scen_change_min']} per
cent ({k['scen_change_min_group']}) to {k['scen_change_max']} per cent
({k['scen_change_max_group']}); the age-structure component ranged from
{k['scen_age_min']} to {k['scen_age_max']} per cent. Across groups the
scenario adds {k['scen_total_change_n']:,} annual code occurrences
({k['scen_total_change_pct']} per cent). People aged 65 or over account for
{k['scen_age_65p_base_share_pct']} per cent of the scenario base and
{k['scen_age_65p_change_share_pct']} per cent of the scenario increase; people
aged 80 or over account for {k['scen_age_80p_base_share_pct']} and
{k['scen_age_80p_change_share_pct']} per cent respectively.

## Sensitivity

The age-specific rate share of between-group variance was
{k['loo_rate_share_min']} to {k['loo_rate_share_max']} per cent when each
group was omitted in turn, {k['weighted_rate_share']} per cent with
baseline-volume weighting, {k['absolute_rate_share']} per cent on the
absolute-count scale and {k['subset_rate_share_p05']} to
{k['subset_rate_share_p95']} per cent (5th to 95th percentile) across all
924 six-group subsets.
"""
    (cfg.ROOT / "RESULTS.md").write_text(txt)


def main():
    PUB.mkdir(parents=True, exist_ok=True)
    for f in PUB.glob("*"):
        f.unlink()
    dec = pd.read_csv(cfg.DERIVED / f"decomposition_{PRIMARY_TAG}.csv")
    rates = pd.read_csv(cfg.DERIVED / f"rates_{PRIMARY_TAG}.csv")
    analysis = pd.read_csv(cfg.DERIVED / f"analysis_{PRIMARY_TAG}.csv")
    var = pd.read_csv(cfg.DERIVED / "variance_decomposition.csv")
    proj = pd.read_csv(cfg.DERIVED / "projection_2040.csv")
    by_age = pd.read_csv(cfg.DERIVED / "projection_2040_by_age.csv")
    panel = pd.read_csv(cfg.DERIVED / "selected_panel_robustness.csv")
    stable = pd.read_csv(cfg.DERIVED / "stable_code_sensitivity.csv")
    cf = pd.read_csv(cfg.DERIVED / "demographic_counterfactual.csv")
    summ = pd.read_csv(cfg.DERIVED / "projection_per_year_summary.csv")
    sub = pd.read_csv(cfg.TABLES / "tab_substitution_check.csv")

    items = []
    t1, t2, t3 = table1(rates, analysis), table2(dec, var), table3(proj, by_age)
    for n, t, cap in [(1, t1, "Procedure groups, recorded code occurrences and age-standardised rates"),
                      (2, t2, "Decomposition of change in recorded code occurrences, two periods"),
                      (3, t3, "Fixed-rate demographic scenario, 2024/25 to 2039/40")]:
        t.to_csv(PUB / f"Table{n}.csv", index=False)
        items.append((f"Table {n}", cap))

    scr = pd.read_csv(cfg.TABLES / "tab_revision_screen.csv")
    scr_flag = scr[scr["flagged"]].copy()
    grid = proj[["group", "rate_base", "variant", "count_2024_25", "count_2039_40",
                 "change_n", "change_pct", "population_size_pct", "age_structure_pct"]].round(2)
    supp_tables = [
        (code_list(), "OPCS-4 codes defining each procedure group, with the expectation recorded before the decomposition was calculated"),
        (pd.read_csv(cfg.TABLES / "tab_age_allocation.csv"), "Proportion of recorded code occurrences with an allocated age band, by group and financial year"),
        (pd.read_csv(cfg.TABLES / "tab_annual_rates.csv"), "Annual recorded code occurrences, crude rates and age-standardised rates per 100 000"),
        (pd.read_csv(cfg.TABLES / "tab_variance_decomposition.csv"), "Covariance decomposition of between-group variance in net change, all comparison periods"),
        (pd.read_csv(cfg.TABLES / "tab_demographic_counterfactual.csv"), "Demographic counterfactual (age-specific rates held at baseline) against observed change"),
        (pd.read_csv(cfg.TABLES / "tab_pandemic_disruption.csv"), "Change in age-standardised rates between 2019/20 and 2020/21, and 2024/25 relative to 2019/20"),
        (pd.read_csv(cfg.TABLES / "tab_phase_decomposition.csv"), "Decomposition over the pre-pandemic, pandemic and recovery phases"),
        (grid, "Scenario results for every combination of rate base and ONS population variant"),
        (pd.read_csv(cfg.TABLES / "tab_projection_per_year.csv"), "Average contribution per year of interval: observed 2012/13 to 2018/19 and scenario 2024/25 to 2039/40"),
        (pd.read_csv(cfg.TABLES / "tab_shapley_comparison.csv"), "Symmetric (Kitagawa) and Shapley allocation of the three components, 2012/13 to 2018/19"),
        (pd.read_csv(cfg.TABLES / "tab_alternative_endpoints.csv"), "Decomposition with alternative endpoints"),
        (pd.read_csv(cfg.TABLES / "tab_cumulative_annual.csv"), "Consecutive-year decompositions cumulated over 2012/13 to 2019/20"),
        (pd.read_csv(cfg.TABLES / "tab_counting_variants.csv"), "Decomposition under six counting conventions, 2012/13 to 2018/19"),
        (pd.read_csv(cfg.TABLES / "tab_selected_panel_robustness.csv"), "Between-group variance shares under alternative panels, weights, scales, code sets and counting conventions"),
        (pd.read_csv(cfg.TABLES / "tab_stable_code_sensitivity.csv"), "Decomposition restricted to codes present throughout the study or primary window"),
        (pd.read_csv(cfg.TABLES / "tab_code_concentration.csv"), "Concentration of each group across its constituent codes"),
        (scr_flag, "Level shifts at OPCS-4 revision boundaries exceeding the code's typical year-on-year variability (flagged rows; the full screen is in the analysis repository)"),
        (sub, "Extra-axial haematoma evacuation and candidate embolisation codes, 2018/19 to 2024/25"),
        (pd.read_csv(cfg.TABLES / "tab_embolisation_age_profile.csv"), "Age profile of candidate embolisation codes, 2018/19 and 2024/25"),
    ]
    for i, (t, cap) in enumerate(supp_tables, 1):
        t.to_csv(PUB / f"TableS{i}.csv", index=False)
        items.append((f"Table S{i}", cap))

    copy_fig("fig_demographic_vs_observed", "Fig1")
    items.append(("Fig. 1", "Demographic change against observed change by procedure group, two periods"))
    copy_fig("fig_scenario_2039", "Fig2")
    items.append(("Fig. 2", "Fixed-rate demographic scenario, 2024/25 to 2039/40"))
    supp_figs = [
        ("fig_asr_trajectories", "Age-standardised rates per 100 000, 2012/13 to 2024/25"),
        ("fig_age_specific_profiles", "Age-specific rates in 2012/13, 2018/19 and 2024/25"),
        ("fig_decomposition_components", "Three-component decomposition by group, two periods"),
        ("fig_counterfactual_scatter", "Demographic counterfactual against observed change, 2012/13 to 2018/19"),
        ("fig_age_structure_observed_vs_scenario", "Age-structure contribution per year of interval, observed and scenario"),
        ("fig_counting_sensitivity", "Components under six counting conventions"),
        ("fig_code_level_trends", "Constituent-code trends in the four groups with the largest rate components"),
    ]
    for i, (src, cap) in enumerate(supp_figs, 1):
        copy_fig(src, f"FigS{i}")
        items.append((f"Fig. S{i}", cap))

    with open(PUB / "CAPTIONS.md", "w") as f:
        f.write("# Publication display items\n\n")
        for lab, cap in items:
            f.write(f"- **{lab}.** {cap}\n")

    k = key_results(dec, var, proj, rates, analysis, panel, stable, cf, summ, sub, by_age)
    with open(cfg.DERIVED / "key_results.json", "w") as f:
        json.dump(k, f, indent=1, sort_keys=True)
    write_results_summary(k)
    print(f"  {len(items)} display items written to outputs/publication/")
    print(f"  {len(k)} key results written to derived/key_results.json")


if __name__ == "__main__":
    main()
