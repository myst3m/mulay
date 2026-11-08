#!/usr/bin/env bash
# mulay.wasm を組めるか、組んだ物が Node で動くかを確かめる (wasm でだけ組む target-when の分岐の誤りを見つけるため)。
# clay の main が要る (入れてある clay では wasm を組めない)。CLAY_ROOT か ~/projects/clay から clone して CLI を組み、
# target/clay-main/<HEAD> に置いて使い回す。出力: target/mulay-check.wasm
set -eu
cd "$(dirname "$0")/../.."
src="${CLAY_ROOT:-$HOME/projects/clay}"
[ -d "$src/.git" ] || { echo "wasm check: skipped (no clay tree at $src; set CLAY_ROOT)"; exit 0; }
head=$(git -C "$src" rev-parse --short HEAD)
tree="target/clay-main/$head"
if [ ! -x "$tree/clay" ]; then
  rm -rf "${tree:?}.tmp"
  git clone -q "$src" "$tree.tmp"
  (cd "$tree.tmp" && bash build.sh src/cli/main.clay -o clay >/dev/null 2>&1)
  rm -rf "${tree:?}"; mv "$tree.tmp" "$tree"
  for old in target/clay-main/*; do [ "$old" = "$tree" ] || rm -rf "${old:?}"; done
fi
out="$(pwd)/target/mulay-check.wasm"
log="$(pwd)/target/mulay-check.log"
if ! CLAY_ROOT="$(pwd)/$tree" CLAY="$(pwd)/$tree/clay" tools/wasm/build.sh "$out" >"$log" 2>&1; then
  grep -E "error" "$log" | head -20
  echo "wasm check: build failed (log: $log)"
  exit 1
fi
node tools/wasm/host_test.mjs "$out"
