#!/usr/bin/env python3
"""Flatten data/leaderboard.json into data/leaderboard.csv (main columns)."""

import csv
import json

COLS = [
    "displayName", "name", "creator", "release", "effort", "releaseDate",
    "deprecated", "isReasoning", "intelligenceIndex", "intelligenceIndexIsEstimated",
    "codingIndex", "agenticIndex",
    "gdpvalNormalized", "tau2", "tauBanking", "terminalbenchHard", "terminalbenchV21",
    "scicode", "lcr", "omniscience", "omniscienceAccuracy", "omniscienceNonHallucination",
    "hle", "gpqa", "critpt", "apexAgents", "analystAgent", "itbenchSre", "mmmuPro", "ifbench",
    "price1mBlended0To3To1", "price1mInputTokens", "price1mOutputTokens",
    "cacheHitPrice", "cacheWritePrice", "intelligenceIndexCostPerTask",
    "medianOutputTokensPerSecond", "medianTimeToFirstTokenSeconds",
    "medianEndToEndResponseTimeSeconds", "medianReasoningTimeSeconds",
    "percentile05OutputTokensPerSecond", "percentile95OutputTokensPerSecond",
    "quartile25OutputTokensPerSecond", "quartile75OutputTokensPerSecond",
    "contextWindowTokens", "totalParameters", "activeParameters", "sizeClass", "paramClass",
    "isOpenWeights", "licenseName", "openrouterApiId", "huggingfaceUrl",
]

def main() -> None:
    data = json.load(open("data/leaderboard.json"))
    models = sorted(data["models"], key=lambda m: -(m.get("intelligenceIndex") or -1))
    with open("data/leaderboard.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for m in models:
            w.writerow([m.get(c) if m.get(c) is not None else "" for c in COLS])
    print(f"wrote data/leaderboard.csv: {len(models)} rows")

if __name__ == "__main__":
    main()
