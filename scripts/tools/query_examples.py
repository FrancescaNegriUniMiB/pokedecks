#!/usr/bin/env python3

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text

import config
from util.query import get_engine, get_set_completion_cost


def run_queries() -> None:
    engine = get_engine(config.DEFAULT_DATABASE_URL)

    print("=" * 60)
    print("PokeDecks Database Query Examples")
    print("=" * 60)

    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM card_prices")).scalar()
        priced = conn.execute(
            text("SELECT COUNT(*) FROM card_prices WHERE market_price IS NOT NULL")
        ).scalar()
        print(f"\nTotal rows: {total:,}")
        print(f"Priced rows: {priced:,} ({100 * priced / total:.1f}%)" if total else "")

        print("\nTop 5 most expensive cards:")
        rows = conn.execute(
            text(
                """
                SELECT market_price, name, set_name, id
                FROM card_prices
                WHERE market_price IS NOT NULL
                ORDER BY market_price DESC
                LIMIT 5
                """
            )
        ).fetchall()
        for price, name, set_name, card_id in rows:
            print(f"  ${price:,.2f} | {name} | {set_name} ({card_id})")

        print("\nTop 5 sets by average market price (min 10 priced cards):")
        rows = conn.execute(
            text(
                """
                SELECT set_name, AVG(market_price) AS avg_price, COUNT(*) AS n
                FROM card_prices
                WHERE market_price IS NOT NULL AND set_name IS NOT NULL
                GROUP BY set_id, set_name
                HAVING COUNT(*) >= 10
                ORDER BY avg_price DESC
                LIMIT 5
                """
            )
        ).fetchall()
        for set_name, avg_price, count in rows:
            print(f"  {set_name}: ${avg_price:.2f} avg over {count} cards")

        print("\nTop 5 sets by completion cost (sum of priced cards):")
        rows = conn.execute(
            text(
                """
                SELECT set_name, SUM(market_price) AS total_cost, COUNT(*) AS n
                FROM card_prices
                WHERE market_price IS NOT NULL AND set_id IS NOT NULL
                GROUP BY set_id, set_name
                ORDER BY total_cost DESC
                LIMIT 5
                """
            )
        ).fetchall()
        for set_name, total_cost, count in rows:
            print(f"  {set_name}: ${total_cost:,.2f} total ({count} priced cards)")

        snapshot = conn.execute(text("SELECT MAX(snapshot_date) FROM card_prices")).scalar()
        if snapshot:
            sample_set = conn.execute(
                text(
                    """
                    SELECT set_id FROM card_prices
                    WHERE snapshot_date = :snapshot AND set_id IS NOT NULL
                    LIMIT 1
                    """
                ),
                {"snapshot": snapshot},
            ).scalar()
            if sample_set:
                cost = get_set_completion_cost(sample_set, snapshot, engine)
                print(f"\nSet completion example ({sample_set}, snapshot {snapshot}):")
                print(f"  Total cost: ${cost['total_cost']:,.2f}")
                print(f"  Priced cards: {cost['priced_cards']} / {cost['total_cards']}")
                print(f"  Missing price: {cost['missing_price_count']} cards")


if __name__ == "__main__":
    run_queries()
