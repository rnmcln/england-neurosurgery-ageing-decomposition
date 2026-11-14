# Manifest

Generated 2026-11-14T13:39:44+00:00.
143 files, 14.2 MB.

SHA-256 is given for every file. The source data files and their
retrieval URLs are additionally recorded in `data-raw/manifest.json`,
and `src/s01_fetch.py` refuses to proceed if a source file differs.

## Documents

| File | Size | SHA-256 (first 12) | Description |
|---|---|---|---|
| `.github/workflows/verify.yml` | 1 kB | `15b735059324` | Continuous integration: rebuild and verify outputs |
| `.gitignore` | 0 kB | `0ac42a5f77fd` | Excluded local, cache and unlicensed source files |
| `.zenodo.json` | 2 kB | `f3e1768c9b5c` | Archival metadata for Zenodo |
| `CITATION.cff` | 2 kB | `a4fc379e6ae7` | Citation metadata for this software release |
| `LICENSE` | 1 kB | `df0804fec300` | MIT licence for the analysis code |
| `README.md` | 8 kB | `539232351d4f` | Study summary, data sources, method and instructions for reproduction |
| `RESULTS.md` | 2 kB | `dde791c35199` | Results summary generated from derived/key_results.json |
| `THIRD_PARTY_DATA.md` | 2 kB | `7d17b83be427` | Licensing and attribution of third-party source data |
| `pyproject.toml` | 0 kB | `c3e5986650e4` | Python project metadata and pinned runtime dependencies |
| `requirements.txt` | 0 kB | `7ea68be5282b` | Pinned runtime dependencies |
| `run_all.sh` | 2 kB | `800643f2bde9` | Pipeline runner (verify or refresh mode) |

## Pipeline source (src/)

| File | Size | SHA-256 (first 12) | Description |
|---|---|---|---|
| `src/config.py` | 13 kB | `ec7eef2284e3` | All analytic choices: procedure groups, age bands, periods, options |
| `src/s01_fetch.py` | 5 kB | `112b5f01c654` | Download pinned source files and verify SHA-256 checksums |
| `src/s02_build.py` | 7 kB | `28445a5b253d` | Build six analysis dataset variants; integrity checks C1 to C3 |
| `src/s03_decompose.py` | 18 kB | `c0b3d7d8b05d` | Three-factor decomposition; Shapley, endpoints, cumulated annual, variance, counterfactual |
| `src/s04_tables.py` | 12 kB | `c047e753a088` | Working tables (tab_*.csv) |
| `src/s05_figures.py` | 22 kB | `b69a55dc2152` | Working figures (fig_*.pdf/.eps/.tiff/.png) |
| `src/s06_verify.py` | 22 kB | `f59be6976428` | Consistency, reconciliation and robustness checks; exits non-zero on failure |
| `src/s07_substitution.py` | 6 kB | `b1bc83e7392c` | Candidate embolisation codes against extra-axial haematoma evacuation |
| `src/s08_projection.py` | 8 kB | `026b4af529bf` | Fixed-rate demographic scenario to 2039/40 |
| `src/s10_package.py` | 9 kB | `fa341b272c7e` | This script: builds the file manifest |
| `src/s11_code_level.py` | 7 kB | `62e840228a3a` | Code-level audit: per-code counts, concentration, OPCS-4 revision-boundary screen |
| `src/s12_robustness.py` | 15 kB | `d60d70a70ebd` | Panel, weighting, stable-code and projection sensitivity analyses |
| `src/s13_publication.py` | 28 kB | `334fd0332667` | Numbered publication tables and figures; key results; RESULTS.md |

## Source data (data-raw/)

| File | Size | SHA-256 (first 12) | Description |
|---|---|---|---|
| `data-raw/manifest.json` | 2 kB | `25ea06499eaf` | Source URL, byte count and SHA-256 for each source file |
| `data-raw/ons_mye_england_sya.csv` | 27 kB | `ce7106ade0af` | ONS mid-year population estimates, England, single year of age, 2012 to 2024 |
| `data-raw/ons_npp_england_sya.csv` | 228 kB | `0195eaf6c7c3` | ONS 2024-based national population projections, England, three variants, 2024 to 2039 |
| `data-raw/opcs4_usage.rda` | 772 kB | `90742fcd5e52` | NHS England HES APC OPCS-4 code usage totals (downloaded, not distributed) |
| `data-raw/opcs4_usage_breakdowns.rda` | 5.0 MB | `ae27855e6b53` | Same, by age band, sex and procedure position (downloaded, not distributed) |

## Derived intermediates (derived/)

