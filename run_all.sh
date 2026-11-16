#!/usr/bin/env bash
# Reproducible pipeline runner.
#
#   ./run_all.sh            verify (and if necessary download) the pinned
#                           source files, then rebuild every output
#   ./run_all.sh refresh    re-download all sources from their moving
#                           endpoints and rewrite the checksum manifest
#                           (a deliberate data update; results will change)
set -euo pipefail

cd "$(dirname "$0")"

mode="${1:-verify}"
neurosurg_python="${NEUROSURG_PYTHON:-python3}"

if ! command -v "$neurosurg_python" >/dev/null 2>&1; then
  echo "Python executable not found: $neurosurg_python" >&2
  echo "Set NEUROSURG_PYTHON to the interpreter containing requirements.txt." >&2
  exit 2
fi

export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1767225600}"  # fixed timestamp in PDF metadata
export MPLBACKEND="${MPLBACKEND:-Agg}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-$PWD/.cache/matplotlib}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$PWD/.cache}"
mkdir -p "$MPLCONFIGDIR" "$XDG_CACHE_HOME/fontconfig"

run_step() {
  echo "[$1] $2"
  "$neurosurg_python" "$2" "${@:3}"
}

case "$mode" in
  verify)  run_step "1/13" src/s01_fetch.py ;;
  refresh) run_step "1/13" src/s01_fetch.py --refresh ;;
  *) echo "Usage: ./run_all.sh [verify|refresh]" >&2; exit 2 ;;
esac

run_step "2/13" src/s02_build.py
run_step "3/13" src/s03_decompose.py
run_step "4/13" src/s07_substitution.py
run_step "5/13" src/s08_projection.py
run_step "6/13" src/s11_code_level.py
run_step "7/13" src/s12_robustness.py
run_step "8/13" src/s14_supplementary.py
run_step "9/13" src/s04_tables.py
run_step "10/13" src/s05_figures.py
run_step "11/13" src/s13_publication.py
run_step "12/13" src/s06_verify.py
run_step "13/13" src/s10_package.py
echo "done ($mode mode)"
