TCGDEX_BASE = "https://api.tcgdex.net/v2/en"
API_TIMEOUT = 30.0
API_RETRIES = 4
API_RETRY_BACKOFF_SEC = 2.0
MAX_CONCURRENT_REQUESTS = 5
ENRICHMENT_CONCURRENCY = 8

USER_AGENT = "Pokedecks/0.1 (+https://github.com/fnegri/pokedecks)"
GITHUB_REPO = "fnegri/pokedecks"
PRICECHARTING_BASE = "https://www.pricecharting.com"
EBAY_SEARCH_URL = "https://www.ebay.com/sch/i.html"

DEFAULT_DATABASE_URL = "sqlite:///./data/pokedecks.db"
DEFAULT_QUALITY_DIR = "./data/quality"
DEFAULT_ANALYSIS_DIR = "./data/analysis"

SUSPICIOUS_SET_MEAN_THRESHOLD = 50.0
SUSPICIOUS_SET_STDDEV_THRESHOLD = 0.01
EXPENSIVE_CARD_THRESHOLD = 100.0

# Set IDs with these prefixes are excluded from RQ analysis (trainer kits, etc.)
ANALYSIS_EXCLUDED_SET_PREFIXES = ("tk-",)

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

# CHART STYLE CONFIG

CHART_DPI = 120
CHART_FIGSIZE_WIDE = (12, 6)
CHART_FIGSIZE_DEFAULT = (10, 6)
CHART_FONT_FAMILY = "sans-serif"
CHART_FONT_SIZE = 11
CHART_TITLE_SIZE = 14
CHART_LABEL_SIZE = 11
CHART_SEABORN_STYLE = "whitegrid"
CHART_SEABORN_PALETTE = "muted"
CHART_BAR_COLOR = "#4C72B0"
CHART_LINE_COLOR = "#4C72B0"
CHART_LINE_MARKER = "o"
CHART_SCATTER_COLOR = "#4C72B0"
CHART_SCATTER_ALPHA = 0.2
CHART_SCATTER_SIZE = 8
CHART_XTICK_ROTATION = 45

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

_style_applied = False


def apply_chart_style() -> None:
    '''Apply matplotlib/seaborn defaults from CHART_* (once per process).'''
    global _style_applied
    if _style_applied:
        return
    plt.rcParams.update({
        "font.family": CHART_FONT_FAMILY,
        "font.size": CHART_FONT_SIZE,
        "axes.titlesize": CHART_TITLE_SIZE,
        "axes.labelsize": CHART_LABEL_SIZE,
        "xtick.labelsize": CHART_FONT_SIZE,
        "ytick.labelsize": CHART_FONT_SIZE,
    })
    sns.set_theme(style=CHART_SEABORN_STYLE, palette=CHART_SEABORN_PALETTE)
    _style_applied = True


def new_figure(wide: bool = False):
    '''Create a styled figure using CHART_FIGSIZE_WIDE or CHART_FIGSIZE_DEFAULT.'''
    apply_chart_style()
    size = CHART_FIGSIZE_WIDE if wide else CHART_FIGSIZE_DEFAULT
    return plt.figure(figsize=size)


def save_chart(path, title: str) -> None:
    '''Set title, layout, save PNG at CHART_DPI, and close the figure.'''
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=CHART_DPI)
    plt.close()


def rotate_xticks() -> None:
    '''Rotate x tick labels using CHART_XTICK_ROTATION.'''
    plt.xticks(rotation=CHART_XTICK_ROTATION, ha="right")
