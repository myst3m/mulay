#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../../.." && pwd)
bin=${1:?mulay binary}; label=${2:?label}; rounds=${3:-12}; idle=${SOAK_IDLE:-12}; cpus=${SOAK_CPUS:-0-3}
db=${SOAK_DB:-$repo/target/bigtest/soak.db}
out=$repo/target/mule-bench/soak-$label.log
mkdir -p "$(dirname "$db")" "$(dirname "$out")"
[ -f "$db" ] || python3 - "$db" <<'PY'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1]); c.execute("create table t (id integer primary key, name text, v real)")
c.executemany("insert into t values (?,?,?)", ((i, "name-%d" % i, i * 1.5) for i in range(1, 1000001))); c.commit()
PY
if curl -s -o /dev/null "localhost:18196/small"; then echo "port 18196 is already in use" >&2; exit 1; fi
taskset -cp "$cpus" $$ > /dev/null
taskset -c "$cpus" "$bin" run "$here/app" -l WARN "soak.db=$db" > "$out.run" 2>&1 &
pid=$!
trap 'kill -INT $pid 2>/dev/null; wait $pid 2>/dev/null || true' EXIT
for _ in $(seq 100); do curl -s -o /dev/null "localhost:18196/small" && break; sleep 0.2; done
t() { curl -s -o /dev/null -w '%{time_total}' "localhost:18196/$1"; }
rss() { awk '/VmRSS/ {printf "%dMB", $2/1024}' "/proc/$pid/status"; }
p50() { sort -n | awk '{a[NR]=$1} END {printf "%.2fms", a[int((NR+1)/2)]*1000}'; }
: > "$out"
echo "base rss=$(rss)" | tee -a "$out"
for r in $(seq "$rounds"); do
  line="round $r:"
  for p in g1 sum gen fe; do line="$line $p=$(t $p | cut -c1-5)"; done
  line="$line small p50=$(for _ in $(seq 50); do t small; echo; done | p50) rss=$(rss)"
  sleep "$idle"
  line="$line idle${idle}s=$(rss)"
  t small > /dev/null
  echo "$line after-small=$(rss)" | tee -a "$out"
done
