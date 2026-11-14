"""
Step 5. Figures.

Design: Tufte-inspired minimalism, maximum data-ink ratio, sans-serif type, no titles
or explanatory text inside the graphic (explanation belongs in the article
legend), thin axes and ticks, no chart boxes, no gridlines unless essential,
mostly greyscale with one muted accent colour, point estimates in preference
to bars, direct labelling in preference to legends where space allows, flat
design. Each figure is written as vector PDF and EPS, 600 dpi TIFF and
400 dpi PNG. Symbol encodings are explained in the figure legends of the
article rather than in keys inside the graphic.

Colour encoding (consistent across all figures, and never the only encoding;
marker shape and position also distinguish series):
  population size    light grey, open marker
  age structure      dark grey, filled marker
  age-specific rate  muted indigo accent, filled marker
  net change         black, small diamond
"""

import sys
import textwrap
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg

PRIMARY_TAG = f"{cfg.COUNT_BASIS}__{cfg.UNKNOWN_AGE_HANDLING}"
DPI = 400

GREY_LIGHT = "#B8B8B8"
GREY_MID = "#7A7A7A"
GREY_DARK = "#3A3A3A"
BLACK = "#1A1A1A"
ACCENT = "#5B6B9E"   # muted indigo, colourblind-safe against greys
BAND = "#EDEDED"     # background band shading

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "Liberation Sans", "DejaVu Sans"],
    "font.size": 7,
    "axes.labelsize": 7,
    "axes.titlesize": 7,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "legend.fontsize": 6.5,
    "axes.edgecolor": GREY_MID,
    "axes.labelcolor": GREY_DARK,
    "text.color": GREY_DARK,
    "xtick.color": GREY_MID,
    "ytick.color": GREY_MID,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.5,
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "lines.linewidth": 0.8,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "pdf.fonttype": 42,
    "legend.frameon": False,
})

GROUPS = list(cfg.PROCEDURE_GROUPS)


def wrap(s, w=26):
    return "\n".join(textwrap.wrap(s, w))


def fy_label(y):
    return f"{str(y-1)[2:]}/{str(y)[2:]}"


def save(fig, name):
    cfg.FIGURES.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf", "eps"):
        fig.savefig(cfg.FIGURES / f"{name}.{ext}", dpi=DPI, bbox_inches="tight")
    fig.savefig(cfg.FIGURES / f"{name}.tiff", dpi=600, bbox_inches="tight",
                pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)
    print(f"  {name}.pdf / .eps / .tiff / .png")


# ---------------------------------------------------------------------------

def fig_decomposition_components(dec):
    """Dot plot of the three components and net change, two periods."""
    periods = cfg.DISPLAY_PERIODS
    panel_labels = ["2012/13 to 2018/19", "2018/19 to 2024/25"]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 4.4), sharey=True)
    ypos = np.arange(len(GROUPS))[::-1]

    series = [
        ("population_size_pct_of_baseline", "Population size",
         dict(marker="o", mfc="white", mec=GREY_LIGHT, mew=0.9, ms=3.4)),
        ("age_structure_pct_of_baseline", "Age structure",
         dict(marker="o", mfc=GREY_DARK, mec=GREY_DARK, mew=0, ms=3.4)),
        ("age_specific_rate_pct_of_baseline", "Age-specific rate",
         dict(marker="o", mfc=ACCENT, mec=ACCENT, mew=0, ms=3.4)),
        ("pct_change", "Net change",
         dict(marker="D", mfc=BLACK, mec=BLACK, mew=0, ms=2.6)),
    ]

    sub = dec[dec["period"].isin(periods)]
    vals = pd.concat([sub[c] for c, _, _ in series])
    lim = (vals.min() - 4, vals.max() + 4)

    for ax, period, plab in zip(axes, periods, panel_labels):
        d = dec[dec["period"] == period].set_index("group").loc[GROUPS]
        for i, y in enumerate(ypos):
            if i % 2 == 0:
                ax.axhspan(y - 0.5, y + 0.5, color=BAND, lw=0, zorder=0)
        ax.axvline(0, color=GREY_MID, lw=0.5, zorder=1)
        for col, lab, style in series:
            ax.plot(d[col], ypos, ls="none", zorder=3,
                    label=lab if ax is axes[0] else None, **style)
        ax.set_yticks(ypos)
        ax.set_yticklabels([wrap(g, 28) for g in GROUPS])
        ax.set_xlim(lim)
        ax.set_xlabel("Contribution, % of baseline-year count")
        ax.text(0.0, 1.02, plab, transform=ax.transAxes, fontsize=7,
                color=GREY_DARK, ha="left")
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
    fig.tight_layout()
    save(fig, "fig_decomposition_components")


