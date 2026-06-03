import asyncio
import random
import re
from typing import Dict, Optional
from urllib.parse import quote

import aiohttp
from selectolax.parser import HTMLParser

import config


def _parse_price(text: str) -> Optional[float]:
    '''Extract the first price amount from scraped text.'''
    if not text or "n/a" in text.lower():
        return None
    try:
        match = re.search(r"\$\s?([\d,]+\.?\d*)", text) or re.search(r"([\d,]+\.?\d*)", text)
        if match:
            return float(match.group(1).replace(",", ""))
    except (ValueError, AttributeError):
        return None
    return None


def _cell_price(html: HTMLParser, cell_id: str) -> Optional[float]:
    '''Read a float price from a PriceCharting cell id.'''
    node = html.css_first(f"#{cell_id}")
    if not node:
        return None
    price_node = node.css_first(".price")
    text = price_node.text(strip=True) if price_node else node.text(strip=True)
    return _parse_price(text)


async def _get_html(session: aiohttp.ClientSession, url: str) -> Optional[HTMLParser]:
    '''Fetch and parse HTML with polite delay.'''
    try:
        await asyncio.sleep(random.uniform(1.0, 2.0))
        async with session.get(url, timeout=config.API_TIMEOUT) as resp:
            if resp.status == 404:
                return None
            resp.raise_for_status()
            return HTMLParser(await resp.text())
    except Exception:
        return None


def _parse_product_prices(product_html: HTMLParser) -> Dict[str, Optional[float]]:
    '''Parse ungraded, psa10 and graded average from a PriceCharting product page.'''
    prices: Dict[str, Optional[float]] = {
        "price_ungraded": None,
        "price_psa10": None,
        "price_graded_avg": None,
    }

    prices["price_ungraded"] = _cell_price(product_html, "ungraded_price")
    if not prices["price_ungraded"]:
        for row in product_html.css("table#price_data tr"):
            cells = row.css("td")
            if cells:
                extracted = _parse_price(cells[0].text(strip=True))
                if extracted:
                    prices["price_ungraded"] = extracted
                    break

    prices["price_graded_avg"] = _cell_price(product_html, "graded_price")

    manual_title_node = product_html.css_first("td#manual_only_price span.title")
    if manual_title_node and "PSA 10" in manual_title_node.text(strip=True):
        prices["price_psa10"] = _cell_price(product_html, "manual_only_price")

    return prices


async def fetch_pricecharting_prices(
        session: aiohttp.ClientSession,
        card_name: str,
        set_name: str,
        set_number: Optional[str] = None,
    ) -> Dict[str, Optional[float]]:
    '''Search PriceCharting and return ungraded, psa10 and graded average prices.'''
    prices: Dict[str, Optional[float]] = {
        "price_ungraded": None,
        "price_psa10": None,
        "price_graded_avg": None,
    }

    query_parts = [card_name, set_name]
    if set_number:
        query_parts.append(str(set_number))
    query = " ".join(query_parts).strip()
    search_url = f"{config.PRICECHARTING_BASE}/search-products?q={quote(query)}&type=prices"

    html = await _get_html(session, search_url)
    if not html:
        return prices

    first_result = html.css_first("table#games_table tr:nth-child(2) td.title a")
    if not first_result:
        return prices

    product_path = first_result.attributes.get("href")
    if not product_path:
        return prices

    product_url = (
        product_path
        if product_path.startswith("http")
        else f"{config.PRICECHARTING_BASE}{product_path}"
    )

    product_html = await _get_html(session, product_url)
    if not product_html:
        return prices

    return _parse_product_prices(product_html)


async def fetch_ebay_sold_average(
        session: aiohttp.ClientSession,
        card_name: str,
        set_name: str,
        set_number: Optional[str] = None,
    ) -> Optional[float]:
    '''Return average sold price from the first five eBay sold listings.'''
    query_parts = [card_name, set_name]
    if set_number:
        query_parts.append(str(set_number))
    query = f"{' '.join(query_parts)} pokemon card"

    params = {
        "_nkw": query,
        "LH_Sold": "1",
        "LH_Complete": "1",
        "_ipg": "60",
    }

    try:
        await asyncio.sleep(random.uniform(1.5, 3.0))
        async with session.get(
            config.EBAY_SEARCH_URL, params=params, timeout=config.API_TIMEOUT
        ) as resp:
            if resp.status != 200:
                return None
            html = HTMLParser(await resp.text())

        prices = []
        for item in html.css(".s-item__info"):
            if "Shop on eBay" in item.text(strip=True):
                continue
            price_node = item.css_first(".s-item__price")
            if not price_node:
                continue
            price = _parse_price(price_node.text(strip=True))
            if price:
                prices.append(price)
            if len(prices) >= 5:
                break

        if not prices:
            return None
        return sum(prices) / len(prices)
    except Exception:
        return None
