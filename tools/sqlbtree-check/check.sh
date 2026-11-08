#!/bin/sh
# 純 Clay の B-tree が書いた DB を sqlite3 (Python) で確かめる: PRAGMA integrity_check (索引と表の一致、freelist、ページの形) と、
# 中身 (gen.clay と同じ規則で作った行が、消した分を除いて全部あるか)。使い方: tools/sqlbtree-check/check.sh
set -e
here=$(cd "$(dirname "$0")" && pwd)
work=$(mktemp -d "${TMPDIR:-/tmp}/sqlbtree-check.XXXXXX")
trap 'rm -rf "$work"' EXIT
ln -s "$here/../../src/mulay" "$work/mulay"
cp "$here/gen.clay" "$work/gen.clay"
(cd "$work" && clay build gen.clay -o gen >/dev/null 2>&1 && ./gen "$work") > "$work/list"
python3 -I - "$work/list" <<'PY'
import sqlite3, sys
ok = True
for line in open(sys.argv[1]):
    path, ps, n, dl, size = line.split()
    c = sqlite3.connect(path)
    ic = c.execute("PRAGMA integrity_check").fetchall()
    rows = c.execute("SELECT count(*), sum(b), count(DISTINCT a) FROM t").fetchone()
    bad = c.execute("SELECT count(*) FROM t WHERE a <> substr(a, 1, length(a))").fetchone()[0]
    viaidx = c.execute("SELECT count(*) FROM t INDEXED BY i WHERE a >= ''").fetchone()[0]
    good = ic == [("ok",)] and viaidx == rows[0] and bad == 0
    ok = ok and good
    print(("ok  " if good else "BAD ") + "page %s rows %s integrity %s via-index %s" % (ps, rows[0], ic[:3], viaidx))
sys.exit(0 if ok else 1)
PY