def fig2_scenario(dec, proj):
    """Observed against scenario age-structure contribution, per year."""
    pre = dec[dec["period"] == cfg.PRIMARY_PERIOD].set_index("group")
    pr = proj[
        (proj["rate_base"] == "2024/25")
        & (proj["variant"] == "Principal projection")
    ].set_index("group")
    prng = proj[proj["rate_base"] == "2024/25"].groupby("group")["age_structure_pct"]

    obs = (pre["age_structure_pct_of_baseline"] / 6).loc[GROUPS]
    fut = (pr["age_structure_pct"] / 15).loc[GROUPS]
    lo = (prng.min() / 15).loc[GROUPS]
    hi = (prng.max() / 15).loc[GROUPS]

    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    ypos = np.arange(len(GROUPS))[::-1]
    for i, y in enumerate(ypos):
        if i % 2 == 0:
            ax.axhspan(y - 0.5, y + 0.5, color=BAND, lw=0, zorder=0)
    ax.hlines(ypos, lo, hi, color=GREY_LIGHT, lw=2.4, zorder=2,
              label="Range across ONS variants")
    ax.axvline(0, color=GREY_MID, lw=0.5, zorder=1)
    ax.plot(obs, ypos, "o", mfc="white", mec=GREY_DARK, mew=0.9, ms=3.8,
            ls="none", label="Observed, 2012/13 to 2018/19", zorder=4)
    ax.plot(fut, ypos, "o", mfc=ACCENT, mec=ACCENT, ms=3.8, ls="none",
            label="Scenario, 2024/25 to 2039/40", zorder=4)
    ax.set_yticks(ypos)
    ax.set_yticklabels([wrap(g, 28) for g in GROUPS])
    ax.set_xlabel("Age-structure contribution, % of baseline count per year")
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    fig.tight_layout()
    save(fig, "fig_age_structure_observed_vs_scenario")


SHORT = {
    "Extra-axial haematoma evacuation": "Extra-axial haematoma evacuation",
    "Intracerebral haematoma evacuation": "Intracerebral haematoma evacuation",
    "Intracranial tumour resection and biopsy": "Intracranial tumour resection/biopsy",
    "CSF diversion, primary": "CSF diversion, primary",
    "CSF diversion, revision and maintenance": "CSF diversion, revision",
    "Peripheral nerve entrapment release": "Peripheral nerve entrapment release",
    "Neuromodulation implantation": "Neuromodulation implantation",
    "Spinal nerve root injection and denervation": "Spinal nerve root injection",
    "Lumbar decompression without fusion": "Lumbar decompression",
    "Spinal fusion and instrumentation": "Spinal fusion",
    "Spinal deformity correction": "Spinal deformity correction",
    "Spinal facet joint denervation": "Facet joint denervation",
}


