#!/usr/bin/env bash
# DataWeave の golden 全件を mulay で回す。引数はそのまま dwt に渡す (-v -e)。
# 例: tools/dwt-all.sh -e      tools/dwt-all.sh -v docs/strings  (末尾の引数はフィクスチャの部分パスで絞り込む)
set -eu
cd "$(dirname "$0")/.."
# ソースが新しければ作り直す (古い target/dwt で回すと変更を試したことにならない)
if [ ! -x target/dwt ] || [ -n "$(find src -name '*.clay' -newer target/dwt -print -quit)" ]; then
  clay build src/mulay/cli/dwt.clay -o target/dwt >&2 || exit 1
fi
flags=(); filt=""
for a in "$@"; do case "$a" in -*) flags+=("$a");; *) filt="$a";; esac; done
lst="$(mktemp)"; trap 'rm -f "$lst"' EXIT
find test/fixtures/dw -name '*.dwt' | sort | grep -- "$filt" > "$lst" || true
target/dwt "${flags[@]}" "@$lst"
