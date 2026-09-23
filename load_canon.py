"""Load the canon archive into SQLite.

Reads /workspace/research/substrate-walker/canon/lore_pack.json and writes
to canon_archive.db.
"""
import json
import sqlite3
import sys

sys.path.insert(0, "/workspace/repos/polyvocoder/polyvocoder")
from canary import fnv1a_64


SCHEMA = """
CREATE TABLE IF NOT EXISTS canon_archive (
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
  lore_hash TEXT,
  promoted INTEGER,
  stable INTEGER,
  generator TEXT,
  timestamp TEXT
);

CREATE INDEX IF NOT EXISTS idx_doctrine ON canon_archive(doctrine);
CREATE INDEX IF NOT EXISTS idx_promoted ON canon_archive(promoted);
CREATE INDEX IF NOT EXISTS idx_composite ON canon_archive(composite DESC);
CREATE INDEX IF NOT EXISTS idx_voice ON canon_archive(voice);
"""


def compute_hash(text):
    if not text:
        return ''
    encoded = text.encode('utf-8')
    return '0x{:016x}'.format(fnv1a_64(encoded))


def load(lore_pack_path, db_path="canon_archive.db"):
    pack = json.load(open(lore_pack_path))
    lores = pack['lores']

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    cur.execute("DELETE FROM canon_archive")

    for lore in lores:
        lore_text = lore.get('lore_snippet', '') or ''
        lore_hash = compute_hash(lore_text)
        cur.execute("""
            INSERT INTO canon_archive VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lore.get('cell_id', "cell_{}".format(lore['rank'])),
            lore['rank'],
            str(lore.get('seed', '')),
            lore.get('voice', ''),
            lore.get('primary_doctrine', ''),
            lore_text,
            lore.get('score', 0),
            lore.get('jev_canon_worthy', 0),
            lore.get('jev_distinct_voice', 0),
            lore.get('jev_doctrine_anchor', 0),
            lore_hash,
            1 if lore.get('promoted') else 0,
            1 if lore.get('stable') else 0,
            lore.get('generator', ''),
            '2026-09-22T23:50:00Z',
        ))

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM canon_archive")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM canon_archive WHERE promoted = 1")
    promoted = cur.fetchone()[0]

    print("Loaded {} cells into {}".format(total, db_path))
    print("  Promoted: {}".format(promoted))

    cur.execute("SELECT doctrine, COUNT(*) FROM canon_archive WHERE promoted=1 GROUP BY doctrine")
    print("  Doctrine distribution (promoted only):")
    for d, c in cur.fetchall():
        print("    {}: {}".format(d, c))

    cur.execute("SELECT AVG(composite) FROM canon_archive WHERE promoted=1")
    avg = cur.fetchone()[0]
    print("  Average composite (promoted): {:.3f}".format(avg))

    # Sample queries
    print("\nTop 5 canon-promoted cells:")
    cur.execute("SELECT rank, voice, doctrine, composite FROM canon_archive WHERE promoted=1 ORDER BY composite DESC LIMIT 5")
    for rank, voice, doctrine, composite in cur.fetchall():
        print("  Cell {}: {} ({}): {:.3f}".format(rank, voice, doctrine, composite))

    conn.close()


if __name__ == "__main__":
    pack = sys.argv[1] if len(sys.argv) > 1 else "/workspace/research/substrate-walker/canon/lore_pack.json"
    db = sys.argv[2] if len(sys.argv) > 2 else "canon_archive.db"
    load(pack, db)
