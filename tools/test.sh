#!/usr/bin/env bash
# すべての test/<area>/ を clay test で回す。引数を渡すとその area だけ。
# 各 area には src/mulay への symlink (test/<area>/mulay) が要る (tools/new-test-area.sh)。
set -u
cd "$(dirname "$0")/.."
areas=("$@")
if [ ${#areas[@]} -eq 0 ]; then
  for d in test/*/; do areas+=("$(basename "$d")"); done
fi
fail=0
for a in "${areas[@]}"; do
  [ -d "test/$a" ] || { echo "no area: $a"; fail=1; continue; }
  ls test/"$a"/*.clay >/dev/null 2>&1 || continue
  echo "== $a"
  clay test "test/$a" || fail=1
done
# 実装済みなのに「読まない属性」の表 (src/mulay/mule/ignored.clay) に残っているものが無いか (全 area のときだけ)
if [ $# -eq 0 ]; then
  echo "== ignored-attrs"
  python3 tools/ignored-attrs.py check || fail=1
  # mulay が持つ DataWeave のモジュール (tools/dwl) と、それを埋め込んだ src/mulay/dw/stdmods.clay がずれていないか
  echo "== dwl-modules"
  python3 tools/gen-dwl-modules.py | cmp -s - src/mulay/dw/stdmods.clay || { echo "src/mulay/dw/stdmods.clay is stale: python3 tools/gen-dwl-modules.py > src/mulay/dw/stdmods.clay"; fail=1; }
  # wasm でだけ組む分岐の誤りを見つける (tools/wasm/check.sh、clay main の木が要る)。MULAY_SKIP_WASM=1 で飛ばす
  if [ "${MULAY_SKIP_WASM:-}" != "1" ]; then
    echo "== wasm"
    tools/wasm/check.sh || fail=1
  fi
fi
exit $fail