def fig_demographic_vs_observed(dec):
    """Main Fig. 1. Change expected from demographic change alone (population
    size plus age structure; open circles) against observed net change (filled
    circles), by group, in the primary and later periods. The connecting
    segment is the age-specific rate component. The shaded band spans the
    range of demographic change across groups within each period."""
    periods = cfg.DISPLAY_PERIODS
    pre = dec[dec["period"] == periods[0]].set_index("group")
    order = pre["pct_change"].sort_values(ascending=True).index.tolist()
    ypos = np.arange(len(order))
    fig, axes = plt.subplots(1, 2, figsize=(6.85, 3.5), sharey=True,
                             gridspec_kw={"wspace": 0.08})
    allv = dec[dec["period"].isin(periods)]
    demo_all = allv["population_size_pct_of_baseline"] + allv["age_structure_pct_of_baseline"]
    lo = min(allv["pct_change"].min(), demo_all.min()) - 4
    hi = max(allv["pct_change"].max(), demo_all.max()) + 4
    for k, (ax, period) in enumerate(zip(axes, periods)):
        d = dec[dec["period"] == period].set_index("group").loc[order]
        demo = d["population_size_pct_of_baseline"] + d["age_structure_pct_of_baseline"]
        obs = d["pct_change"]
        ax.axvspan(demo.min(), demo.max(), color=BAND, lw=0, zorder=0)
        ax.axvline(0, color=GREY_MID, lw=0.5, zorder=1)
        ax.hlines(ypos, np.minimum(demo, obs), np.maximum(demo, obs),
                  color=GREY_LIGHT, lw=0.8, zorder=2)
        ax.plot(demo, ypos, "o", mfc="white", mec=GREY_DARK, mew=0.7, ms=3.6,
                ls="none", zorder=3)
        ax.plot(obs, ypos, "o", mfc=ACCENT, mec=ACCENT, mew=0, ms=3.8,
                ls="none", zorder=4)
        ax.set_xlim(lo, hi)
        ax.set_ylim(-0.7, len(order) - 0.3)
        ax.set_xlabel("Change from baseline year, %")
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
        lab = "2012/13 to 2018/19" if k == 0 else "2018/19 to 2024/25"
        ax.text(0.0, 1.015, f"{('1a', '1b')[k]}   {lab}", transform=ax.transAxes,
                fontsize=7, color=GREY_DARK, ha="left", va="bottom")
        if k == 0:
            top = order[-1]
            ax.annotate("demographic change", (demo.loc[top], ypos[-1]),
                        xytext=(0, 5), textcoords="offset points", fontsize=5.6,
                        color=GREY_DARK, ha="center", va="bottom")
            ax.annotate("observed", (obs.loc[top], ypos[-1]),
                        xytext=(0, 5), textcoords="offset points", fontsize=5.6,
                        color=ACCENT, ha="center", va="bottom")
    axes[0].set_yticks(ypos)
    axes[0].set_yticklabels([SHORT[g] for g in order])
    save(fig, "fig_demographic_vs_observed")


def fig_scenario_2039(proj):
    """Main Fig. 2. Fixed-rate demographic scenario, 2024/25 to 2039/40.
    Filled circles: principal projection with 2024/25 rates. Grey bars: range
    across three population variants and three rate bases. Dashed line: mean
    population-size component across groups. Right margin: absolute change in
    annual code occurrences under the principal scenario."""
    pr = proj[(proj["rate_base"] == "2024/25")
              & (proj["variant"] == "Principal projection")].set_index("group")
    rng = proj.groupby("group")["change_pct"].agg(["min", "max"])
    order = pr["change_pct"].sort_values(ascending=True).index.tolist()
    ypos = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(5.0, 3.5))
    pop_mean = pr["population_size_pct"].mean()
    ax.axvline(0, color=GREY_MID, lw=0.5, zorder=1)
    ax.axvline(pop_mean, color=GREY_LIGHT, lw=0.6, ls=(0, (3, 2)), zorder=1)
    ax.hlines(ypos, rng.loc[order, "min"], rng.loc[order, "max"],
              color=GREY_LIGHT, lw=2.2, zorder=2)
    ax.plot(pr.loc[order, "change_pct"], ypos, "o", mfc=ACCENT, mec=ACCENT,
            ms=3.8, ls="none", zorder=4)
    xmax = rng["max"].max() + 3
    xmin = rng["min"].min() - 3
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(-0.7, len(order) - 0.3)
    for y, g in zip(ypos, order):
        n = pr.loc[g, "change_n"]
        ax.text(1.02, y, f"{n:+,.0f}".replace("-", "\u2212"), transform=ax.get_yaxis_transform(),
                fontsize=6.2, color=GREY_DARK, va="center", ha="left")
    ax.text(1.02, len(order) - 0.35, "n", transform=ax.get_yaxis_transform(),
            fontsize=6.2, color=GREY_MID, va="bottom", ha="left")
    ax.annotate("population growth alone", (pop_mean, len(order) - 0.5),
                xytext=(3, 0), textcoords="offset points", fontsize=5.6,
                color=GREY_MID, ha="left", va="center")
    ax.set_yticks(ypos)
    ax.set_yticklabels([SHORT[g] for g in order])
    ax.set_xlabel("Change in annual code occurrences, 2024/25 to 2039/40, %")
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    save(fig, "fig_scenario_2039")


