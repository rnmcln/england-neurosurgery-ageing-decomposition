"""
Step 11. Code-level screen within groups.

The dependent quantity throughout the study is OPCS-4 code occurrences, so
changes in how constituent codes are used enter the age-specific rate
component directly. This step screens the 125 constituent codes empirically:

  A  code-level annual counts for every constituent code
     (derived/code_level_counts.csv)
  B  concentration of each group's count across its constituent codes over
     time: top-code share and normalised Shannon entropy, plus the share of
     each group's pre-pandemic change contributed by its largest single
     contributor (tableS14)
  C  a revision-boundary screen: for each code, the year-on-year log change
     in the first financial year recorded under each new OPCS-4 version
     (4.7 in 2014/15, 4.8 in 2017/18, 4.9 in 2020/21, 4.10 in 2023/24) is
     compared with that code's typical year-on-year variability. A change
     exceeding three times the code's median absolute non-revision log change,
     with an absolute change of at least 50 occurrences, is flagged
     (tableS15). 2020/21 flags are confounded by the pandemic and are listed
     but not interpretable.

This is an empirical screen for discontinuities coincident with coding
revisions. It does not replace a documentary audit of OPCS-4 revision
notes, which requires the TRUD release documentation.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg

FLAG_RATIO = 3.0
FLAG_MIN_ABS = 50


def load_code_counts():
    raw = pyreadr.read_r(str(cfg.RAW / "opcs4_usage.rda"))["opcs4_usage"]
    raw["usage"] = pd.to_numeric(raw["usage"])
    raw["fy"] = pd.to_datetime(raw["end_date"]).dt.year
    raw["opcs4_code"] = raw["opcs4_code"].astype(str)
    code_to_group = {
        c: g for g, s in cfg.PROCEDURE_GROUPS.items() for c in s["codes"]
    }
    raw = raw[raw["opcs4_code"].isin(code_to_group)].copy()
    raw["group"] = raw["opcs4_code"].map(code_to_group)
    return raw.groupby(["group", "opcs4_code", "fy"], as_index=False)[
        "usage"
    ].sum()


def concentration(cc):
    rows = []
    y1, y2 = cfg.PERIODS[cfg.PRIMARY_PERIOD]
    for group, g in cc.groupby("group"):
        wide = g.pivot_table(index="opcs4_code", columns="fy", values="usage",
                             aggfunc="sum").fillna(0.0)
        n_codes = len(wide)
        for fy in sorted(wide.columns):
            v = wide[fy].to_numpy(float)
            tot = v.sum()
            p = v[v > 0] / tot
            entropy = float(-(p * np.log(p)).sum())
            norm_entropy = entropy / np.log(n_codes) if n_codes > 1 else np.nan
            rows.append(
                {
                    "group": group,
                    "fy": int(fy),
                    "n_codes": n_codes,
                    "top_code_share": float(v.max() / tot),
                    "normalised_entropy": norm_entropy,
                }
            )
        # share of pre-pandemic group change contributed by the single code
        # with the largest absolute change
        delta = wide[y2] - wide[y1]
        total_delta = delta.sum()
        top = delta.abs().idxmax()
        rows.append(
            {
                "group": group,
                "fy": -1,  # summary row marker
                "n_codes": n_codes,
                "top_code_share": np.nan,
                "normalised_entropy": np.nan,
                "top_change_code": top,
                "top_change_share_of_group_change": (
                    float(delta.loc[top] / total_delta)
                    if abs(total_delta) > 0
                    else np.nan
                ),
            }
        )
    return pd.DataFrame(rows)


def revision_screen(cc):
    """Code-level and group-level screens with the same criterion. Group
    totals are screened because offsetting within-group code substitution
    (which the code-level screen detects) need not move the group total."""
    rows = []
    grouped = pd.concat(
        [
            cc,
            cc.groupby(["group", "fy"], as_index=False)["usage"]
            .sum()
            .assign(opcs4_code="(group total)"),
        ],
        ignore_index=True,
    )
    for (group, code), g in grouped.groupby(["group", "opcs4_code"]):
        s = g.set_index("fy")["usage"].sort_index()
        s = s.reindex(range(2013, 2026)).fillna(0.0)
        with np.errstate(divide="ignore"):
            logr = np.log((s + 0.5) / (s.shift(1) + 0.5)).dropna()
        non_rev = logr[~logr.index.isin(cfg.OPCS_REVISION_FYS)]
        med = non_rev.abs().median()
        for fy in cfg.OPCS_REVISION_FYS:
            if fy not in logr.index:
                continue
            change = float(s[fy] - s[fy - 1])
            flagged = (
                med > 0
                and abs(logr[fy]) > FLAG_RATIO * med
                and abs(change) >= FLAG_MIN_ABS
            )
            rows.append(
                {
                    "group": group,
                    "opcs4_code": code,
                    "revision_fy": fy,
                    "count_before": float(s[fy - 1]),
                    "count_at": float(s[fy]),
                    "log_change": float(logr[fy]),
                    "median_abs_nonrevision_log_change": float(med),
                    "flagged": flagged,
                    "pandemic_confounded": fy == 2021,
                }
            )
    return pd.DataFrame(rows)


def main():
    cc = load_code_counts()
    cc.to_csv(cfg.DERIVED / "code_level_counts.csv", index=False)

    conc = concentration(cc)
    conc.to_csv(cfg.TABLES / "tab_code_concentration.csv", index=False)

    scr = revision_screen(cc)
    scr.to_csv(cfg.TABLES / "tab_revision_screen.csv", index=False)

    flagged = scr[scr["flagged"]]
    interp = flagged[~flagged["pandemic_confounded"]]
    code_flags = interp[interp["opcs4_code"] != "(group total)"]
    group_flags = interp[interp["opcs4_code"] == "(group total)"]
    print(f"  code_level_counts.csv ({cc['opcs4_code'].nunique()} codes)")
    print(f"  tab_code_concentration.csv, tab_revision_screen.csv")
    print(
        f"  revision screen (excluding pandemic-confounded 2020/21): "
        f"{len(code_flags)} constituent-code flags, "
        f"{len(group_flags)} group-total flags"
    )
    if len(group_flags):
        print(group_flags[["group", "revision_fy", "count_before",
                           "count_at"]].to_string(index=False))


if __name__ == "__main__":
    main()
