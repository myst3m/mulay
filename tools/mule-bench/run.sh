#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
cd "$repo"
data=${BENCH_DATA:-$repo/target/bigtest/bench}
out=$repo/target/mule-bench
cpus=${BENCH_CPUS:-0-3}
taskset -cp "$cpus" $$ > /dev/null
mulay=${BENCH_MULAY:-$repo/target/mulay}
tag=${BENCH_TAG:-}
which=${1:-both}; shift || true
mkdir -p "$out"
mo_flags=
unit=
[ -f "$data/orders.json" ] || python3 "$here/gen-input.py" "$data" "${BENCH_ROWS:-1000000}" "${BENCH_COPY_MB:-1024}"
wait_port() { for _ in $(seq 1 1200); do curl -sf -o /dev/null "http://127.0.0.1:18590/ping" && return 0; sleep 0.25; done; return 1; }
cgroup() { local g; g=$(systemctl --user show -p ControlGroup --value "$1"); [ -n "$g" ] || { echo "no cgroup for $1" >&2; return 1; }; echo "${g#/}"; }
stop_unit() {
  [ -n "$unit" ] || return 0
  systemctl --user kill -s INT "$unit" 2>/dev/null || true
  for _ in $(seq 1 120); do systemctl --user is-active -q "$unit" || break; sleep 0.25; done
  systemctl --user stop "$unit" 2>/dev/null || true
  unit=
}
trap stop_unit EXIT
start() {
  if curl -sf -o /dev/null "http://127.0.0.1:18590/ping"; then echo "port 18590 is already in use" >&2; return 1; fi
  unit=mbench-$1-$2-$$.scope
  shift 2
  systemd-run --user --scope -q --unit="${unit%.scope}" taskset -c "$cpus" "$@" &
  wait_port
}

run_mulay() {
  mkdir -p "$out/mulay"
  start mulay "$1" "$mulay" run "$here/app" > "$out/mulay.log" 2>&1
  local pid
  pid=$(head -1 "/sys/fs/cgroup/$(cgroup "$unit")/cgroup.procs")
  python3 "$here/bench.py" "$pid" "$(cgroup "$unit")" 18590 "$data" "$out/mulay" "mulay$tag" "$1" > "$out/mulay$tag-$1.json"
  stop_unit
}

run_mule() {
  mkdir -p "$out/mule"
  start mule "$1" python3 tools/mule-oracle/mule-oracle run $mo_flags "$here/app" > "$out/mule.log" 2>&1
  mo_flags=--no-build
  local jpid=""
  for p in $(cat "/sys/fs/cgroup/$(cgroup "$unit")/cgroup.procs"); do
    [ "$(cat /proc/$p/comm 2>/dev/null)" = java ] && jpid=$p
  done
  [ -n "$jpid" ] || { echo "no Mule java process" >&2; return 1; }
  python3 "$here/bench.py" "$jpid" "$(cgroup "$unit")" 18590 "$data" "$out/mule" mule "$1" > "$out/mule-$1.json"
  stop_unit
}

cases=("$@"); [ ${#cases[@]} -gt 0 ] || cases=(copy csv2json json2xml xml2json json-filter json-agg)
for c in "${cases[@]}"; do
  case $which in
    mulay) run_mulay "$c" ;;
    mule) run_mule "$c" ;;
    both) run_mule "$c"; run_mulay "$c" ;;
  esac
done
