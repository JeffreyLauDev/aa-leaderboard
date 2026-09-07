#!/usr/bin/env python3
"""Pick free (or cheapest) capable models from the Artificial Analysis leaderboard.

"Free" here = zero priced via at least one API provider (OpenRouter :free models,
or vendor free tiers). The script ranks free models by the AA Intelligence Index
and emits:
  - data/free_models.json   full rows
  - data/free_models.csv    spreadsheet-friendly
  - data/free_models.md     human-readable leaderboard table (committed to git)

Usage:
    python3 pick_free_models.py [--max-price 0] [--top 30] [--min-intelligence 20]
"""

import argparse
import csv
import json
import os

def fmt(v, nd=1):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/leaderboard.json")
    ap.add_argument("--max-price", type=float, default=0.0,
                    help="max blended USD price per 1M tokens (0 = free only)")
    ap.add_argument("--top", type=int, default=30, help="rows to keep in output")
    ap.add_argument("--min-intelligence", type=float, default=0.0)
    args = ap.parse_args()

    data = json.load(open(args.input))
    models = data["models"]

    rows = []
    for m in models:
        price = m.get("price1mBlended0To3To1")
        intel = m.get("intelligenceIndex")
        if price is None or intel is None:
            continue
        if price > args.max_price:
            continue
        if intel < args.min_intelligence:
            continue
        if m.get("deprecated"):
            continue
        rows.append(m)

    rows.sort(key=lambda m: -(m["intelligenceIndex"] or 0))
    rows = rows[: args.top]

    os.makedirs("data", exist_ok=True)
    with open("data/free_models.json", "w") as f:
        json.dump({"generatedAt": data["fetchedAt"], "count": len(rows), "models": rows},
                  f, ensure_ascii=False, indent=1)

    cols = ["displayName", "creator", "intelligenceIndex", "price1mBlended0To3To1",
            "price1mInputTokens", "price1mOutputTokens", "medianOutputTokensPerSecond",
            "contextWindowTokens", "openrouterApiId", "isOpenWeights", "licenseName"]
    headers = ["Model", "Creator", "Intelligence Index", "Blended Price USD/1M",
               "Input USD/1M", "Output USD/1M", "Median Tokens/s", "Context Window",
               "OpenRouter ID", "Open Weights", "License"]
    with open("data/free_models.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for m in rows:
            w.writerow([fmt(m.get(c), 4 if "price" in c.lower() or c == "price1mBlended0To3To1" else 1)
                        if isinstance(m.get(c), float) else (m.get(c) if m.get(c) is not None else "")
                        for c in cols])

    with open("data/free_models.md", "w") as f:
        f.write(f"# Free Models Leaderboard\n\n")
        f.write(f"Generated {data['fetchedAt']} from Artificial Analysis. "
                f"{len(rows)} models, ranked by Intelligence Index. "
                f"Blended price = 0:3:1 input:cache:output mix.\n\n")
        f.write("| # | Model | Creator | Intelligence | In $/1M | Out $/1M | Tokens/s | Context | OpenRouter ID |\n")
        f.write("|---|-------|---------|--------------|---------|----------|----------|---------|---------------|\n")
        for i, m in enumerate(rows, 1):
            f.write(f"| {i} | {m.get('displayName') or m.get('name')} | {m.get('creator') or ''} "
                    f"| {fmt(m.get('intelligenceIndex'))} "
                    f"| {fmt(m.get('price1mInputTokens'), 3)} | {fmt(m.get('price1mOutputTokens'), 3)} "
                    f"| {fmt(m.get('medianOutputTokensPerSecond'), 0)} | {fmt(m.get('contextWindowTokens'), 0)} "
                    f"| {m.get('openrouterApiId') or ''} |\n")

    print(f"picked {len(rows)} models (max price ${args.max_price}/1M)")

if __name__ == "__main__":
    main()
