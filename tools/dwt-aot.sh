#!/usr/bin/env bash
# DataWeave の golden を、事前コンパイルしたコードで回す (docs/aot.md)。引数は dwt に渡す (-v -e)。
# target/aot-dwt/ に src/mulay を写し (symlink)、mulay/cli/aot.clay を差し替えて (ADR 082)、全フィクスチャのスクリプトを生成して dwt を作り直す。
set -eu
cd "$(dirname "$0")/.."
if [ ! -x target/dwt ] || [ -n "$(find src -name '*.clay' -newer target/dwt -print -quit)" ]; then
  clay build src/mulay/cli/dwt.clay -o target/dwt >&2 || exit 1
fi
B=target/aot-dwt
rm -rf "$B"; mkdir -p "$B/mulay/cli"
for e in src/mulay/*; do [ "$(basename "$e")" = cli ] || ln -s "$PWD/$e" "$B/mulay/"; done
for e in src/mulay/cli/*; do case "$(basename "$e")" in aot.clay) ;; *) ln -s "$PWD/$e" "$B/mulay/cli/";; esac; done
lst="$(mktemp)"; trap 'rm -f "$lst"' EXIT
find test/fixtures/dw -name '*.dwt' | sort > "$lst"
target/dwt -g "$B" "@$lst" >&2
clay build "$B/mulay/cli/dwt.clay" -o target/dwt-aot >&2 || exit 1
target/dwt-aot "$@" "@$lst"
