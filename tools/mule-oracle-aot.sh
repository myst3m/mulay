#!/usr/bin/env bash
# アプリのシナリオを、mulay build で作った実行ファイル (DataWeave を事前コンパイルしたもの) で回す (docs/aot.md)。
# アプリごとに target/aot-apps/<app> (アプリを埋め込んだ実行ファイル) を作り、mule-oracle mulay で回す。
# 引数はアプリ名 (省略で全部)。
set -u
cd "$(dirname "$0")/.."
clay build src/mulay/cli/main.clay -o target/mulay >&2 || exit 1
mkdir -p target/aot-apps
apps=("$@")
if [ ${#apps[@]} -eq 0 ]; then
  for d in test/fixtures/apps/*/; do [ -f "$d/scenario.scn" ] && apps+=("$(basename "$d")"); done
fi
pass=0; total=0; failed=()
for a in "${apps[@]}"; do
  bin="target/aot-apps/$a"
  if ! target/mulay build "test/fixtures/apps/$a" -o "$bin" > "target/aot-apps/$a.log" 2>&1; then
    echo "BUILD FAIL $a (target/aot-apps/$a.log)"; failed+=("$a"); continue
  fi
  # mule-oracle は "<bin> run <app>" で起動する。埋め込み型の実行ファイルはアプリのパスを取らないので、
  # 引数を捨てて起動するラッパーを挟む
  printf '#!/bin/sh\nexec "%s"\n' "$PWD/$bin" > "$bin.sh"; chmod +x "$bin.sh"
  line=$(MULAY_BIN="$PWD/$bin.sh" tools/mule-oracle/mule-oracle mulay "$a" 2>&1 | tail -1)
  echo "$a: $line"
  p=$(echo "$line" | sed -n 's/.*mulay: \([0-9]*\)\/\([0-9]*\).*/\1/p'); t=$(echo "$line" | sed -n 's/.*mulay: \([0-9]*\)\/\([0-9]*\).*/\2/p')
  pass=$((pass + ${p:-0})); total=$((total + ${t:-0}))
done
echo "aot: $pass/$total request(s) passed${failed:+, build failed: ${failed[*]}}"
