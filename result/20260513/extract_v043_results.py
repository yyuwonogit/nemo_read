"""Dump every populated v* result table from feas/NEMO_25 24.sqlite to CSV.

Output: mailbox/20260513/results_v043/<table>.csv with LEAP-name columns
(<dim>_name) appended via decode_dims.

Run once: `python mailbox/20260513/extract_v043_results.py`
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
from nemo_read import NemoDB, decode_dims

DB_PATH = Path("feas/NEMO_25 27.sqlite")
OUT_DIR = Path("mailbox/20260513/results_v045")


def main() -> int:
    if not DB_PATH.exists():
        print(f"[FAIL] {DB_PATH} not found", file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    db = NemoDB(str(DB_PATH))
    print(f"DB: {DB_PATH}  version={db.version}")

    result_tables = sorted(db.list_result_tables())
    print(f"Result tables: {len(result_tables)}")

    index_rows = []
    for tbl in result_tables:
        rc = db.row_count(tbl)
        if rc == 0:
            print(f"  skip {tbl} (0 rows)")
            index_rows.append({"table": tbl, "rows": 0, "csv": ""})
            continue
        df = db.query(f'SELECT * FROM "{tbl}"')
        df = decode_dims(df, db)
        out = OUT_DIR / f"{tbl}.csv"
        df.to_csv(out, index=False)
        size_kb = out.stat().st_size / 1024
        print(f"  wrote {tbl:42s} rows={rc:>7d}  size={size_kb:>8.1f} KB")
        index_rows.append({"table": tbl, "rows": rc, "csv": out.name})

    idx = pd.DataFrame(index_rows)
    idx.to_csv(OUT_DIR / "_index.csv", index=False)
    print(f"\nIndex: {OUT_DIR / '_index.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
