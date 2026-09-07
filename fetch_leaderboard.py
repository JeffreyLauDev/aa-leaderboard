#!/usr/bin/env python3
"""Fetch the Artificial Analysis LLM leaderboard as structured JSON — no browser needed.

The leaderboard page is a Next.js App Router page. Requesting it with the
`RSC: 1` header returns the React Server Component flight payload, which
contains the full model table data as plain JSON arrays (metrics object per
model + metadata object per model). This script extracts and merges them.

Usage:
    python3 fetch_leaderboard.py                    # writes data/leaderboard.json
    python3 fetch_leaderboard.py -o out.json        # custom output path
"""

import argparse
import json
import re
import sys
import urllib.request

URL = "https://artificialanalysis.ai/leaderboards/models?status=all"
HEADERS = {
    "RSC": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Accept": "text/x-component",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_rsc(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def extract_array(text: str, anchor: str) -> list:
    """Bracket-match the JSON array that starts at the `[` following `anchor`."""
    i = text.find(anchor)
    if i < 0:
        raise ValueError(f"anchor {anchor!r} not found")
    start = text.find("[", i)
    depth = 0
    for j in range(start, len(text)):
        c = text[j]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : j + 1])
    raise ValueError("unbalanced array")


def extract_objects_with_field(text: str, field: str) -> list:
    """Extract every top-level {...} object containing `field` from flight data.

    Flight payload is a stream of lines like `c:[...]`. Model metric objects
    appear inline; we bracket-match each object whose body contains the field.
    """
    objs = []
    i = 0
    n = len(text)
    while True:
        i = text.find('{"id"', i)
        if i < 0:
            break
        # bracket-match forward from '{'
        depth = 0
        in_str = False
        esc = False
        end = -1
        for j in range(i, n):
            c = text[j]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
                continue
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = j
                    break
        if end < 0:
            break
        chunk = text[i : end + 1]
        if f'"{field}"' in chunk:
            try:
                obj = json.loads(chunk)
            except json.JSONDecodeError:
                obj = None
            if obj is not None:
                # strip RSC "$undefined" markers → None
                def clean(o):
                    if isinstance(o, dict):
                        return {k: clean(v) for k, v in o.items()}
                    if isinstance(o, list):
                        return [clean(v) for v in o]
                    return None if o == "$undefined" else o
                objs.append(clean(obj))
        i = end + 1
    return objs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--output", default="data/leaderboard.json")
    args = ap.parse_args()

    text = fetch_rsc(URL)

    # metadata array: slug/name/creator/release info
    models_meta = extract_array(text, '"models":[')
    # metrics objects: contain intelligenceIndex
    metrics = extract_objects_with_field(text, "intelligenceIndex")

    meta_by_slug = {m["slug"]: m for m in models_meta}
    rows = []
    for m in metrics:
        slug = m.get("slug")
        meta = meta_by_slug.get(slug, {})
        row = dict(m)
        row["creator"] = (meta.get("creator") or {}).get("name") if isinstance(meta.get("creator"), dict) else meta.get("creator")
        row["displayName"] = meta.get("name")
        effort = meta.get("effort")
        row["effort"] = effort.get("label") if isinstance(effort, dict) else effort
        release = meta.get("release")
        row["release"] = release.get("name") if isinstance(release, dict) else release
        row["releaseDate"] = meta.get("releaseDate") or m.get("releaseDate")
        row["deprecated"] = meta.get("deprecated", m.get("deprecated"))
        rows.append(row)

    out = {
        "source": URL,
        "fetchedAt": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "modelCount": len(rows),
        "models": rows,
    }
    import os
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"wrote {args.output}: {len(rows)} models", file=sys.stderr)


if __name__ == "__main__":
    main()
