TCGDEX_BASE = "https://api.tcgdex.net/v2/en"
API_TIMEOUT = 30.0
API_RETRIES = 4
API_RETRY_BACKOFF_SEC = 2.0
MAX_CONCURRENT_REQUESTS = 5
ENRICHMENT_CONCURRENCY = 8

USER_AGENT = "Pokedecks/0.1 (+https://github.com/fnegri/pokedecks)"
PRICECHARTING_BASE = "https://www.pricecharting.com"
EBAY_SEARCH_URL = "https://www.ebay.com/sch/i.html"

DEFAULT_DATABASE_URL = "sqlite:///./data/pokedecks.db"
DEFAULT_QUALITY_DIR = "./data/quality"
DEFAULT_ANALYSIS_DIR = "./data/analysis"

SUSPICIOUS_SET_MEAN_THRESHOLD = 50.0
SUSPICIOUS_SET_STDDEV_THRESHOLD = 0.01
EXPENSIVE_CARD_THRESHOLD = 100.0

# card_prices column order and SQLite types (insertion order preserved)
SCHEMA_COLUMNS = {
    "snapshot_date": "TEXT",
    "id": "TEXT",
    "name": "TEXT",
    "rarity": "TEXT",
    "set_number": "TEXT",
    "image_url": "TEXT",
    "set_id": "TEXT",
    "set_name": "TEXT",
    "set_total_cards": "INTEGER",
    "set_release_date": "TEXT",
    "illustrator": "TEXT",
    "dex_id": "INTEGER",
    "price_cardmarket_avg": "REAL",
    "price_cardmarket_low": "REAL",
    "price_cardmarket_trend": "REAL",
    "price_tcgplayer_market": "REAL",
    "price_tcgplayer_low": "REAL",
    "market_price": "REAL",
    "price_ungraded": "REAL",
    "price_psa10": "REAL",
    "price_graded_avg": "REAL",
}
