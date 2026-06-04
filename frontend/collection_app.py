import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from sqlalchemy import text

import config
from frontend.ui import render_exit_button
from pipeline import import_phase

_db = import_phase("5_storing.modules.db")
_query = import_phase("5_storing.modules.query")

add_owned_card = _db.add_owned_card
get_engine = _db.get_engine
get_owned_card_ids = _db.get_owned_card_ids
init_collection_table = _db.init_collection_table
init_table = _db.init_table
remove_owned_card = _db.remove_owned_card
get_set_cards = _query.get_set_cards
get_set_completion_cost = _query.get_set_completion_cost
list_sets = _query.list_sets


def list_snapshot_dates(engine) -> list[str]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT DISTINCT snapshot_date FROM card_prices ORDER BY snapshot_date DESC")
        ).fetchall()
    return [row[0] for row in rows]


st.set_page_config(page_title="PokeDecks Collection", layout="wide")
render_exit_button()
st.title("PokeDecks — Set Completion (RQ4)")
st.caption("Select a set and mark owned cards to track remaining completion cost.")

engine = get_engine(config.DEFAULT_DATABASE_URL)
init_table(engine)
init_collection_table(engine)

snapshots = list_snapshot_dates(engine)
if not snapshots:
    st.warning("No data in database. Run the pipeline first.")
    st.stop()

username = st.text_input("Username", value="collector")
snapshot_date = st.selectbox("Snapshot date", snapshots)
sets_df = list_sets(snapshot_date, engine)

if sets_df.empty:
    st.warning("No sets found for this snapshot.")
    st.stop()

set_labels = {
    f"{row.set_name} ({row.set_id})": row.set_id for row in sets_df.itertuples()
}
selected_label = st.selectbox("Set", list(set_labels.keys()))
set_id = set_labels[selected_label]

owned_ids = get_owned_card_ids(username, snapshot_date, engine)
cost = get_set_completion_cost(set_id, snapshot_date, engine, list(owned_ids))

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total set cost", f"${cost['total_cost']:,.2f}")
col2.metric("Owned value", f"${cost['owned_cost']:,.2f}")
col3.metric("Remaining cost", f"${cost['remaining_cost']:,.2f}")
col4.metric("Owned cards", f"{cost['owned_count']} / {cost['priced_cards']}")

if cost["missing_price_count"]:
    st.info(f"{cost['missing_price_count']} cards in this set have no market price (excluded from totals).")

cards = get_set_cards(set_id, snapshot_date, engine)
st.subheader("Your collection")

for row in cards.itertuples():
    owned = row.id in owned_ids
    price_label = f"${row.market_price:,.2f}" if row.market_price == row.market_price else "N/A"
    checked = st.checkbox(
        f"{row.name} ({row.set_number}) — {price_label}",
        value=owned,
        key=f"{username}:{snapshot_date}:{row.id}",
    )
    if checked and not owned:
        add_owned_card(username, row.id, snapshot_date, engine)
        owned_ids.add(row.id)
    elif not checked and owned:
        remove_owned_card(username, row.id, snapshot_date, engine)
        owned_ids.discard(row.id)
