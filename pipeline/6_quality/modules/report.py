from pathlib import Path
from typing import Any, Dict, Optional


def format_quality_summary(
        summary: Dict[str, Any],
        paths: Dict[str, Path],
        before_enrichment: Optional[Dict[str, Any]],
    ) -> str:
    '''Build the quality report as plain text for log file and terminal.'''
    comp = summary["completeness"]
    val = summary["validity"]
    lines = [
        "",
        "--- 1. Completeness ---",
        f"Total cards: {comp['total_cards']}",
        f"Market price filled: {comp['market_price_filled']} ({comp['market_price_filled_pct']})",
        f"Market price missing: {comp['market_price_missing']} ({comp['market_price_missing_pct']})",
        f"Missing name: {comp['missing_name']}, missing set_id: {comp['missing_set_id']}",
        "",
        "Price source breakdown:",
    ]
    for col, stats in comp["price_source_breakdown"].items():
        lines.append(f"  - {col}: {stats['count']} ({stats['pct']})")

    lines.extend([
        "",
        "--- 2. Price validity ---",
        f"Non-positive market_price: {val['non_positive_prices']}",
    ])
    if val["distribution"]:
        lines.append("Distribution:")
        for key, value in val["distribution"].items():
            lines.append(f"  {key}: {value:.4f}")

    lines.extend([
        "",
        "--- 3. Suspicious sets ---",
        f"Flagged sets: {summary['suspicious_sets_count']}",
    ])
    for row in summary["suspicious_sets"][:5]:
        lines.append(
            f"  {row['set_id']} ({row.get('set_name')}): "
            f"mean={row['mean']:.2f}, std={row['std']:.4f}, n={row['count']}"
        )

    lines.extend([
        "",
        "--- 4. Top sets missing market_price ---",
    ])
    for row in summary["top_sets_missing_price"][:5]:
        lines.append(
            f"  {row['set_id']} ({row.get('set_name')}): {row['missing_count']} cards"
        )

    lines.extend([
        "",
        "--- 5. Exported files ---",
    ])
    for label, path in paths.items():
        lines.append(f"  {label}: {path}")

    if before_enrichment:
        before = before_enrichment["market_price_filled_pct"]
        after = summary["after_enrichment"]["market_price_filled_pct"]
        lines.extend([
            "",
            "--- 6. Enrichment delta ---",
            f"Market price filled: {before} -> {after}",
        ])

    return "\n".join(lines)
