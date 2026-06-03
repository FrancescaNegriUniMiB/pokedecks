# Processing phase

Flattens nested TCGdex JSON into warehouse **records** with API-derived prices and an initial `market_price`.

**Entry point:** `run.py` → `run_processing`

---

## Data flow

```
List[TCGdex detail dict]  ──►  run_processing  ──►  List[WarehouseRecord]
         + snapshot_date
```

### `WarehouseRecord`

Flat `Dict[str, Any]` with keys from `config.SCHEMA_COLUMNS`. Price enrichment fields start as `None`.

| Field | Type | Source |
|-------|------|--------|
| `snapshot_date` | `str` (ISO date) | argument |
| `id` | `Optional[str]` | `card_detail["id"]` |
| `name` | `Optional[str]` | `card_detail["name"]` |
| `rarity` | `Optional[str]` | `card_detail["rarity"]` |
| `set_number` | `Optional[str]` | `card_detail["localId"]` |
| `image_url` | `Optional[str]` | `card_detail["image"]` |
| `set_id` | `Optional[str]` | `card_detail["set"]["id"]` |
| `set_name` | `Optional[str]` | `card_detail["set"]["name"]` |
| `set_total_cards` | `Optional[int]` | `card_detail["set"]["cardCount"]["official"]` |
| `set_release_date` | `Optional[str]` | `card_detail["set"]["releaseDate"]` (from acquisition) |
| `price_cardmarket_avg` | `Optional[float]` | TCGdex `pricing.cardmarket.avg` |
| `price_cardmarket_low` | `Optional[float]` | TCGdex `pricing.cardmarket.low` |
| `price_cardmarket_trend` | `Optional[float]` | TCGdex `pricing.cardmarket.trend` |
| `price_tcgplayer_market` | `Optional[float]` | TCGdex `pricing.tcgplayer.*.marketPrice` |
| `price_tcgplayer_low` | `Optional[float]` | TCGdex `pricing.tcgplayer.*.lowPrice` |
| `market_price` | `Optional[float]` | `max(cm_avg, tcg_market)` or `None` if both missing |
| `price_ungraded` | `None` | filled by enrichment |
| `price_psa10` | `None` | filled by enrichment |
| `price_graded_avg` | `None` | filled by enrichment |

---

## `run.py`

### `run_processing`

| | |
|---|---|
| **Input** | |
| `snapshot_date` | `datetime.date` |
| `acquired` | `List[Dict[str, Any]]` — TCGdex detail dicts from acquisition |
| **Output** | `List[Dict[str, Any]]` — one warehouse record per acquired card |
| **Side effects** | none |

Calls `build_record(snapshot_date, detail)` for each item.

---

## `modules/build_record.py`

### `_extract_price` (internal)

Safely reads a single price from nested TCGdex `pricing` JSON.

| | |
|---|---|
| **Input** | |
| `pricing_data` | `Optional[Dict[str, Any]]` — `card_detail["pricing"]` |
| `source` | `str` — `"cardmarket"` or `"tcgplayer"` |
| `field` | `str` — field name to read (e.g. `"avg"`, `"marketPrice"`) |
| **Output** | `Optional[float]` |

**Cardmarket:** reads `pricing_data["cardmarket"][field]` directly.

**TCGplayer:** walks variants in order `normal` → `holofoil` → `reverseHolofoil` → `1stEdition` and returns the first non-null `field` value.

### `build_record`

| | |
|---|---|
| **Input** | |
| `snapshot_date` | `datetime.date` |
| `card_detail` | `Dict[str, Any]` — full TCGdex detail |
| **Output** | `Dict[str, Any]` — flat warehouse record (see schema above) |

**`market_price` logic:**

```python
market_price = max(cm_avg or 0, tcg_market or 0) or None
```

If both API prices are missing or zero, `market_price` is `None` and the record will be picked up by enrichment.
