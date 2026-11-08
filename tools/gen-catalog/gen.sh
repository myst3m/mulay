#!/usr/bin/env bash
# src/mulay/conn/catalog_gen.clay を conn/registry から作り直す (wasm の入口がコネクタを持たずに使う表)。
set -eu
cd "$(dirname "$0")"
out=$(mktemp -d)
trap 'rm -rf "${out:?}"' EXIT
clay build gencat/main.clay -o "$out/gencat" >/dev/null
"$out/gencat" > ../../src/mulay/conn/catalog_gen.clay