| File | Size | SHA-256 (first 12) | Description |
|---|---|---|---|
| `derived/alternative_endpoints.csv` | 6 kB | `b9e0efe31460` | Endpoint sensitivity: 2018/19, 2019/20, three-year averages |
| `derived/analysis_all_procedures__drop.csv` | 254 kB | `50dd52dfe262` | Analysis dataset variant: group by year by age band counts and population |
| `derived/analysis_all_procedures__oldest.csv` | 254 kB | `f6cc03023bed` | Analysis dataset variant: group by year by age band counts and population |
| `derived/analysis_all_procedures__proportional.csv` | 291 kB | `b71eb50c29d3` | Analysis dataset variant: group by year by age band counts and population |
| `derived/analysis_main_procedure__drop.csv` | 291 kB | `e14b1b0645db` | Analysis dataset variant: group by year by age band counts and population |
| `derived/analysis_main_procedure__oldest.csv` | 292 kB | `f9297ac7eed6` | Analysis dataset variant: group by year by age band counts and population |
| `derived/analysis_main_procedure__proportional.csv` | 292 kB | `ab2f8e088ca3` | Analysis dataset variant: group by year by age band counts and population |
| `derived/build_checks.csv` | 31 kB | `2311a1df8bf5` | Integrity checks: code coverage, age allocation, positional ratio |
| `derived/code_coverage.csv` | 8 kB | `187184262892` | Per-code availability across the study and primary window |
| `derived/code_level_counts.csv` | 80 kB | `385b78eb55bc` | Annual counts for each of the 125 constituent OPCS-4 codes |
| `derived/cumulative_annual.csv` | 2 kB | `efa0fc21ced6` | Consecutive-year decompositions cumulated over 2012/13 to 2019/20 |
| `derived/decomposition_all_procedures__drop.csv` | 27 kB | `ab162adca04e` | Decomposition output for one analysis variant |
| `derived/decomposition_all_procedures__oldest.csv` | 27 kB | `b5373e0b1b54` | Decomposition output for one analysis variant |
| `derived/decomposition_all_procedures__proportional.csv` | 29 kB | `76efc620e015` | Decomposition output for one analysis variant |
| `derived/decomposition_main_procedure__drop.csv` | 30 kB | `33519a3b9407` | Decomposition output for one analysis variant |
| `derived/decomposition_main_procedure__oldest.csv` | 29 kB | `6427cefcb94e` | Decomposition output for one analysis variant |
| `derived/decomposition_main_procedure__proportional.csv` | 29 kB | `5a4686387586` | Decomposition output for one analysis variant |
| `derived/demographic_counterfactual.csv` | 11 kB | `e7a45104832f` | Demographic counterfactual N(P2,c2,m1) - N(P1,c1,m1) per group and period |
| `derived/dispersion.csv` | 4 kB | `8db6a28f3a9b` | Between-group SD, IQR and range per component (descriptive) |
| `derived/key_results.json` | 6 kB | `6397f502624e` | Every quantity quoted in the results summary and article |
| `derived/npp_population_checks.csv` | 2 kB | `9cc5d2809055` | Projected single-age totals reconciled to published All Ages totals |
| `derived/projection_2040.csv` | 25 kB | `5918214f902f` | Scenario results, all groups by rate base and population variant |
| `derived/projection_per_year_comparison.csv` | 1 kB | `6b53d06ae397` | Group-level interval-average observed and projected demographic contributions |
| `derived/projection_per_year_summary.csv` | 1 kB | `6ac6ecca085c` | Across-group summaries of observed and projected demographic contributions |
| `derived/rates_all_procedures__drop.csv` | 13 kB | `a9652de913ec` | Annual counts, crude and age-standardised rates by group |
| `derived/rates_all_procedures__oldest.csv` | 13 kB | `97a84089b0fd` | Annual counts, crude and age-standardised rates by group |
| `derived/rates_all_procedures__proportional.csv` | 14 kB | `850d1929e923` | Annual counts, crude and age-standardised rates by group |
| `derived/rates_main_procedure__drop.csv` | 15 kB | `6a687213b4b6` | Annual counts, crude and age-standardised rates by group |
| `derived/rates_main_procedure__oldest.csv` | 14 kB | `929e15ef8f8b` | Annual counts, crude and age-standardised rates by group |
| `derived/rates_main_procedure__proportional.csv` | 14 kB | `becd49379010` | Annual counts, crude and age-standardised rates by group |
| `derived/selected_panel_robustness.csv` | 4 kB | `34891d14b3a8` | Variance shares under panel, weighting, scale, code-set and counting sensitivities |
| `derived/shapley_comparison.csv` | 3 kB | `9d96a5a6befa` | Symmetric versus three-factor Shapley allocation, primary period |
| `derived/stable_code_sensitivity.csv` | 7 kB | `27b4769b1aa7` | Decomposition after excluding codes not present throughout |
| `derived/variance_decomposition.csv` | 1 kB | `0ebe4cb4cac9` | Covariance decomposition of between-group variance in net change |

