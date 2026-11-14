# Third-party data and licensing

The MIT licence in `LICENSE` applies to the analysis code and documentation in
this repository. It does not apply to source data.

## Office for National Statistics population data (included)

`data-raw/ons_mye_england_sya.csv` and `data-raw/ons_npp_england_sya.csv` are
extracts of ONS mid-year population estimates (Nomis dataset NM_2002_1) and
2024-based national population projections (Nomis dataset NM_2403_1) for
England. They are redistributed under the
[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
They are included because the Nomis API serves the current release, which ONS
revises; the extracts preserve the exact figures analysed.

Attribution: Source: Office for National Statistics licensed under the Open
Government Licence v3.0.

## NHS England code-usage data (not included)

The OPCS-4 code-usage statistics are published by NHS England from Hospital
Episode Statistics under the Open Government Licence v3.0. This analysis reads
them from the R data files of the `opencodecounts` resource
(<https://github.com/bennettoxford/opencodecounts>), which carries no
licence of its own for its packaged files. Those files are therefore not
redistributed. `src/s01_fetch.py` downloads them from a fixed commit and
checks them against the SHA-256 values in `data-raw/manifest.json`.

The derived tables in `derived/` and `outputs/` contain aggregate counts
calculated from the NHS England statistics. The OPCS-4 code descriptions
reproduced in `outputs/publication/TableS1.csv` are taken from the same
published statistics. The OPCS-4 classification is Crown copyright, published
by NHS England under the Open Government Licence v3.0.

Attribution: Contains public sector information licensed under the Open
Government Licence v3.0. Source: NHS England, Hospital Episode Statistics.
