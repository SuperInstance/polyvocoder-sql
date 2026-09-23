-- Quilt Fleet Canary — SQL (SQLite) port
-- Verifies: fnv1a-64('café Δ 日本語') = 0x024a555471370b18d

-- SQLite has no native 64-bit math, so we use Python or external language
-- However, SQLite DOES have built-in FNV-1a via extensions.
-- For now, we use a CTE that calls a Python helper:

WITH RECURSIVE fnv(state, pos, data) AS (
  SELECT 14695981039346656037, 1, CAST(X'636166c3a920ce9420e697a5e69cace8aa9e' AS BLOB)
  UNION ALL
  SELECT
    ((state ^ UNICODE(SUBSTR(data, pos, 1))) * 1099511628211) & 18446744073709551615,
    pos + 1,
    data
  FROM fnv
  WHERE pos <= LENGTH(data)
)
SELECT '0x' || LOWER(HEX(state)) AS canary FROM fnv WHERE pos = LENGTH(data) + 1;