def figS1_trajectories(rates):
    fig, axes = plt.subplots(3, 4, figsize=(7.2, 5.6), sharex=True)
    for ax, g in zip(axes.ravel(), GROUPS):
        r = rates[rates["group"] == g].sort_values("fy")
        ax.axvspan(2020.5, 2021.5, color=BAND, lw=0, zorder=0)
        base = r[r.fy == 2013]["asr_per_100k"].iloc[0]
        ax.axhline(base, color=GREY_LIGHT, lw=0.5, ls=(0, (3, 3)), zorder=1)
        ax.plot(r["fy"], r["asr_per_100k"], color=ACCENT, lw=0.8, zorder=3)
        ax.plot(r["fy"], r["asr_per_100k"], "o", ms=1.6, mfc="white",
                mec=ACCENT, mew=0.6, ls="none", zorder=4)
        ax.set_title(wrap(g, 30), loc="left", fontsize=6.5, color=GREY_DARK,
                     pad=3)
        ax.set_xticks([2013, 2019, 2025])
        ax.set_xticklabels([fy_label(y) for y in [2013, 2019, 2025]])
        ax.set_ylim(bottom=0)
        ax.margins(x=0.04)
    for ax in axes[:, 0]:
        ax.set_ylabel("Rate per 100 000")
    fig.tight_layout()
    save(fig, "fig_asr_trajectories")


def figS2_age_profiles(analysis):
    fig, axes = plt.subplots(3, 4, figsize=(7.2, 5.6), sharex=True)
    years = [(2013, GREY_LIGHT, "2012/13"), (2019, GREY_DARK, "2018/19"),
             (2025, ACCENT, "2024/25")]
    x = np.arange(len(cfg.AGE_BANDS))
    for ax, g in zip(axes.ravel(), GROUPS):
        for fy, colour, lab in years:
            s = analysis[(analysis["group"] == g) & (analysis["fy"] == fy)]
            s = s.set_index("band").loc[cfg.AGE_BANDS]
            ax.plot(x, s["rate_per_100k"], color=colour, lw=0.8,
                    label=lab if ax is axes.ravel()[0] else None)
        ax.set_yscale("log")
        ax.set_title(wrap(g, 30), loc="left", fontsize=6.5, color=GREY_DARK,
                     pad=3)
        ax.set_xticks(x[::5])
        ax.set_xticklabels([cfg.AGE_BANDS[i] for i in range(0, len(x), 5)])
    for ax in axes[:, 0]:
        ax.set_ylabel("Rate per 100 000, log scale")
    for ax in axes[-1, :]:
        ax.set_xlabel("Age band, years")
    first = axes.ravel()[0]
    for i, (fy, colour, lab) in enumerate(years):
        first.text(0.03, 0.95 - i * 0.09, lab, transform=first.transAxes,
                   fontsize=5.6, color=colour, va="top", ha="left")
    fig.tight_layout()
    save(fig, "fig_age_specific_profiles")


def fig_counting_sensitivity(sens):
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    ypos = np.arange(len(GROUPS))[::-1]
    comps = [
        ("Population size, % of baseline", GREY_LIGHT, "Population size", 0.22),
        ("Age structure, % of baseline", GREY_DARK, "Age structure", 0.0),
        ("Age-specific rate, % of baseline", ACCENT, "Age-specific rate", -0.22),
    ]
    for i, y in enumerate(ypos):
        if i % 2 == 0:
            ax.axhspan(y - 0.5, y + 0.5, color=BAND, lw=0, zorder=0)
    ax.axvline(0, color=GREY_MID, lw=0.5, zorder=1)
    for col, colour, lab, off in comps:
        for i, g in enumerate(GROUPS):
            v = sens[sens["Procedure group"] == g][col]
            y = ypos[i] + off
            # A round-capped bar spans the six variants; where they agree it
            # collapses to a dot, which is the correct visual statement.
            ax.plot([v.min(), v.max()], [y, y], color=colour, lw=2.4,
                    solid_capstyle="round", zorder=3,
                    label=lab if i == 0 else None)
    ax.set_yticks(ypos)
    ax.set_yticklabels([wrap(g, 28) for g in GROUPS])
    ax.set_xlabel("Contribution, % of baseline-year count")
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    fig.tight_layout()
    save(fig, "fig_counting_sensitivity")


