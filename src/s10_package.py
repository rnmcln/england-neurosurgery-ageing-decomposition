"""
Step 10. Package.

Walks the project, computes a SHA-256 for every file, attaches a one-line
description, and writes MANIFEST.csv and MANIFEST.md. Files with no description
are listed under "undescribed" rather than omitted, so that the manifest cannot
silently drift from the contents.

Run last. The manifest necessarily excludes itself.
"""

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg

EXCLUDE_DIRS = {
    "__pycache__", ".git", ".venv", ".cache", ".ipynb_checkpoints",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "_to_delete", "tmp", "qa",
}
EXCLUDE_NAMES = {"MANIFEST.csv", "MANIFEST.md", ".DS_Store"}

DESCRIPTIONS = {
    # documents
    "README.md": "Study summary, data sources, method and instructions for reproduction",
    "RESULTS.md": "Results summary generated from derived/key_results.json",
    "LICENSE": "MIT licence for the analysis code",
    "THIRD_PARTY_DATA.md": "Licensing and attribution of third-party source data",
    "CITATION.cff": "Citation metadata for this software release",
    ".zenodo.json": "Archival metadata for Zenodo",
    ".gitignore": "Excluded local, cache and unlicensed source files",
    ".github/workflows/verify.yml": "Continuous integration: rebuild and verify outputs",
    "requirements.txt": "Pinned runtime dependencies",
    "pyproject.toml": "Python project metadata and pinned runtime dependencies",
    "run_all.sh": "Pipeline runner (verify or refresh mode)",
    # source
    "src/config.py": "All analytic choices: procedure groups, age bands, periods, options",
    "src/s01_fetch.py": "Download pinned source files and verify SHA-256 checksums",
    "src/s02_build.py": "Build six analysis dataset variants; integrity checks C1 to C3",
    "src/s03_decompose.py": "Three-factor decomposition; Shapley, endpoints, cumulated annual, variance, counterfactual",
    "src/s04_tables.py": "Working tables (tab_*.csv)",
    "src/s05_figures.py": "Working figures (fig_*.pdf/.eps/.tiff/.png)",
    "src/s06_verify.py": "Consistency, reconciliation and robustness checks; exits non-zero on failure",
    "src/s07_substitution.py": "Candidate embolisation codes against extra-axial haematoma evacuation",
    "src/s08_projection.py": "Fixed-rate demographic scenario to 2039/40",
    "src/s10_package.py": "This script: builds the file manifest",
    "src/s11_code_level.py": "Code-level screen: per-code counts, concentration, OPCS-4 revision-boundary screen",
    "src/s12_robustness.py": "Panel, weighting, stable-code and projection sensitivity analyses",
    "src/s13_publication.py": "Numbered publication tables and figures; key results; RESULTS.md",
    "src/s14_supplementary.py": "Recorded expectations, Poisson intervals and denominator timing",
    # raw
    "data-raw/manifest.json": "Source URL, byte count and SHA-256 for each source file",
    "data-raw/opcs4_usage.rda": "NHS England HES APC OPCS-4 code usage totals (downloaded, not distributed)",
    "data-raw/opcs4_usage_breakdowns.rda": "Same, by age band, sex and procedure position (downloaded, not distributed)",
    "data-raw/ons_mye_england_sya.csv": "ONS mid-year population estimates, England, single year of age, 2012 to 2024",
    "data-raw/ons_npp_england_sya.csv": "ONS 2024-based national population projections, England, three variants, 2024 to 2039",
    # derived
    "derived/build_checks.csv": "Integrity checks: code coverage, age allocation, positional ratio",
    "derived/projection_2040.csv": "Scenario results, all groups by rate base and population variant",
    "derived/projection_2040_by_age.csv": "Primary scenario split by broad age (0-64, 65-79, 80 and over)",
    "derived/shapley_comparison.csv": "Symmetric versus three-factor Shapley allocation, primary period",
    "derived/alternative_endpoints.csv": "Endpoint sensitivity: 2018/19, 2019/20, three-year averages",
    "derived/cumulative_annual.csv": "Consecutive-year decompositions cumulated over 2012/13 to 2019/20",
    "derived/dispersion.csv": "Between-group SD, IQR and range per component (descriptive)",
    "derived/variance_decomposition.csv": "Covariance decomposition of between-group variance in net change",
    "derived/demographic_counterfactual.csv": "Demographic counterfactual N(P2,c2,m1) - N(P1,c1,m1) per group and period",
    "derived/code_level_counts.csv": "Annual counts for each of the 125 constituent OPCS-4 codes",
    "derived/code_coverage.csv": "Per-code availability across the study and primary window",
    "derived/npp_population_checks.csv": "Projected single-age totals reconciled to published All Ages totals",
    "derived/selected_panel_robustness.csv": "Variance shares under panel, weighting, scale, code-set and counting sensitivities",
    "derived/stable_code_sensitivity.csv": "Decomposition after excluding codes not present throughout",
    "derived/projection_per_year_comparison.csv": "Group-level interval-average observed and projected demographic contributions",
    "derived/projection_per_year_summary.csv": "Across-group summaries of observed and projected demographic contributions",
    "derived/key_results.json": "Every quantity quoted in the results summary and article",
    "derived/expectation_outcomes.csv": "Recorded expectations against the components of change; population-size identity",
    "derived/poisson_intervals.csv": "Poisson 95% intervals for age-standardised rates and rate components",
    "derived/denominator_timing.csv": "Decomposition with mid-year and 1 October interpolated populations",
    "outputs/publication/CAPTIONS.md": "Short description of each numbered publication item",
}

