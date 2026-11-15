"""The shop database as three read-only MCP tools (videos 14 to 17).

Environment (set per MCP config, so one factor changes at a time):
  SHOP_DB    database file next to this script (default shop.db; shop_messy.db for the messy-data set)
  SHOP_DOCS  tool descriptions: default | vague | precise (the words chapter)
"""
import os
import sqlite3
from pathlib import Path

from mcp.server import MCPServer

mcp = MCPServer("shop-db")
DB = (Path(__file__).parent / os.environ.get("SHOP_DB", "shop.db")).resolve()
MAX_ROWS = 50

DOCS = {
    "default": {
        "list_tables": "List the tables in the shop database. Call this first.",
        "describe_table": "Show the columns of one table, with their types.\n\n    Args:\n        table: Table name, exactly as list_tables returned it\n    ",
        "run_query": "Run one SQL statement on the shop database (SQLite) and return the rows.\n\n    The database is opened read-only: statements that write will fail.\n\n    Args:\n        sql: One SQL statement\n    ",
    },
    "vague": {
        "list_tables": "List tables.",
        "describe_table": "Describe a table.\n\n    Args:\n        table: table\n    ",
        "run_query": "Run a query.\n\n    Args:\n        sql: sql\n    ",
    },
    "precise": {
        "list_tables": "List the tables in the shop database (SQLite, read-only). The shop has two tables: customers (id, name, city) "
                       "and orders (id, customer_id -> customers.id, item, total_eur, ordered_on as ISO text). Call this first.",
        "describe_table": "Show the columns of one table, with their types. customers: id INTEGER, name TEXT, city TEXT. orders: id INTEGER, "
                          "customer_id INTEGER (references customers.id), item TEXT, total_eur REAL (euros), ordered_on TEXT (YYYY-MM-DD).\n\n"
                          "    Args:\n        table: Table name, exactly as list_tables returned it\n    ",
        "run_query": "Run one SQL statement on the shop database (SQLite) and return up to 50 rows. Read-only: writes fail. Join orders to "
                     "customers on orders.customer_id = customers.id; group people by customers.id, not by name; dates are ISO text, so "
                     "compare them as strings or with julianday(); total_eur may be NULL for an order that has no total yet.\n\n"
                     "    Args:\n        sql: One SQL statement\n    ",
    },
}[os.environ.get("SHOP_DOCS", "default")]


def connect() -> sqlite3.Connection:
    # mode=ro: SQLite itself refuses every write, whatever the SQL says
    return sqlite3.connect(f"{DB.as_uri()}?mode=ro", uri=True)


@mcp.tool(description=DOCS["list_tables"])
def list_tables() -> str:
    with connect() as db:
        rows = db.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    return ", ".join(name for (name,) in rows)


@mcp.tool(description=DOCS["describe_table"])
def describe_table(table: str) -> str:
    with connect() as db:
        rows = db.execute(
            "SELECT name, type FROM pragma_table_info(?)", (table,)
        ).fetchall()
    if not rows:
        return f"There is no table called {table}."
    return ", ".join(f"{name} {kind}" for name, kind in rows)


@mcp.tool(description=DOCS["run_query"])
def run_query(sql: str) -> str:
    try:
        with connect() as db:
            cursor = db.execute(sql)  # execute() runs one statement; never executescript()
            rows = cursor.fetchmany(MAX_ROWS)
    except sqlite3.Error as error:
        return f"The query failed: {error}"
    if not rows:
        return "No rows."
    header = " | ".join(column[0] for column in cursor.description)
    lines = [" | ".join(str(value) for value in row) for row in rows]
    return "\n".join([header, *lines])


if __name__ == "__main__":
    mcp.run(transport="stdio")
