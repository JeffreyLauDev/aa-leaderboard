# aa-leaderboard

Daily pipeline that scrapes the [Artificial Analysis LLM Leaderboard](https://artificialanalysis.ai/leaderboards/models) — all ~640 models with full metrics (Intelligence Index breakdown, benchmark scores, pricing, speed percentiles) — and picks out the **free models**, ranked by intelligence.

Data lands in `data/` every day via GitHub Actions. No browser, no API key, no scraping infra — just one HTTP GET with an `RSC: 1` header that returns the page's React Server Component payload containing the whole table as JSON.

## Outputs

| File | What |
|---|---|
| `data/leaderboard.json` | Full leaderboard: 640+ models × 70+ fields each |
| `data/leaderboard.csv` | Same, flattened to the main columns |
| `data/free_models.json` / `.csv` / `.md` | Free models only, ranked by Intelligence Index |

## Quick start

```bash
pip install -r requirements.txt   # nothing — stdlib only
python3 fetch_leaderboard.py          # → data/leaderboard.json
python3 pick_free_models.py           # → data/free_models.{json,csv,md}
```

### Options

```bash
# free models only (default)
python3 pick_free_models.py --max-price 0

# anything under $0.50/1M blended, top 50, intelligence ≥ 30
python3 pick_free_models.py --max-price 0.5 --top 50 --min-intelligence 30
```

## Daily automation

`.github/workflows/daily.yml` runs every day at 03:00 UTC (and on every push to `main` touching the scripts):

1. `fetch_leaderboard.py` — pull fresh data
2. `pick_free_models.py` — rank free models
3. `to_csv.py` — flatten leaderboard to CSV
4. Auto-commit updated `data/` back to `main`

## How the scraper works (no API key)

The leaderboard is a Next.js App Router page. Requesting it with header `RSC: 1` returns the React flight payload (~3.5MB text) which embeds:

- `"models":[...]` — slug / name / creator / release metadata
- one object per model containing `intelligenceIndex` — all metrics (benchmark scores, prices, speed percentiles, context window, `openrouterApiId`, license...)

`fetch_leaderboard.py` bracket-matches those JSON fragments out of the payload and merges them by slug. If Artificial Analysis ever changes their payload shape, the script fails loudly (non-zero exit) and the Action turns red — no silent bad data.

## Fields worth knowing

Each model row includes (among ~70 fields):

- `intelligenceIndex` + per-benchmark breakdown: `gdpvalNormalized`, `tau2`, `tauBanking`, `terminalbenchHard`, `terminalbenchV21`, `scicode`, `lcr`, `omniscience*`, `hle`, `gpqa`, `critpt`, `apexAgents`, `analystAgent`, `itbenchSre`, `mmmuPro`, `ifbench`
- pricing: `price1mInputTokens`, `price1mOutputTokens`, `cacheHitPrice`, `cacheWritePrice`, blended prices for several I:O mixes, `intelligenceIndexCostPerTask`
- speed/latency: `medianOutputTokensPerSecond`, P5/P25/P75/P95 tokens/s and time-to-first-token, `medianEndToEndResponseTimeSeconds`, `medianReasoningTimeSeconds`
- meta: `contextWindowTokens`, `isOpenWeights`, `licenseName`, `openrouterApiId`, `huggingfaceUrl`, modalities, param counts

## License

MIT — see [LICENSE](LICENSE). Data originates from Artificial Analysis; check their terms if you republish at scale.
