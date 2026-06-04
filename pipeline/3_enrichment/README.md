# Enrichment phase

Scrapes **PriceCharting** and **eBay sold listings** for records where `market_price` is still `None` after preprocess.

**Entry point:** `run.py` → `run_enrichment` (async)

**Stack:** `aiohttp` + `selectolax`, semaphore `config.ENRICHMENT_CONCURRENCY` (8)

---

## Data flow

```
List[WarehouseRecord]  ──►  run_enrichment  ──►  records + (enriched_pc, enriched_ebay)
         │
         └── only rows where market_price is None
```

Integration metrics and JSON export live in **6_quality** (`build_integration_metrics`, `export_integration_metrics`).

---

## `run.py`

### `run_enrichment`

| | |
|---|---|
| **Input** | `records: List[Dict[str, Any]]` |
| **Output** | `records`, `enriched_pc: int`, `enriched_ebay: int` |
| **Side effects** | HTTP requests to PriceCharting and eBay; console stats via `click.echo` |

**Internal helper (nested):** `_enrich_one`

---

## `modules/scrape.py`

| Function | Source | Output |
|----------|--------|--------|
| `fetch_pricecharting_prices` | PriceCharting (primary) | `price_ungraded`, `price_psa10`, `price_graded_avg` |
| `fetch_ebay_sold_average` | eBay sold search (fallback) | mean of up to 5 listing prices |
