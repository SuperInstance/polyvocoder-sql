# polyvocoder-sql

> **SQL polyformalism port for the Quilt canon archive.**
> SQLite byte-exact canon lookups via FNV-1a.

## What This Does

This is the SQL polyformalism port of the Quilt canon archive. It enables:

1. **In-database canon lookups** — query canon by lore hash
2. **Byte-exact FNV-1a** — same hash as Python/TS/Rust/C#/Bash
3. **JEV composite scoring** — store and query canon-worthy lore

## Quick Start

```bash
python3 canary.py
```

Should output:
```
Python FNV-1a-64: 0x24a555471370b18d
Verified (== expected): True
```

## Schema

```sql
CREATE TABLE canon_archive (
  cell_id TEXT PRIMARY KEY,
  rank INTEGER NOT NULL,
  seed TEXT,
  voice TEXT,
  doctrine TEXT,
  lore TEXT,
  composite REAL,
  canon_worthy REAL,
  distinct_voice REAL,
  doctrine_anchor REAL,
  lore_hash TEXT,  -- FNV-1a-64 of the lore text
  promoted INTEGER,
  stable INTEGER,
  generator TEXT,
  timestamp TEXT
);

CREATE INDEX idx_doctrine ON canon_archive(doctrine);
CREATE INDEX idx_promoted ON canon_archive(promoted);
CREATE INDEX idx_composite ON canon_archive(composite DESC);
```

## Usage

```python
import sqlite3

conn = sqlite3.connect("canon_archive.db")
cur = conn.cursor()

# Find all canon-promoted cells_are_scars lore
cur.execute("""
  SELECT rank, lore, composite
  FROM canon_archive
  WHERE doctrine = 'cells_are_scars' AND promoted = 1
  ORDER BY composite DESC
  LIMIT 10;
""")

for rank, lore, composite in cur.fetchall():
    print(f"Cell {rank}: composite={composite:.3f}")
    print(lore[:200])
    print("---")
```

## Fleet Canary

The SQL port pins to the Quilt fleet canary:
`fnv1a-64('café Δ 日本語') = 0x024a555471370b18d`

Verified via `canary.py` (Python helper).

## Why SQL?

- **In-database canon queries** — no need to load entire JSON into memory
- **Fast filtering** — index by doctrine, composite, voice
- **Relational integrity** — primary key on cell_id
- **Cross-language** — SQL is the universal query language

## Use Cases

- **Canon archives** — store 100k+ lore entries with sub-millisecond queries
- **Doctrine distribution** — `SELECT doctrine, COUNT(*) FROM canon_archive GROUP BY doctrine`
- **Composite analysis** — `SELECT AVG(composite) FROM canon_archive WHERE promoted=1`
- **Stability tracking** — `SELECT * FROM canon_archive WHERE stable=1 ORDER BY composite DESC`

## Polyformalism Fleet

This is port 7 of the polyformalism fleet:
1. Python
2. TypeScript
3. Rust
4. Bash
5. JavaScript ESM
6. C#/.NET 9
7. **SQL (SQLite)** ← you are here

All ports share the canary `0x024a555471370b18d`.

## License

MIT — Casey / SuperInstance, Sept 22, 2026
