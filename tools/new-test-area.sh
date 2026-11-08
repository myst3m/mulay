#!/usr/bin/env bash
# test/<area>/ を作り、src/mulay への symlink を張る。
set -eu
cd "$(dirname "$0")/.."
mkdir -p "test/$1"
[ -e "test/$1/mulay" ] || ln -s ../../src/mulay "test/$1/mulay"
