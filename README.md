# Population ageing and neurosurgery-related procedure activity in England

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24221325.svg)](https://doi.org/10.5281/zenodo.24221325)

Analysis code and derived data for a national decomposition of recorded
neurosurgery-related procedure activity in England, 2012/13 to 2024/25, with
fixed-rate demographic projections to 2039/40.

Authors: Aaron Lawson McLean, Zsófia Varga-Vrancsik, Julian Kahr, Christian
Senft and Marcel A. Kamp (Department of Neurosurgery, Jena University
Hospital, Friedrich Schiller University Jena; Brandenburg Medical School
Theodor Fontane and Immanuel Clinic Rüdersdorf).

## Study summary

**Question.** Capacity planning for neurosurgical services commonly assumes
that population ageing drives demand. How much of the change in recorded
activity across neurosurgery-related procedures is attributable to population
growth, to changing age structure and to changing age-specific procedure
rates, and how much demographic pressure would projected population change
alone exert on each procedure group to 2039/40?

**Design.** Repeated cross-sectional analysis of national aggregate data.
Twelve procedure groups were defined from 125 four-character OPCS-4 codes
(cranial emergency, cranial elective, CSF diversion, degenerative spine,
deformity, peripheral nerve and interventional pain procedures). Annual code
occurrences in NHS-commissioned admitted patient care (Hospital Episode
Statistics) were combined with Office for National Statistics population
estimates and 2024-based projections. Change in each group was split into
population-size, age-structure and age-specific rate components that sum
exactly to the observed change, and the variance of change across groups was
partitioned among the three components. A fixed-rate scenario applied
2024/25 age-specific rates to projected populations.

**Main findings.** Between 2012/13 and 2018/19, demographic change added a
small and similar increment to every group, while observed change differed
widely between groups; changes in age-specific rates accounted for almost all
of the difference between groups. After 2018/19, demographic change would
have increased activity while recorded activity fell. Under current rates,
projected demographic pressure to 2039/40 differs strongly by procedure and is
largest for extra-axial haematoma evacuation; almost all of the projected
increase concerns people aged 65 years or over. Every number is reported in
[RESULTS.md](RESULTS.md), which the pipeline generates from
`derived/key_results.json`.

## Reproducing the analysis

Requirements: Python 3.11 and an internet connection for the first run.

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
./run_all.sh
```

`./run_all.sh` downloads the two upstream code-usage files from a pinned
commit, checks every source file against the SHA-256 values in
`data-raw/manifest.json`, rebuilds all derived data, tables and figures, and
runs the verification step, which exits with an error if any check fails.
Set `NEUROSURG_PYTHON` if the interpreter is not called `python3`.
`./run_all.sh refresh` re-downloads all sources from their current
endpoints and rewrites the manifest; this is a deliberate data update and will
change the results. All computations are deterministic.

## Data sources

| Source | Content | How obtained |
|---|---|---|
| NHS England, Hospital Episode Statistics Admitted Patient Care, OPCS-4 code usage (via the `opencodecounts` resource, Bennett Institute for Applied Data Science, University of Oxford) | Annual four-character OPCS-4 code counts, in total and by age band, sex and procedure position, 2012/13 to 2024/25 | Downloaded at run time from commit `a92a37bbfc3d670864fe6ae08edf1a61ed1d818e` of `bennettoxford/opencodecounts`; not redistributed |
| Office for National Statistics, mid-year population estimates (Nomis NM_2002_1) | England, single year of age, mid-2012 to mid-2024 | Included in `data-raw/` |
| Office for National Statistics, 2024-based national population projections (Nomis NM_2403_1) | England, single year of age, 2024 to 2039; principal, old and young age-structure variants | Included in `data-raw/` |

Checksums of the analysed source files:

- `opcs4_usage.rda` `90742fcd...af9e`
- `opcs4_usage_breakdowns.rda` `ae27855e...7a1c`
- `ons_mye_england_sya.csv` `ce7106ad...19d4`
- `ons_npp_england_sya.csv` `0195eaf6...101b`

See [THIRD_PARTY_DATA.md](THIRD_PARTY_DATA.md) for licensing and attribution.

## Repository structure

```
src/config.py            analytic choices: procedure groups, age bands, periods
src/s01_fetch.py         download pinned sources and verify checksums
src/s02_build.py         analysis datasets (six counting variants), integrity checks
src/s03_decompose.py     decomposition, Shapley allocation, endpoints, variance shares
src/s07_substitution.py  candidate embolisation codes
src/s08_projection.py    fixed-rate demographic scenario to 2039/40
src/s11_code_level.py    code-level audit and OPCS-4 revision-boundary screen
src/s12_robustness.py    panel, weighting, code-set and projection sensitivity
src/s04_tables.py        working tables (outputs/tables/tab_*.csv)
src/s05_figures.py       working figures (outputs/figures/fig_*)
src/s13_publication.py   numbered tables and figures (outputs/publication/),
                         derived/key_results.json and RESULTS.md
src/s06_verify.py        reconciliation and consistency checks
src/s10_package.py       file manifest with SHA-256 (MANIFEST.csv, MANIFEST.md)
derived/                 analysis datasets and intermediate results
outputs/publication/     tables and figures numbered as in the article
```

To change the procedure groups, edit `PROCEDURE_GROUPS` in `src/config.py`
and rerun the pipeline.

## Method

For a procedure group in year t with population `P`, age-band population
shares `c` and age-specific rates `m`, the recorded count is
`N = P * sum(c * m)`. The change between two years is decomposed as

```
N2 - N1 = (P2 - P1)(R1 + R2)/2                     population size
        + (P1 + P2)/2 * sum((c2 - c1) * mbar)      age structure
        + (P1 + P2)/2 * sum((m2 - m1) * cbar)      age-specific rate
```

with `R = sum(c * m)` and bars denoting two-year means (Kitagawa 1955; Das
Gupta 1994). The identity is exact. Because net change `Y` is the sum of the
three components in every group, the between-group variance decomposes as
`Var(Y) = Cov(P, Y) + Cov(A, Y) + Cov(R, Y)`; each term is reported as a share
of `Var(Y)`. Sensitivity analyses cover the allocation of interaction terms
(three-factor Shapley decomposition), endpoints, counting conventions, panel
composition and weighting, code stability and OPCS-4 revision boundaries.

## Interpretation

The counted quantity is recorded OPCS-4 code occurrences in admitted patient
care, not patients, operations or workload. OPCS-4 does not record indication,
and treatment specialty is not available in the source, so the procedure
groups are neurosurgery-related rather than attributable to neurosurgical
units. The age-specific rate component contains every within-age influence on
recorded activity, including incidence, indications, guidance, capacity,
setting of care and coding. The 2039/40 scenario is a demographic exposure
estimate at current rates, not a forecast.

## Archive

Releases are archived at Zenodo: https://doi.org/10.5281/zenodo.24221325
resolves to the latest version, and each release has its own version DOI on
the Zenodo record.

## Changes

- 1.1.1: point labels in the demographic counterfactual scatter (Figure S4)
  are set in one column with elbow leader lines, so that each label is
  unambiguously attached to its point. No numerical output changed.
- 1.1.0: the primary 2039/40 scenario is additionally split by broad age at
  the time of the procedure (0 to 64, 65 to 79, 80 and over;
  `derived/projection_2040_by_age.csv`, reported in Table 3); figure 1 panels
  are labelled 1a and 1b; PDF metadata timestamps are fixed so that figure
  files are byte-identical between runs.
- 1.0.1: manifest exclusions made independent of the checkout location.
- 1.0.0: first release.

## Licence and citation

Code is released under the MIT licence (see [LICENSE](LICENSE)). Source data
remain under their original licences. Please cite the associated article and
this archive; citation metadata are in [CITATION.cff](CITATION.cff).
