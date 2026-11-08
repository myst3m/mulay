#!/usr/bin/env bash
# 確認一式。全体を GATE_CPUS (既定 0-3) の 4 つの CPU に固定する (このマシンは他のエージェントと分け合う)。
#   tools/gate.sh [--full] [--wasm] [--bench [件...]]
# ビルド → DW の golden (通常・遅延・AOT) → 全アプリの照合 (mule-oracle mulay -j 4 --lazy-local) と単体のテスト
# (nice で優先度を下げる。照合はほとんど待っているので、空いた CPU を単体が使う) を同時に → MUnit と OpenTelemetry の
# トレースの照合 (tools/otlp/trace-oracle check) を同時に。
# 遅延の照合 (MULAY_DW_LAZY_ALL=1) は、外のサービス (Salesforce・Anypoint MQ・DB・SFTP) を使わないアプリだけ回す。--full は全アプリ
# (外のサービスのアプリは 1 列で順に回すので、Salesforce の列だけで 6 分ほど延びる)。
# --wasm は wasm の確認と作り直し (livenote に渡す時)、--bench は最後に単独でベンチ (件を省くと 6 件)。
# 段ごとの出力は target/gate/<段>.log (照合は落ちた要求の差分も残す)。段ごとの結果と時間を出し、どれかが落ちれば 1 で終わる。
# 照合が落ちた回の oracle.log は target/gate/failed/oracle-<日時>.log に写して残す (新しい 20 個まで。ときどきしか落ちないものを後で調べるため)。
set -uo pipefail
cd "$(dirname "$0")/.."
cpus=${GATE_CPUS:-0-3}
taskset -cp "$cpus" $$ > /dev/null
export CLAY_TEST_JOBS=${CLAY_TEST_JOBS:-4}
out=target/gate
mkdir -p "$out"
wasm=0; bench=0; lazy=--lazy-local; cases=()
while [ $# -gt 0 ]; do
  case $1 in
    --full) lazy=--lazy ;;
    --wasm) wasm=1 ;;
    --bench) bench=1 ;;
    *) if [ $bench = 1 ]; then cases+=("$1"); else echo "gate: unknown argument: $1" >&2; exit 2; fi ;;
  esac
  shift
done
bin=$PWD/$out/mulay
fail=0
t_all=$(date +%s)
secs() { echo "$(( $(date +%s) - $1 ))s"; }
report() { printf '%-9s %-64s %s\n' "$1" "$2" "$3"; }

cv=$(clay --version)
if [ "$(cat "$out/clay-version" 2>/dev/null)" != "$cv" ]; then
  rm -f target/dwt target/dwt-aot
  echo "$cv" > "$out/clay-version"
fi

s=$(date +%s)
if ! clay build src/mulay/cli/main.clay -o "$bin" > "$out/build.log" 2>&1; then
  report build "FAILED ($out/build.log)" "$(secs "$s")"; exit 1
fi
report build "ok ($(grep -c 'warning' "$out/build.log") warnings)" "$(secs "$s")"

dwt() {
  local name=$1 s line; shift
  s=$(date +%s)
  "$@" > "$out/$name.log" 2>&1
  line=$(grep -E '^dwt:' "$out/$name.log" | tail -1)
  case $line in *" 0 fail,"*) ;; *) fail=1 ;; esac
  report "$name" "${line:-no result ($out/$name.log)}" "$(secs "$s")"
}
dwt dwt tools/dwt-all.sh
dwt dwt-lazy env MULAY_DW_LAZY_ALL=1 tools/dwt-all.sh
dwt aot tools/dwt-aot.sh

s_or=$(date +%s)
MULAY_BIN=$bin tools/mule-oracle/mule-oracle mulay -v -j 4 $lazy > "$out/oracle.log" 2>&1 &
or_pid=$!
s=$(date +%s)
nice -n 10 tools/test.sh > "$out/unit.log" 2>&1
urc=$?
if [ $urc = 0 ]; then report unit "ok" "$(secs "$s")"
else fail=1; report unit "FAILED ($out/unit.log)" "$(secs "$s")"; grep -E 'BROKEN|[1-9][0-9]* failing|FAIL|^clay: .*: error: ' "$out/unit.log" | head -10; fi
wait $or_pid
orc=$?
if [ $orc != 0 ]; then
  fail=1
  mkdir -p "$out/failed"
  kept="$out/failed/oracle-$(date +%Y%m%d-%H%M%S).log"
  cp "$out/oracle.log" "$kept"
  ls -1t "$out"/failed/oracle-*.log | tail -n +21 | xargs -r rm -f
  echo "oracle: kept $kept"
fi
grep -E '^mulay( lazy)?:' "$out/oracle.log" | while read -r line; do report oracle "$line" "$(secs "$s_or")"; done
grep -E '^FAIL' "$out/oracle.log" | head -20

s_tr=$(date +%s)
MULAY_BIN=$bin tools/otlp/trace-oracle check -v > "$out/trace.log" 2>&1 &
tr_pid=$!
s=$(date +%s)
MULAY_BIN=$bin tools/munit-oracle/munit-oracle mulay > "$out/munit.log" 2>&1 || fail=1
report munit "$(tail -1 "$out/munit.log")" "$(secs "$s")"
wait $tr_pid || fail=1
report trace "$(grep -c '^PASS' "$out/trace.log") pass, $(grep -c '^FAIL' "$out/trace.log") fail" "$(secs "$s_tr")"

if [ $wasm = 1 ]; then
  s=$(date +%s)
  if tools/wasm/check.sh > "$out/wasm.log" 2>&1; then
    t=$(ls -d target/clay-main/*/ | head -1)
    if CLAY_ROOT=$PWD/$t CLAY=$PWD/$t/clay tools/wasm/build.sh "$PWD/target/mulay.wasm" >> "$out/wasm.log" 2>&1; then
      report wasm "ok, sha256 $(sha256sum target/mulay.wasm | cut -c1-16) (clay ${t#target/clay-main/})" "$(secs "$s")"
    else fail=1; report wasm "build FAILED ($out/wasm.log)" "$(secs "$s")"; fi
  else fail=1; report wasm "check FAILED ($out/wasm.log)" "$(secs "$s")"; fi
fi

if [ $bench = 1 ]; then
  s=$(date +%s)
  BENCH_CPUS=$cpus BENCH_MULAY=$bin tools/mule-bench/run.sh mulay "${cases[@]}" > "$out/bench.log" 2>&1 || fail=1
  grep -E '^mulay' "$out/bench.log"
  report bench "$out/bench.log" "$(secs "$s")"
fi

report total "$([ $fail = 0 ] && echo ok || echo FAILED)" "$(secs "$t_all")"
exit $fail
