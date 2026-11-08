#!/usr/bin/env bash
# mulay.lib.dec と Java 17 の BigDecimal の同じ計算を 1 コアで 100 万回ずつ測る。使い方: tools/dec-bench/run.sh
set -eu
cd "$(dirname "$0")/../.."
B=target/dec-bench
mkdir -p "$B"
ln -sfn "$PWD/src/mulay" "$B/mulay"
cp tools/dec-bench/bench.clay "$B/bench.clay"
taskset -c 0-3 clay build "$B/bench.clay" -o "$B/bench" 2>&1 | grep -v '^clay: \(chunks\|built\|needs\)' >&2 || true
echo "== mulay.lib.dec (3 回目)"
taskset -c 0 "$B/bench"
echo "== java.math.BigDecimal (Java 17, 6 回目)"
taskset -c 0 /usr/lib/jvm/java-17-openjdk-amd64/bin/java -XX:ActiveProcessorCount=1 tools/dec-bench/DecBench.java