## Tables (outputs/tables/)

| File | Size | SHA-256 (first 12) | Description |
|---|---|---|---|
| `outputs/tables/tab_age_allocation.csv` | 2 kB | `4fb637c00278` | Working table |
| `outputs/tables/tab_alternative_endpoints.csv` | 4 kB | `aff4e2f718bf` | Working table |
| `outputs/tables/tab_annual_rates.csv` | 9 kB | `b98c389284d7` | Working table |
| `outputs/tables/tab_code_concentration.csv` | 14 kB | `ac427be13ab1` | Working table |
| `outputs/tables/tab_counting_variants.csv` | 6 kB | `6df6dc03d596` | Working table |
| `outputs/tables/tab_cumulative_annual.csv` | 1 kB | `bb0c9b0e6281` | Working table |
| `outputs/tables/tab_decomposition_display_periods.csv` | 3 kB | `b8c60d9e6503` | Working table |
| `outputs/tables/tab_demographic_counterfactual.csv` | 3 kB | `1d9218fefcc8` | Working table |
| `outputs/tables/tab_embolisation_age_profile.csv` | 0 kB | `63c0b00cb244` | Working table |
| `outputs/tables/tab_pandemic_disruption.csv` | 1 kB | `285d86cab2a0` | Working table |
| `outputs/tables/tab_phase_decomposition.csv` | 4 kB | `65d2b2387365` | Working table |
| `outputs/tables/tab_procedure_groups.csv` | 2 kB | `9b5b5d802f78` | Working table |
| `outputs/tables/tab_projection_per_year.csv` | 0 kB | `7e223ab7e6d3` | Working table |
| `outputs/tables/tab_projection_range.csv` | 1 kB | `aa98b423ee96` | Working table |
| `outputs/tables/tab_projection_scenario.csv` | 1 kB | `a1e11b79f9a7` | Working table |
| `outputs/tables/tab_revision_screen.csv` | 60 kB | `c88ac991ed4e` | Working table |
| `outputs/tables/tab_selected_panel_robustness.csv` | 3 kB | `2b43fe9f78f2` | Working table |
| `outputs/tables/tab_shapley_comparison.csv` | 1 kB | `7bef436293ce` | Working table |
| `outputs/tables/tab_stable_code_sensitivity.csv` | 3 kB | `199a83db098c` | Working table |
| `outputs/tables/tab_substitution_check.csv` | 0 kB | `b2a66503ad06` | Working table |
| `outputs/tables/tab_variance_decomposition.csv` | 1 kB | `c26d150b6f9e` | Working table |

## Figures (outputs/figures/)

| File | Size | SHA-256 (first 12) | Description |
|---|---|---|---|
| `outputs/figures/fig_age_specific_profiles.pdf` | 24 kB | `9aa96719f27b` | Working figure (PDF) |
| `outputs/figures/fig_age_specific_profiles.png` | 661 kB | `8bab1edeec31` | Working figure |
| `outputs/figures/fig_age_structure_observed_vs_scenario.pdf` | 14 kB | `9005684028d2` | Working figure (PDF) |
| `outputs/figures/fig_age_structure_observed_vs_scenario.png` | 204 kB | `336ef6507281` | Working figure |
| `outputs/figures/fig_asr_trajectories.pdf` | 23 kB | `6e41d79a4cd9` | Working figure (PDF) |
| `outputs/figures/fig_asr_trajectories.png` | 404 kB | `2836ea0f7524` | Working figure |
| `outputs/figures/fig_code_level_trends.pdf` | 16 kB | `261c95bb76ee` | Working figure (PDF) |
| `outputs/figures/fig_code_level_trends.png` | 439 kB | `3ff6a2dba09b` | Working figure |
| `outputs/figures/fig_counterfactual_scatter.pdf` | 14 kB | `391bae1bc1d3` | Working figure (PDF) |
| `outputs/figures/fig_counterfactual_scatter.png` | 167 kB | `3cefab57bff4` | Working figure |
| `outputs/figures/fig_counting_sensitivity.pdf` | 14 kB | `2f16538c104e` | Working figure (PDF) |
| `outputs/figures/fig_counting_sensitivity.png` | 191 kB | `443da65f8c52` | Working figure |
| `outputs/figures/fig_decomposition_components.pdf` | 17 kB | `7c74361bb751` | Working figure (PDF) |
| `outputs/figures/fig_decomposition_components.png` | 232 kB | `44b3c7a3c06c` | Working figure |
| `outputs/figures/fig_demographic_vs_observed.pdf` | 16 kB | `85b1ac132828` | Working figure (PDF) |
| `outputs/figures/fig_demographic_vs_observed.png` | 199 kB | `15aaad8620ea` | Working figure |
| `outputs/figures/fig_scenario_2039.pdf` | 15 kB | `d29152ae5579` | Working figure (PDF) |
| `outputs/figures/fig_scenario_2039.png` | 198 kB | `f52564bff68b` | Working figure |

