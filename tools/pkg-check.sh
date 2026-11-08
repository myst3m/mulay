#!/usr/bin/env bash
set -euo pipefail

repo=$(cd "$(dirname "$0")/.." && pwd)
tpl=$repo/templates/connector
pkgs=${CLAY_CACHE:-$HOME/.cache/clay-cache}/pkgs
port=${PKG_CHECK_PORT:-18391}
c=$(git -C "$repo" rev-parse HEAD)

if [ -n "$(git -C "$repo" status --porcelain -- src templates)" ]; then
  echo "pkg-check: src or templates has uncommitted changes; this checks the commit ${c:0:12}, not the working tree" >&2
fi

had_c=0; [ -d "$pkgs/$c" ] && had_c=1
w=$(mktemp -d "${TMPDIR:-/tmp}/pkg-check.XXXXXX")
pid=""; t=""
cleanup() {
  [ -n "$pid" ] && kill "$pid" 2>/dev/null && wait "$pid" 2>/dev/null || true
  [ -n "$t" ] && rm -rf "${pkgs:?}/$t"
  [ "$had_c" = 0 ] && rm -rf "${pkgs:?}/$c"
  rm -rf "$w"
}
trap cleanup EXIT

mkdir -p "$w/toy" "$w/dist"
cp -r "$tpl/toy/." "$w/toy/"
printf 'name: toyconn\ngit: file://%s %s\n' "$repo" "$c" > "$w/toy/clay.pkg"
git -C "$w/toy" init -q
git -C "$w/toy" add -A
git -C "$w/toy" -c user.email=pkg-check@localhost -c user.name=pkg-check commit -qm toy
t=$(git -C "$w/toy" rev-parse HEAD)

cp "$tpl/dist/"*.clay "$w/dist/"
printf 'name: dist\ngit: file://%s %s\ngit: file://%s/toy %s\n' "$repo" "$c" "$w" "$t" > "$w/dist/clay.pkg"
clay build "$w/dist" -o "$w/dist/mulay-toy" >"$w/build.log" 2>&1 || { cat "$w/build.log" >&2; echo "pkg-check: FAIL (build)" >&2; exit 1; }

cp -r "$tpl/app" "$w/app"
sed -i "s/port=\"18391\"/port=\"$port\"/" "$w/app/src/main/mule/app.xml"

serve_check() {
  local what=$1; shift
  "$@" >"$w/run.log" 2>&1 &
  pid=$!
  for _ in $(seq 100); do curl -s -o /dev/null "http://127.0.0.1:$port/" && break; sleep 0.1; done
  local got
  got=$(curl -s "http://127.0.0.1:$port/shout?w=hello" || true)
  if [ "$got" != "hello!" ]; then
    cat "$w/run.log" >&2
    echo "pkg-check: FAIL ($what: expected 'hello!', got '$got')" >&2
    exit 1
  fi
  got=$(curl -s "http://127.0.0.1:$port/ping" || true)
  if [ "$got" != "pong /ping" ]; then
    cat "$w/run.log" >&2
    echo "pkg-check: FAIL ($what: expected 'pong /ping' from the toy mount, got '$got')" >&2
    exit 1
  fi
  kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null || true
  pid=""
}

serve_check run "$w/dist/mulay-toy" run "$w/app"

"$w/dist/mulay-toy" build "$w/app" -o "$w/dist/toy-app" >"$w/build2.log" 2>&1 || { cat "$w/build2.log" >&2; echo "pkg-check: FAIL (mulay-toy build)" >&2; exit 1; }
[ ! -e "$w/dist/toy-app.build" ] || { echo "pkg-check: FAIL (mulay build left $w/dist/toy-app.build, which holds the embedded properties)" >&2; exit 1; }
v=$("$w/dist/toy-app" version)
case "$v" in
  *" precompiled DataWeave script(s))") ;;
  *) echo "pkg-check: FAIL (the built executable has no precompiled DataWeave: '$v')" >&2; exit 1;;
esac
serve_check build "$w/dist/toy-app"

echo "pkg-check: PASS (mulay ${c:0:12} + toy connector via git:, operation and mount, run and build)"