def fig_dispersion():
    d = pd.read_csv(cfg.DERIVED / "dispersion.csv")
    d = d[d["period"] == cfg.PRIMARY_PERIOD].set_index("quantity")
    order = ["net_change", "age_specific_rate", "age_structure", "population_size"]
    labels = ["Net change", "Age-specific rate", "Age structure", "Population size"]
    colours = [BLACK, ACCENT, GREY_DARK, GREY_LIGHT]

    fig, ax = plt.subplots(figsize=(4.6, 1.9))
    ypos = np.arange(len(order))[::-1]
    vals = d.loc[order, "sd_between_groups_pp"].to_numpy()
    ax.hlines(ypos, 0, vals, color=colours, lw=1.2, zorder=2)
    for y, v, c in zip(ypos, vals, colours):
        ax.plot(v, y, "o", color=c, ms=4, zorder=3)
        ax.text(v + 0.45, y, f"{v:.1f}", va="center", fontsize=6.5,
                color=GREY_DARK)
    ax.set_yticks(ypos)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, vals.max() * 1.12)
    ax.set_xlabel("Between-group standard deviation, percentage points")
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    fig.tight_layout()
    save(fig, "fig_dispersion")


def figS5_counterfactual():
    """Demographic counterfactual against observed change, twelve groups."""
    cf = pd.read_csv(cfg.DERIVED / "demographic_counterfactual.csv")
    cf = cf[(cf["period"] == cfg.PRIMARY_PERIOD)
            & (~cf["group"].str.startswith("("))].copy()
    x = pd.to_numeric(cf["counterfactual_pct"])
    y = pd.to_numeric(cf["observed_pct"])

    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    lo = min(x.min(), y.min()) - 4
    hi = max(x.max(), y.max()) + 4
    ax.plot([lo, hi], [lo, hi], color=GREY_LIGHT, lw=0.6, ls=(0, (3, 3)),
            zorder=1)
    ax.axhline(0, color=GREY_LIGHT, lw=0.4, zorder=1)
    ax.axvline(0, color=GREY_LIGHT, lw=0.4, zorder=1)
    ax.plot(x, y, "o", mfc=ACCENT, mec=ACCENT, ms=4, ls="none", zorder=3)
    short = {
        "Extra-axial haematoma evacuation": "Extra-axial haematoma",
        "Intracerebral haematoma evacuation": "Intracerebral haematoma",
        "Intracranial tumour resection and biopsy": "Tumour resection/biopsy",
        "CSF diversion, primary": "CSF diversion, primary",
        "CSF diversion, revision and maintenance": "CSF diversion, revision",
        "Peripheral nerve entrapment release": "Nerve entrapment release",
        "Neuromodulation implantation": "Neuromodulation",
        "Spinal nerve root injection and denervation": "Nerve root injection",
        "Lumbar decompression without fusion": "Lumbar decompression",
        "Spinal fusion and instrumentation": "Spinal fusion",
        "Spinal deformity correction": "Deformity correction",
        "Spinal facet joint denervation": "Facet denervation",
    }
    # Labels are set in one column to the right of the points, at the height
    # of their point where possible and spaced apart where points are close.
    # Each label is joined to its point by an elbow leader (vertical, then
    # horizontal), so that no leader passes through another point; where two
    # points share a height, the point further right takes the upper label.
    label_x = float(x.max()) + 8
    gap = 2.8      # minimum vertical spacing between labels, data units
    r = 0.7        # clearance from the marker centre, data units
    key = y.to_numpy() + 0.05 * x.to_numpy()
    order = np.argsort(key)
    ys = y.to_numpy()[order].astype(float)
    xs = x.to_numpy()[order].astype(float)
    groups = cf["group"].to_numpy()[order]
    pos = ys.copy()
    for _ in range(500):
        moved = False
        for i in range(1, len(pos)):
            d = pos[i] - pos[i - 1]
            if d < gap - 1e-9:
                shift = (gap - d) / 2
                pos[i - 1] -= shift
                pos[i] += shift
                moved = True
        if not moved:
            break
    for xi, yi, li, g in zip(xs, ys, pos, groups):
        if abs(li - yi) < 0.3:
            px, py = [xi + r, label_x - 0.6], [li, li]
        else:
            sgn = 1 if li > yi else -1
            px = [xi, xi, label_x - 0.6]
            py = [yi + sgn * r, li, li]
        ax.plot(px, py, color=GREY_MID, lw=0.35, zorder=2,
                solid_joinstyle="miter", solid_capstyle="butt")
        ax.text(label_x, li, short[g], fontsize=6, color=GREY_DARK,
                ha="left", va="center", zorder=4,
                bbox=dict(facecolor="white", edgecolor="none", pad=0.6))
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("Demographic counterfactual change, % of baseline")
    ax.set_ylabel("Observed net change, % of baseline")
    fig.tight_layout()
    save(fig, "fig_counterfactual_scatter")


