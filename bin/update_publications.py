#!/usr/bin/env python3
"""
Rebuild _bibliography/papers.bib from a NASA ADS public library.

Usage (from the repository root):
    python bin/update_publications.py            # update papers.bib
    python bin/update_publications.py --dry-run  # show what would change

Needs an ADS API token (free): https://ui.adsabs.harvard.edu/user/settings/token
The token is read from, in order:
    1. the ADS_TOKEN environment variable
    2. the file ~/.ads/dev_key

Optional: _bibliography/extra_fields.yml lets you add al-folio fields
(selected, abbr, pdf, code, preview, ...) to specific papers, or hide papers,
without ever editing papers.bib by hand. See that file for examples.

Only the Python standard library is needed (PyYAML only if you use
extra_fields.yml).
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
LIBRARY_ID = "rTaH98YmTs6-aZoxtV7WXg"   # from the public-library URL
API_URL = os.environ.get("ADS_API_URL", "https://api.adsabs.harvard.edu/v1")

ROOT = Path(__file__).resolve().parent.parent
BIB_FILE = ROOT / "_bibliography" / "papers.bib"
EXTRA_FILE = ROOT / "_bibliography" / "extra_fields.yml"

EXPORT_OPTIONS = {
    "sort": ["date desc"],
    "maxauthor": 0,       # 0 = keep every author (the site shows the first few anyway)
    "journalformat": 3,   # 3 = full journal names ("Astronomy & Astrophysics")
}


# ---------------------------------------------------------------------------
# ADS API helpers
# ---------------------------------------------------------------------------
def get_token():
    token = os.environ.get("ADS_TOKEN") or os.environ.get("ADS_API_TOKEN")
    if not token:
        keyfile = Path.home() / ".ads" / "dev_key"
        if keyfile.exists():
            token = keyfile.read_text().strip()
    if not token:
        sys.exit(
            "No ADS token found. Create one at "
            "https://ui.adsabs.harvard.edu/user/settings/token and either\n"
            "  export ADS_TOKEN=<token>\n"
            "or save it in ~/.ads/dev_key"
        )
    return token


def api(path, token, payload=None):
    url = f"{API_URL}/{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:500]
        sys.exit(f"ADS API error {e.code} for {url}:\n{body}")
    except urllib.error.URLError as e:
        sys.exit(f"Could not reach ADS ({url}): {e.reason}")


def library_bibcodes(token):
    bibcodes, start, rows = [], 0, 500
    while True:
        res = api(f"biblib/libraries/{LIBRARY_ID}?start={start}&rows={rows}&fl=bibcode", token)
        docs = res.get("documents", [])
        # documents may be plain bibcodes or {"bibcode": ...} dicts
        bibcodes += [d["bibcode"] if isinstance(d, dict) else d for d in docs]
        total = res.get("metadata", {}).get("num_documents", len(bibcodes))
        start += rows
        if not docs or start >= total:
            break
    return list(dict.fromkeys(bibcodes))  # de-duplicate, keep order


def export_bibtex(bibcodes, token):
    chunks = []
    for i in range(0, len(bibcodes), 2000):
        res = api("export/bibtex", token, {"bibcode": bibcodes[i:i + 2000], **EXPORT_OPTIONS})
        chunks.append(res["export"])
    return "\n".join(chunks)


# ---------------------------------------------------------------------------
# BibTeX post-processing
# ---------------------------------------------------------------------------
ENTRY_HEAD = re.compile(r"^@\w+\s*\{\s*([^,\s]+)\s*,", re.M)


def split_entries(bibtex):
    """Return [(key, entry_text), ...]."""
    heads = list(ENTRY_HEAD.finditer(bibtex))
    out = []
    for n, m in enumerate(heads):
        end = heads[n + 1].start() if n + 1 < len(heads) else len(bibtex)
        out.append((m.group(1), bibtex[m.start():end].strip()))
    return out


def load_extras():
    if not EXTRA_FILE.exists():
        return {}
    try:
        import yaml
    except ImportError:
        sys.exit("extra_fields.yml exists but PyYAML is missing: pip install pyyaml")
    return yaml.safe_load(EXTRA_FILE.read_text()) or {}


def bib_value(v):
    if isinstance(v, bool):
        v = "true" if v else "false"
    return "{" + str(v) + "}"


def process(bibtex, extras):
    # al-folio turns the `html` field into the "HTML" button -> point it at ADS
    bibtex = re.sub(r"(?m)^(\s*)adsurl(\s*=)", r"\1  html\2", bibtex)

    entries = []
    for key, text in split_entries(bibtex):
        fields = dict(extras.get(key) or {})
        if fields.pop("hide", False):
            continue
        if fields:
            head_end = text.index(",") + 1
            added = "".join(f"\n{k:>13} = {bib_value(v)}," for k, v in fields.items())
            text = text[:head_end] + added + text[head_end:]
        entries.append((key, text))
    return entries


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="report changes without writing papers.bib")
    args = ap.parse_args()

    token = get_token()
    bibcodes = library_bibcodes(token)
    if not bibcodes:
        sys.exit("ADS returned an empty library - leaving papers.bib untouched.")
    print(f"ADS library {LIBRARY_ID}: {len(bibcodes)} papers")

    extras = load_extras()
    unknown = sorted(set(extras) - set(bibcodes))
    if unknown:
        print("Note: extra_fields.yml mentions bibcodes not in the library:", ", ".join(unknown))

    entries = process(export_bibtex(bibcodes, token), extras)
    if len(entries) < len(bibcodes) - sum(1 for v in extras.values() if v and v.get("hide")):
        sys.exit(f"Export returned only {len(entries)} entries - leaving papers.bib untouched.")
    new_text = "\n\n".join(t for _, t in entries) + "\n"

    old_text = BIB_FILE.read_text() if BIB_FILE.exists() else ""
    old_keys = {k for k, _ in split_entries(old_text)}
    new_keys = {k for k, _ in entries}
    for k in sorted(new_keys - old_keys):
        print("  + added  ", k)
    for k in sorted(old_keys - new_keys):
        print("  - removed", k)

    if new_text == old_text:
        print("papers.bib is already up to date.")
    elif args.dry_run:
        print("Dry run: papers.bib would be updated.")
    else:
        BIB_FILE.write_text(new_text)
        print(f"Wrote {BIB_FILE.relative_to(ROOT)} ({len(entries)} entries).")


if __name__ == "__main__":
    main()
