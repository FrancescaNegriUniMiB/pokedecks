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

SCHEMA_COLUMNS = [
    "snapshot_date",
    "id",
    "name",
    "rarity",
    "set_number",
    "image_url",
    "set_id",
    "set_name",
    "set_total_cards",
    "set_release_date",
    "illustrator",
    "dex_id",
    "price_cardmarket_avg",
    "price_cardmarket_low",
    "price_cardmarket_trend",
    "price_tcgplayer_market",
    "price_tcgplayer_low",
    "market_price",
    "price_ungraded",
    "price_psa10",
    "price_graded_avg",
]