def figS6_code_trends():
    """Constituent-code trends for the four groups with the largest
    absolute pre-pandemic rate components."""
    cc = pd.read_csv(cfg.DERIVED / "code_level_counts.csv")
    dec = pd.read_csv(cfg.DERIVED / f"rates_{PRIMARY_TAG}.csv")  # not used; keep sig simple
    d = pd.read_csv(cfg.DERIVED / f"decomposition_{PRIMARY_TAG}.csv")
    pre = d[d["period"] == cfg.PRIMARY_PERIOD].set_index("group")
    top4 = (
        pre["age_specific_rate_pct_of_baseline"].abs()
        .sort_values(ascending=False).head(4).index.tolist()
    )
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.2), sharex=True)
    for ax, g in zip(axes.ravel(), top4):
        sub = cc[cc["group"] == g]
        wide = sub.pivot_table(index="fy", columns="opcs4_code",
                               values="usage", aggfunc="sum").fillna(0.0)
        totals = wide.sum().sort_values(ascending=False)
        majors = list(totals.index[:2])
        ends = sorted(((wide[c].iloc[-1], c) for c in majors))
        span = wide.to_numpy().max()
        label_y = {}
        for i, (v, c) in enumerate(ends):
            label_y[c] = v if i == 0 else max(v, label_y[ends[i - 1][1]] + 0.06 * span)
        for code in wide.columns:
            major = code in majors
            ax.plot(wide.index, wide[code],
                    color=ACCENT if major else GREY_LIGHT,
                    lw=0.9 if major else 0.6, zorder=3 if major else 2)
            if major:
                ax.annotate(f"{code[:3]}.{code[3]}", (wide.index[-1], label_y[code]),
                            xytext=(3, 0), textcoords="offset points",
                            fontsize=5.6, color=GREY_DARK, va="center")
        ax.set_title(wrap(g, 34), loc="left", fontsize=6.5, color=GREY_DARK,
                     pad=3)
        ax.set_xticks([2013, 2019, 2025])
        ax.set_xticklabels([fy_label(y) for y in [2013, 2019, 2025]])
        ax.set_ylim(bottom=0)
        ax.margins(x=0.10)
    for ax in axes[:, 0]:
        ax.set_ylabel("Recorded code occurrences")
    fig.tight_layout()
    save(fig, "fig_code_level_trends")


def main():
    rates = pd.read_csv(cfg.DERIVED / f"rates_{PRIMARY_TAG}.csv")
    dec = pd.read_csv(cfg.DERIVED / f"decomposition_{PRIMARY_TAG}.csv")
    analysis = pd.read_csv(cfg.DERIVED / f"analysis_{PRIMARY_TAG}.csv")
    sens = pd.read_csv(cfg.TABLES / "tab_counting_variants.csv")

    figS1_trajectories(rates)
    fig_decomposition_components(dec)
    figS2_age_profiles(analysis)
    fig_counting_sensitivity(sens)
    figS5_counterfactual()
    if (cfg.DERIVED / "code_level_counts.csv").exists():
        figS6_code_trends()
    else:
        print("  [skip] figS6: run s11_code_level.py first")

    fig_demographic_vs_observed(dec)
    proj_path = cfg.DERIVED / "projection_2040.csv"
    if proj_path.exists():
        proj = pd.read_csv(proj_path)
        fig2_scenario(dec, proj)
        fig_scenario_2039(proj)
    else:
        print("  [skip] fig2 scenario: run s08_projection.py first")


if __name__ == "__main__":
    main()
