"""
Step 1. Retrieve source data and record checksums.

Two sources:
  1. OPCS-4 usage and usage breakdowns, from the opencodecounts R package data
     directory on GitHub (NHS England HES-APC aggregates, OGL v3.0).
  2. ONS mid-year population estimates for England by single year of age, from
     the Nomis API.

Default mode (python src/s01_fetch.py): every file listed in
data-raw/manifest.json that is not present locally is downloaded from the URL
recorded in the manifest, and every file is checked against its recorded
SHA-256. A mismatch stops the pipeline. The opencodecounts files are pinned to
an upstream commit, so their bytes do not change; the ONS extracts are
distributed with the repository because the Nomis API serves the current
release, which ONS revises.

Refresh mode (python src/s01_fetch.py --refresh): re-downloads every source
from its moving endpoint and rewrites the manifest. This is a deliberate data
update and changes the results.
"""

import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import config as cfg


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url, dest, attempts=5, base_wait=4):
    """Retrieve a URL, retrying on transient upstream failures.

    Nomis intermittently returns 503 under load. Retries are exponential and
    the final failure is raised rather than swallowed, so a partial build
    cannot be mistaken for a complete one.
    """
    import time
    import urllib.error

    req = urllib.request.Request(url, headers={"User-Agent": "opcs4-decomp/0.1"})
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                payload = r.read()
            if not payload:
                raise ValueError("empty response body")
            with open(dest, "wb") as f:
                f.write(payload)
            return dest
        except (urllib.error.HTTPError, urllib.error.URLError, ValueError,
                TimeoutError) as exc:
            if attempt == attempts:
                raise RuntimeError(
                    f"failed to retrieve {url} after {attempts} attempts"
                ) from exc
            wait = base_wait * 2 ** (attempt - 1)
            print(f"    attempt {attempt} failed ({exc}); retrying in {wait}s")
            time.sleep(wait)


def verify_or_fetch():
    """Download any missing source file and verify every checksum."""
    manifest = json.load(open(cfg.RAW / "manifest.json"))
    bad = []
    for name, meta in manifest["files"].items():
        dest = cfg.RAW / name
        if not dest.exists():
            print(f"  downloading {name}")
            download(meta["source"], dest)
        digest = sha256(dest)
        ok = digest == meta["sha256"]
        print(f"  {'OK ' if ok else 'BAD'} {name} {digest[:12]}")
        if not ok:
            bad.append(name)
    if bad:
        sys.exit(f"checksum mismatch for {bad}; the analysed snapshot cannot be reproduced")


def main():
    if "--refresh" not in sys.argv:
        verify_or_fetch()
        return
    cfg.RAW.mkdir(parents=True, exist_ok=True)
    manifest = {
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": {},
    }

    for name in cfg.RDA_FILES:
        dest = cfg.RAW / f"{name}.rda"
        download(f"{cfg.OPENCODECOUNTS_BASE}/{name}.rda", dest)
        manifest["files"][dest.name] = {
            "source": f"{cfg.OPENCODECOUNTS_BASE}/{name}.rda",
            "bytes": dest.stat().st_size,
            "sha256": sha256(dest),
        }
        print(f"  fetched {dest.name} ({dest.stat().st_size:,} bytes)")

    dates = ",".join(str(y) for y in cfg.MYE_YEARS)
    pop_dest = cfg.RAW / "ons_mye_england_sya.csv"
    download(cfg.NOMIS_URL.format(dates=dates), pop_dest)
    manifest["files"][pop_dest.name] = {
        "source": cfg.NOMIS_URL.format(dates=dates),
        "bytes": pop_dest.stat().st_size,
        "sha256": sha256(pop_dest),
    }
    print(f"  fetched {pop_dest.name} ({pop_dest.stat().st_size:,} bytes)")

    npp_dest = cfg.RAW / "ons_npp_england_sya.csv"
    npp_url = cfg.NPP_URL.format(
        years=",".join(str(y) for y in cfg.NPP_YEARS)
    )
    download(npp_url, npp_dest)
    manifest["files"][npp_dest.name] = {
        "source": npp_url,
        "bytes": npp_dest.stat().st_size,
        "sha256": sha256(npp_dest),
    }
    print(f"  fetched {npp_dest.name} ({npp_dest.stat().st_size:,} bytes)")

    with open(cfg.RAW / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  wrote manifest.json")


if __name__ == "__main__":
    main()
