#!/usr/bin/env bash
# DW の速さを実 DW (JIT 後) と mulay (閉包と事前コンパイル) で比べる。使い方: tools/dw-bench/run.sh [件名の絞り込み] (docs/perf.md)
# 実 DW の結果は target/dw-bench/real-<件名>.txt に残し、BENCH_REAL=1 か件の更新で測り直す
set -eu
cd "$(dirname "$0")/../.."
taskset -cp "${BENCH_CPUS:-0-3}" $$ > /dev/null
MULE_HOME="${MULE_HOME:-$HOME/srv/mule-enterprise-standalone-4.11.3}"
J=/usr/lib/jvm/java-17-openjdk-amd64/bin
B=target/dw-bench
N="${BENCH_RUNS:-10}"
mkdir -p "$B/cases"
[ -f "$B/input.json" ] || python3 tools/dw-bench/gen-input.py 100000 > "$B/input.json"
cp="$(ls "$MULE_HOME"/services/mule-service-weave-ee-*/lib/*.jar "$MULE_HOME"/lib/mule/*dwb*.jar | tr '\n' ':')"
if [ ! -f "$B/DwBench.class" ] || [ tools/dw-bench/DwBench.java -nt "$B/DwBench.class" ]; then
  "$J/javac" -nowarn -cp "$cp" -d "$B" tools/dw-bench/DwBench.java
fi
cases=$(ls tools/dw-bench/cases/*.dwt | grep -- "${1:-}" || true)
for c in $cases; do
  n=$(basename "$c" .dwt)
  if grep -q payload "$c"; then { cat "$c"; echo "%%% input payload application/json"; cat "$B/input.json"; echo; } > "$B/cases/$n.dwt"; else cp "$c" "$B/cases/$n.dwt"; fi
done
if [ ! -x target/dwt ] || [ -n "$(find src -name '*.clay' -newer target/dwt -print -quit)" ]; then clay build src/mulay/cli/dwt.clay -o target/dwt >&2; fi
A="$B/aot"; rm -rf "$A"; mkdir -p "$A/mulay/cli"
for e in src/mulay/*; do [ "$(basename "$e")" = cli ] || ln -s "$PWD/$e" "$A/mulay/"; done
for e in src/mulay/cli/*; do case "$(basename "$e")" in aot.clay) ;; *) ln -s "$PWD/$e" "$A/mulay/cli/";; esac; done
target/dwt -g "$A" $(for c in $cases; do echo "$B/cases/$(basename "$c")"; done) >&2
clay build "$A/mulay/cli/dwt.clay" -o "$B/dwt-aot" >&2
printf '%-16s %12s %12s %12s\n' case real-DW mulay-clos mulay-aot
for c in $cases; do
  n=$(basename "$c" .dwt)
  inp=""; grep -q payload "$c" && inp="$B/input.json"
  rf="$B/real-$n.txt"
  if [ ! -s "$rf" ] || [ -n "${BENCH_REAL:-}" ] || [ "$c" -nt "$rf" ]; then
    "$J/java" -cp "$cp:$B" DwBench "$c" "$inp" "$N" | sed -n 's/bench median \([0-9]*\) ms.*/\1/p' > "$rf"
  fi
  r=$(cat "$rf")
  m=$(target/dwt -r 5 "$B/cases/$n.dwt" | sed -n 's/bench median \([0-9]*\) ms.*/\1/p')
  x=$("$B/dwt-aot" -r 5 "$B/cases/$n.dwt" | sed -n 's/bench median \([0-9]*\) ms.*/\1/p')
  printf '%-16s %10s ms %10s ms %10s ms\n' "$n" "$r" "$m" "$x"
done
