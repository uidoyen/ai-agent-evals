"""Run every question's SQL and print the rows next to the stored keys, so the truth is reviewed by hand once.

Usage: check_truth.py [questions.json] [shop.db]   e.g. check_truth.py questions_messy.json shop_messy.db"""
import json, sqlite3
from pathlib import Path
HERE = Path(__file__).parent
import sys
qfile = sys.argv[1] if len(sys.argv) > 1 else "questions.json"
dbfile = sys.argv[2] if len(sys.argv) > 2 else "shop.db"
db = sqlite3.connect(f"{(HERE / dbfile).as_uri()}?mode=ro", uri=True)
for q in json.loads((HERE / qfile).read_text()):
    rows = db.execute(q["sql"]).fetchall()
    print(f"{q['id']} {q['kind']:4} keys={q['keys']!s:24} sql-> {rows}")
