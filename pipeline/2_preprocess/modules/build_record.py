from datetime import date
from typing import Any, Dict, Optional


def _extract_price(
        pricing_data: Optional[Dict[str, Any]],
        source: str,
        field: str,
    ) -> Optional[float]:
    '''Safely extract a price value from nested TCGdex pricing data.'''
    if not pricing_data:
        return None

    source_data = pricing_data.get(source)
    if not source_data:
        return None

    if source == "cardmarket":
        return source_data.get(field)

    if source == "tcgplayer":
        for variant in ["normal", "holofoil", "reverseHolofoil", "1stEdition"]:
            if variant in source_data and isinstance(source_data[variant], dict):
                val = source_data[variant].get(field)
                if val is not None:
                    return val
        return None

    return None


def build_record(
        snapshot_date: date,
        card_detail: Dict[str, Any],
    ) -> Dict[str, Any]:
    '''Build a flat warehouse record from TCGdex card detail.'''
    cd = card_detail
    pricing = cd.get("pricing") or {}
    card_set = cd.get("set") or {}
    card_count = card_set.get("cardCount") or {}
    set_id = card_set.get("id")

    cm_avg = _extract_price(pricing, "cardmarket", "avg")
    cm_low = _extract_price(pricing, "cardmarket", "low")
    cm_trend = _extract_price(pricing, "cardmarket", "trend")
    tcg_market = _extract_price(pricing, "tcgplayer", "marketPrice")
    tcg_low = _extract_price(pricing, "tcgplayer", "lowPrice")

    market_price = max(cm_avg or 0, tcg_market or 0) or None
    dex_ids = cd.get("dexId") or []

    return {
        "snapshot_date": snapshot_date.isoformat(),
        "id": cd.get("id"),
        "name": cd.get("name"),
        "rarity": cd.get("rarity"),
        "set_number": cd.get("localId"),
        "image_url": cd.get("image"),
        "set_id": set_id,
        "set_name": card_set.get("name"),
        "set_total_cards": card_count.get("official"),
        "set_release_date": card_set.get("releaseDate"),
        "illustrator": cd.get("illustrator"),
        "dex_id": dex_ids[0] if dex_ids else None,
        "price_cardmarket_avg": cm_avg,
        "price_cardmarket_low": cm_low,
        "price_cardmarket_trend": cm_trend,
        "price_tcgplayer_market": tcg_market,
        "price_tcgplayer_low": tcg_low,
        "market_price": market_price,
        "price_ungraded": None,
        "price_psa10": None,
        "price_graded_avg": None,
    }