## Publication items (outputs/publication/)

| File | Size | SHA-256 (first 12) | Description |
|---|---|---|---|
| `outputs/publication/CAPTIONS.md` | 3 kB | `0299f4327468` | Short description of each numbered publication item |
| `outputs/publication/Fig1.pdf` | 16 kB | `85b1ac132828` | Main figure (numbered as in the article) (PDF) |
| `outputs/publication/Fig1.png` | 199 kB | `15aaad8620ea` | Main figure (numbered as in the article) |
| `outputs/publication/Fig2.pdf` | 15 kB | `d29152ae5579` | Main figure (numbered as in the article) (PDF) |
| `outputs/publication/Fig2.png` | 198 kB | `f52564bff68b` | Main figure (numbered as in the article) |
| `outputs/publication/FigS1.pdf` | 23 kB | `6e41d79a4cd9` | Supplementary figure (numbered as in the article) (PDF) |
| `outputs/publication/FigS1.png` | 404 kB | `2836ea0f7524` | Supplementary figure (numbered as in the article) |
| `outputs/publication/FigS2.pdf` | 24 kB | `9aa96719f27b` | Supplementary figure (numbered as in the article) (PDF) |
| `outputs/publication/FigS2.png` | 661 kB | `8bab1edeec31` | Supplementary figure (numbered as in the article) |
| `outputs/publication/FigS3.pdf` | 17 kB | `7c74361bb751` | Supplementary figure (numbered as in the article) (PDF) |
| `outputs/publication/FigS3.png` | 232 kB | `44b3c7a3c06c` | Supplementary figure (numbered as in the article) |
| `outputs/publication/FigS4.pdf` | 14 kB | `391bae1bc1d3` | Supplementary figure (numbered as in the article) (PDF) |
| `outputs/publication/FigS4.png` | 167 kB | `3cefab57bff4` | Supplementary figure (numbered as in the article) |
| `outputs/publication/FigS5.pdf` | 14 kB | `9005684028d2` | Supplementary figure (numbered as in the article) (PDF) |
| `outputs/publication/FigS5.png` | 204 kB | `336ef6507281` | Supplementary figure (numbered as in the article) |
| `outputs/publication/FigS6.pdf` | 14 kB | `2f16538c104e` | Supplementary figure (numbered as in the article) (PDF) |
| `outputs/publication/FigS6.png` | 191 kB | `443da65f8c52` | Supplementary figure (numbered as in the article) |
| `outputs/publication/FigS7.pdf` | 16 kB | `261c95bb76ee` | Supplementary figure (numbered as in the article) (PDF) |
| `outputs/publication/FigS7.png` | 439 kB | `3ff6a2dba09b` | Supplementary figure (numbered as in the article) |
| `outputs/publication/Table1.csv` | 2 kB | `036a5995e196` | Main table (numbered as in the article) |
| `outputs/publication/Table2.csv` | 1 kB | `efbd43ca4478` | Main table (numbered as in the article) |
| `outputs/publication/Table3.csv` | 1 kB | `2577d91ff957` | Main table (numbered as in the article) |
| `outputs/publication/TableS1.csv` | 13 kB | `76af1423a985` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS10.csv` | 1 kB | `7bef436293ce` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS11.csv` | 4 kB | `aff4e2f718bf` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS12.csv` | 1 kB | `bb0c9b0e6281` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS13.csv` | 6 kB | `6df6dc03d596` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS14.csv` | 3 kB | `2b43fe9f78f2` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS15.csv` | 3 kB | `719476faf906` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS16.csv` | 14 kB | `2878ee784714` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS17.csv` | 8 kB | `9a3f322ef78b` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS18.csv` | 0 kB | `b2a66503ad06` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS19.csv` | 0 kB | `63c0b00cb244` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS2.csv` | 2 kB | `4fb637c00278` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS3.csv` | 9 kB | `b98c389284d7` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS4.csv` | 1 kB | `c26d150b6f9e` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS5.csv` | 3 kB | `1d9218fefcc8` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS6.csv` | 1 kB | `285d86cab2a0` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS7.csv` | 4 kB | `65d2b2387365` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS8.csv` | 12 kB | `c216c31a22b6` | Supplementary table (numbered as in the article) |
| `outputs/publication/TableS9.csv` | 0 kB | `7e223ab7e6d3` | Supplementary table (numbered as in the article) |