PATTERNS = [
    ("derived/analysis_", "Analysis dataset variant: group by year by age band counts and population"),
    ("derived/decomposition_", "Decomposition output for one analysis variant"),
    ("derived/rates_", "Annual counts, crude and age-standardised rates by group"),
    ("outputs/tables/tab_", "Working table"),
    ("outputs/figures/fig_", "Working figure"),
    ("outputs/publication/TableS", "Supplementary table (numbered as in the article)"),
    ("outputs/publication/Table", "Main table (numbered as in the article)"),
    ("outputs/publication/FigS", "Supplementary figure (numbered as in the article)"),
    ("outputs/publication/Fig", "Main figure (numbered as in the article)"),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def describe(rel):
    if rel in DESCRIPTIONS:
        return DESCRIPTIONS[rel]
    for prefix, text in PATTERNS:
        if rel.startswith(prefix):
            suffix = " (PDF)" if rel.endswith(".pdf") else ""
            return text + suffix
    return ""


def main():
    root = cfg.ROOT
    rows = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in p.relative_to(root).parts):
            continue
        if p.name in EXCLUDE_NAMES or p.suffix in {".tiff", ".eps"}:
            continue
        rel = str(p.relative_to(root))
        rows.append({
            "path": rel,
            "bytes": p.stat().st_size,
            "sha256": sha256(p),
            "description": describe(rel),
        })

    df = pd.DataFrame(rows).sort_values("path").reset_index(drop=True)
    df.to_csv(root / "MANIFEST.csv", index=False)

    undescribed = df[df["description"] == ""]["path"].tolist()
    total_mb = df["bytes"].sum() / 1e6

    groups = {
        "Documents": lambda r: "/" not in r or r.startswith(".github/"),
        "Pipeline source (src/)": lambda r: r.startswith("src/"),
        "Source data (data-raw/)": lambda r: r.startswith("data-raw/"),
        "Derived intermediates (derived/)": lambda r: r.startswith("derived/"),
        "Tables (outputs/tables/)": lambda r: r.startswith("outputs/tables/"),
        "Figures (outputs/figures/)": lambda r: r.startswith("outputs/figures/"),
        "Publication items (outputs/publication/)": lambda r: r.startswith("outputs/publication/"),
    }

    lines = [
        "# Manifest",
        "",
        f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}.",
        f"{len(df)} files, {total_mb:.1f} MB.",
        "",
        "SHA-256 is given for every file. The source data files and their",
        "retrieval URLs are additionally recorded in `data-raw/manifest.json`,",
        "and `src/s01_fetch.py` refuses to proceed if a source file differs.",
        "",
    ]
    seen = set()
    for title, pred in groups.items():
        sub = df[df["path"].apply(pred) & ~df["path"].isin(seen)]
        if sub.empty:
            continue
        seen.update(sub["path"])
        lines += [f"## {title}", "", "| File | Size | SHA-256 (first 12) | Description |",
                  "|---|---|---|---|"]
        for _, r in sub.iterrows():
            size = (f"{r['bytes']/1e6:.1f} MB" if r["bytes"] > 1e6
                    else f"{r['bytes']/1e3:.0f} kB")
            lines.append(
                f"| `{r['path']}` | {size} | `{r['sha256'][:12]}` | "
                f"{r['description'] or 'UNDESCRIBED'} |"
            )
        lines.append("")

    if undescribed:
        lines += ["## Undescribed files", "",
                  "These are present in the archive but have no description in "
                  "`s10_package.py`. Add one there rather than editing the "
                  "manifest by hand.", ""]
        lines += [f"- `{u}`" for u in undescribed] + [""]

    (root / "MANIFEST.md").write_text("\n".join(lines))

    print(f"  {len(df)} files, {total_mb:.1f} MB")
    print(f"  MANIFEST.csv and MANIFEST.md written")
    if undescribed:
        print(f"  {len(undescribed)} undescribed: {undescribed[:5]}")
    else:
        print("  every file described")


if __name__ == "__main__":
    main()
