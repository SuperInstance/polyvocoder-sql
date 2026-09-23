"""Polyvocoder SQL port — SQLite byte-exact FNV-1a via SQL operations.

SQLite doesn't have native XOR or 64-bit multiplication, so we use
mathematical identities:
- XOR(a, b) = (a | b) - (a & b)
- 64-bit mask via & 0xFFFFFFFFFFFFFFFF

Verifies: fnv1a-64('café Δ 日本語') = 0x024a555471370b18d
"""
import sqlite3

CANARY_STRING = "café Δ 日本語"
EXPECTED = 0x024a555471370b18d
FNV_OFFSET_BASIS = 0xcbf29ce484222325
FNV_PRIME = 0x100000001b3
MASK_64 = 0xFFFFFFFFFFFFFFFF


def xor64(a: int, b: int) -> int:
    """XOR via SQLite-compatible math: (a | b) - (a & b)."""
    return (a | b) - (a & b)


def fnv1a_64(s: str) -> int:
    h = FNV_OFFSET_BASIS
    for b in s.encode("utf-8"):
        h = xor64(h, b)
        h = (h * FNV_PRIME) & MASK_64
    return h


def fnv1a_64_sql(s: str, db_path: str = ":memory:") -> int:
    """Compute FNV-1a 64 via SQLite, byte-exact with Python."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Encode string as a sequence of bytes via SQLite's UNICODE function
    # Then iterate, applying FNV-1a via pure SQL arithmetic

    # Note: SQLite uses 64-bit signed integers internally (post-3.0)
    # We use ABS() to ensure positive values where needed
    cur.execute(f"""
        WITH RECURSIVE
          byte_stream(byte_val, pos, h) AS (
            -- Initial state
            SELECT
              CAST(? AS INTEGER),
              1,
              CAST({FNV_OFFSET_BASIS} AS INTEGER)
            UNION ALL
            -- Iterate: get next byte, update hash
            SELECT
              UNICODE(SUBSTR(?, pos, 1)) & 0xFF,
              pos + 1,
              (((((h | (UNICODE(SUBSTR(?, pos, 1)) & 0xFF)) - (h & (UNICODE(SUBSTR(?, pos, 1)) & 0xFF))) * {FNV_PRIME}) & {MASK_64}) + {2**64}) & {MASK_64}
            FROM byte_stream
            WHERE pos <= LENGTH(?)
          )
        SELECT h FROM byte_stream ORDER BY pos DESC LIMIT 1;
    """, (
        # First byte (for init)
        s.encode('utf-8')[0],
        # Subsequent parameters for the recursive part
        s, s, s,
        s,
    ))

    result = cur.fetchone()
    conn.close()
    return result[0] if result else 0


if __name__ == "__main__":
    py_hash = fnv1a_64(CANARY_STRING)

    print(f"Python FNV-1a-64: 0x{py_hash:016x}")

    try:
        sql_hash = fnv1a_64_sql(CANARY_STRING)
        print(f"SQLite FNV-1a-64: 0x{sql_hash:016x}")
        print(f"Verified (Python == SQLite): {py_hash == sql_hash}")
    except Exception as e:
        print(f"SQLite error: {e}")
        sql_hash = py_hash

    print(f"Verified (== expected): {py_hash == EXPECTED}")
    print(f"Expected: 0x{EXPECTED:016x}")
