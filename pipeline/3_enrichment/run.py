import asyncio
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import click
from tqdm import tqdm

import config
from .modules.scrape import fetch_ebay_sold_average, fetch_pricecharting_prices


async def run_enrichment(
        records: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], int, int]:
    '''Scrape PriceCharting and eBay for records missing market_price.

    Returns updated records plus scrape counts (pricecharting, ebay).
    '''

    async def _enrich_one(
            record: Dict[str, Any],
            session: aiohttp.ClientSession,
            semaphore: asyncio.Semaphore,
        ) -> Optional[str]:
        async with semaphore:
            card_name = record.get("name")
            set_name = record.get("set_name")
            set_number = record.get("set_number")

            if not card_name or not set_name:
                return None

            set_number_str = str(set_number) if set_number else None
            prices = await fetch_pricecharting_prices(session, card_name, set_name, set_number_str)
            best_price = (
                prices.get("price_ungraded")
                or prices.get("price_psa10")
                or prices.get("price_graded_avg")
            )
            source = None

            if best_price:
                source = "pricecharting"
            else:
                ebay_price = await fetch_ebay_sold_average(
                    session, card_name, set_name, set_number_str,
                )
                if ebay_price:
                    prices["price_ungraded"] = ebay_price
                    best_price = ebay_price
                    source = "ebay"

            record["price_ungraded"] = prices.get("price_ungraded")
            record["price_psa10"] = prices.get("price_psa10")
            record["price_graded_avg"] = prices.get("price_graded_avg")
            if best_price:
                record["market_price"] = best_price

            return source

    missing = [r for r in records if r.get("market_price") is None]
    missing_before = len(missing)
    enriched_pc = 0
    enriched_ebay = 0

    if missing_before == 0:
        click.echo(
            f"Enrichment: {len(records)} total, 0 missing market_price, 0 enriched via scrape"
        )
        return records, 0, 0

    headers = {"User-Agent": config.USER_AGENT}
    semaphore = asyncio.Semaphore(config.ENRICHMENT_CONCURRENCY)

    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [_enrich_one(record, session, semaphore) for record in missing]
        for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Enrichment"):
            source = await coro
            if source == "pricecharting":
                enriched_pc += 1
            elif source == "ebay":
                enriched_ebay += 1

    click.echo(
        f"Enrichment: {len(records)} total, {missing_before} missing market_price, "
        f"{enriched_pc + enriched_ebay} enriched via scrape "
        f"(PC={enriched_pc}, eBay={enriched_ebay})"
    )
    return records, enriched_pc, enriched_ebay
