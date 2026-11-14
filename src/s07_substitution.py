"""
Step 7. Substitution check.

The extra-axial haematoma evacuation rate fell after 2018/19. Two explanations
are observationally equivalent within chapter A: falling disease burden or
falling operative treatment, and displacement of treatment to endovascular
embolisation, which is coded outside chapter A and is therefore invisible to
the primary analysis.

This step tests whether the second explanation is arithmetically compatible
with the data. It is a bounding exercise, not an identification strategy.

Method. OPCS-4 has no code specific to middle meningeal artery embolisation.
The candidate landing codes are L713 (percutaneous transluminal embolisation
of artery, site unspecified) and the cerebral artery codes L351 and L344. L713
is dominated by unrelated indications, principally visceral and gynaecological
embolisation, so its total is uninformative. The discriminating quantity is
growth confined to the age bands in which extra-axial haematoma occurs.

The test compares, over 2018/19 to 2024/25 and within the 75 and over bands:
  D  the fall in extra-axial haematoma evacuation counts
  E  the rise in candidate embolisation counts

If E is small relative to D, substitution cannot account for the fall. If E is
comparable to or larger than D, substitution remains possible but is not
demonstrated, because the embolisation codes are not specific to the
indication.

Interpretive limit. Because no available code identifies middle meningeal
artery embolisation, this check cannot reject or confirm substitution. What it
can establish is whether the candidate codes provide a temporally and
demographically credible proxy for it; on these data they do not, so the
question is left unquantifiable rather than answered. This analysis is
supplementary.
"""

import sys
from pathlib import Path

import pandas as pd
import pyreadr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg

CANDIDATE_CODES = {
    "L713": "Percutaneous transluminal embolisation of artery, site unspecified",
    "L351": "Percutaneous transluminal embolisation of cerebral artery",
    "L344": "Open embolisation of cerebral artery",
}
OLDER_BANDS = ["75-79", "80-84", "85-89", "90+"]
Y1, Y2 = 2019, 2025


def embolisation_by_band():
    bd = pyreadr.read_r(str(cfg.RAW / "opcs4_usage_breakdowns.rda"))[
        "opcs4_usage_breakdowns"
    ]
    bd["usage"] = pd.to_numeric(bd["usage"])
    bd["fy"] = pd.to_datetime(bd["end_date"]).dt.year
    bd["opcs4_code"] = bd["opcs4_code"].astype(str)
    bd["breakdown"] = bd["breakdown"].astype(str)

    sub = bd[
        bd["opcs4_code"].isin(CANDIDATE_CODES)
        & bd["breakdown"].isin(cfg.BREAKDOWN_TO_BAND)
    ].copy()
    sub["band"] = sub["breakdown"].map(cfg.BREAKDOWN_TO_BAND)
    return sub.groupby(["fy", "band"], as_index=False)["usage"].sum().rename(
        columns={"usage": "count"}
    )


def main():
    emb = embolisation_by_band()
    tag = f"{cfg.COUNT_BASIS}__{cfg.UNKNOWN_AGE_HANDLING}"
    analysis = pd.read_csv(cfg.DERIVED / f"analysis_{tag}.csv")
    hae = analysis[analysis["group"] == "Extra-axial haematoma evacuation"]

    rows = []
    for label, bands in [("75 and over", OLDER_BANDS), ("all ages", cfg.AGE_BANDS)]:
        h1 = hae[(hae.fy == Y1) & (hae.band.isin(bands))]["count"].sum()
        h2 = hae[(hae.fy == Y2) & (hae.band.isin(bands))]["count"].sum()
        e1 = emb[(emb.fy == Y1) & (emb.band.isin(bands))]["count"].sum()
        e2 = emb[(emb.fy == Y2) & (emb.band.isin(bands))]["count"].sum()
        rows.append(
            {
                "Age stratum": label,
                "Haematoma evacuation 2018/19": round(h1),
                "Haematoma evacuation 2024/25": round(h2),
                "Change D": round(h2 - h1),
                "Embolisation 2018/19": int(e1),
                "Embolisation 2024/25": int(e2),
                "Change E": int(e2 - e1),
                "E as % of |D|": (
                    round((e2 - e1) / abs(h2 - h1) * 100, 1)
                    if abs(h2 - h1) > 0
                    else None
                ),
            }
        )
    summary = pd.DataFrame(rows)

    # Concentration of embolisation growth in older bands, as a second signal.
    wide = emb.pivot_table(index="band", columns="fy", values="count", aggfunc="sum")
    wide = wide.reindex(cfg.AGE_BANDS)
    profile = pd.DataFrame(
        {
            "Age band": wide.index,
            "Embolisation 2018/19": wide[Y1].astype("Int64"),
            "Embolisation 2024/25": wide[Y2].astype("Int64"),
            "Change": (wide[Y2] - wide[Y1]).astype("Int64"),
        }
    )
    older_share = (
        profile[profile["Age band"].isin(OLDER_BANDS)]["Change"].sum()
        / profile["Change"].sum()
        * 100
    )

    cfg.TABLES.mkdir(parents=True, exist_ok=True)
    summary.to_csv(cfg.TABLES / "tab_substitution_check.csv", index=False)
    profile.to_csv(cfg.TABLES / "tab_embolisation_age_profile.csv", index=False)

    print(summary.to_string(index=False))
    print()
    print(f"  share of total embolisation growth occurring at 75 and over: "
          f"{older_share:.1f}%")
    print(f"  population share aged 75 and over, 2024: "
          f"{_pop_share_75plus(analysis):.1f}%")
    print("  tab_substitution_check.csv, tab_embolisation_age_profile.csv")

    return summary, older_share


def _pop_share_75plus(analysis):
    p = analysis.drop_duplicates(["mye_year", "band"])
    p = p[p["mye_year"] == p["mye_year"].max()]
    return p[p["band"].isin(OLDER_BANDS)]["population"].sum() / p["population"].sum() * 100


if __name__ == "__main__":
    main()
