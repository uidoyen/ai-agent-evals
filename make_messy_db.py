"""Build shop_messy.db: the shop database with real-world traps, same schema, same questions.

Traps (each one a way a correct-looking query goes wrong):
- a second customer called Ben Okafor (id 6, Accra) with one order: grouping by name instead of id merges two people;
- an order with a NULL total (id 10, Emil Hansen, Keyboard stand): treating NULL as 0 changes "cheapest";
- one date stored as 12/10/2026 instead of 2026-10-12 (order 4): text ordering and julianday() break on it;
- Chen Wei's city stored as 'Taipei ' with a trailing space: WHERE city = 'Taipei' finds nobody.
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "shop_messy.db"
DB.unlink(missing_ok=True)
db = sqlite3.connect(DB)
db.executescript("""
CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL, city TEXT NOT NULL);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    item TEXT NOT NULL,
    total_eur REAL,
    ordered_on TEXT NOT NULL
);
""")
db.executemany("INSERT INTO customers VALUES (?,?,?)", [
    (1, "Ana Costa", "Lisbon"), (2, "Ben Okafor", "Lagos"), (3, "Chen Wei", "Taipei "), (4, "Dora Novak", "Prague"),
    (5, "Emil Hansen", "Oslo"), (6, "Ben Okafor", "Accra")])
db.executemany("INSERT INTO orders VALUES (?,?,?,?,?)", [
    (1, 1, "Desk lamp", 39.0, "2026-08-14"), (2, 1, "Monitor arm", 89.0, "2026-10-30"), (3, 2, "Keyboard", 120.0, "2026-09-02"),
    (4, 3, "USB hub", 25.0, "12/10/2026"), (5, 3, "Webcam", 65.0, "2026-11-03"), (6, 4, "Desk mat", 19.0, "2026-07-21"),
    (7, 5, "Headset", 75.0, "2026-11-05"), (8, 2, "Mouse", 45.0, "2026-08-19"), (9, 6, "Cable", 30.0, "2026-09-20"),
    (10, 5, "Keyboard stand", None, "2026-11-10")])
db.commit()
print("shop_messy.db:", db.execute("select count(*) from customers").fetchone()[0], "customers,", db.execute("select count(*) from orders").fetchone()[0], "orders")
