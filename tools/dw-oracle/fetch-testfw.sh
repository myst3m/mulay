#!/usr/bin/env bash
# dw::test (DataWeave Testing Framework) の jar を target/dw-testfw に取ってくる。dw-oracle で dw::test の golden を作る時に使う:
#   DW_ORACLE_EXTRA_CP="$(tools/dw-oracle/fetch-testfw.sh)" tools/dw-oracle/dw-oracle fill test/fixtures/dw/dwtest/x.dwt
# 版は実 Mule 4.11.3 の DW (2.11.0-20251202) にそろえる。jar はリポジトリに入れない (ライセンスの記載が無い)。
set -eu
V=2.11.0-20251202
R=https://repository.mulesoft.org/nexus/content/repositories/releases/org/mule/weave
root="$(cd "$(dirname "$0")/../.." && pwd)"
d="$root/target/dw-testfw"
mkdir -p "$d"
get() { [ -s "$d/$2" ] || curl -fsS -o "$d/$2" "$R/$1/$V/$1-$V.jar"; }
get data-weave-testing-framework fw.jar
get assertions assertions.jar
get file-module file-module.jar
echo "$d/fw.jar:$d/assertions.jar:$d/file-module.jar"
