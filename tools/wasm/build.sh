#!/usr/bin/env bash
# mulay.wasm (livenote の実行エンジン) を作る。wasm の link の設定 (clay ADR 121) と asin などの組み込み (ADR 125) が要るので、
# clay の main を CLAY_ROOT に渡す (例: clay を clone して build.sh で CLI を組んだもの)。
# 使い方: CLAY_ROOT=<clay の木> CLAY=<その CLI> tools/wasm/build.sh <出力.wasm>
# 組めたら <出力.wasm>.clay-version に、組んだ clay の版 (`clay --version` の 1 行目) を書く (Müdrover の写しの手順が見る)。
set -eu
: "${CLAY_ROOT:?CLAY_ROOT must point to a clay tree with ADR 121-125}"
CLAY="${CLAY:-$CLAY_ROOT/clay}"
out="$(realpath -m "${1:?usage: build.sh <out.wasm>}")"
cd "$(dirname "$0")/../../src"
CLAY_ROOT="$CLAY_ROOT" "$CLAY" build mulay/wasm/main.clay -o "$out"
"$CLAY" --version | head -1 > "$out.clay-version"
