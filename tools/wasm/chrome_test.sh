#!/usr/bin/env bash
# host.mjs の JSPI の道を、headless の Chrome で試す。使い方: tools/wasm/chrome_test.sh <mulay.wasm>
set -eu
wasm="$(realpath "${1:?usage: chrome_test.sh <mulay.wasm>}")"
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'kill "$srv" 2>/dev/null || true; rm -rf "${work:?}"' EXIT
cp "$wasm" "$work/mulay.wasm"; cp "$here/host.mjs" "$here/chrome_test.html" "$work/"
echo '{"name":"A"}' > "$work/data.json"
port=$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')
(cd "$work" && exec python3 -m http.server "$port" --bind 127.0.0.1 >/dev/null 2>&1) & srv=$!
sleep 1
out=$(timeout 90 google-chrome --headless=new --disable-gpu --no-sandbox --user-data-dir="$work/profile" --virtual-time-budget=600000 \
      --dump-dom "http://127.0.0.1:$port/chrome_test.html" 2>/dev/null | sed -n '/<pre id="out">/,/<\/pre>/p' | sed 's/<[^>]*>//g')
echo "$out"
echo "$out" | grep -q '^PASSED$'
