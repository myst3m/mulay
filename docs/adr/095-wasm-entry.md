# 095 — wasm の入口 (mulay.wasm.main) と、wasm で組めない所の分け方

状態: **採用** (2026-10-24)

## 背景

ライブ・ノート (WebIDE) は mulay を wasm32 にしてブラウザの Worker で動かす (取り決めは livenote の `Runtime`:
`load`・`run`・`getValue`・`components`)。中身の実行は ADR 094 (`mulay.note.run`)、OS の口は ADR 093 (`lib/host`)。

## 決定

- **入口は `mulay.wasm.main`**。`^:export` の `load`・`run`・`get_value`・`components` (clay は `-` を `_` にして export する)。
  引数と戻り値は Str (clay ADR 094 の作法: 引数は (ptr, len)、戻り値は最後の引数 out に番地を書き長さを返す)。
  - `load` の引数は「パス \n バイト数 \n 中身」を並べたもの (JSON の escape を避けるため)。パスはプロジェクトからの相対で、
    `/app/` の下に `lib/host/mount!` で置き、`note/load-dir "/app"` で読む。戻りは AppModel の JSON。テキストのファイルだけを
    前提にする (JS 側で UTF-8 の文字列にして渡すので、JAR などのバイナリは壊れる)。
  - 予約したパス `@properties` (2026-10-24、livenote の接続のプロファイルのため) は、ファイルとして置かずにシステムプロパティ
    (Mule の `-D`、CLI の `key=value` と同じ表) として読む。中身は平らな JSON の object で、値は文字列 (数と真偽は文字にする、
    null は無視、object と配列はエラー)。global-property と configuration-properties より強い。`${secure::x}` には
    キー `secure::x` で値を渡す (秘密を wasm の中のファイルに書かないため)。環境変数は wasm では使わない。
    形が違えば `{"error": ..}` を返す。
  - `scaffold` は APIkit の雛形の編集の一覧 (ADR 097)。`call` はほかのインスタンスからの HTTP の呼び出し (ADR 098)。
  - host の import に `env.mulay_http` (ADR 098) が加わった。つながないなら長さ 0 の文字列を返す。
  - `run` は Example の JSON、`get_value` は値の ID、`components` は要素名を改行で並べたもの。
- **組み方**: `tools/wasm/build.sh` (clay の main を `CLAY_ROOT` に渡す。wasm の link の設定 = clay ADR 121、asin などの組み込み
  = clay ADR 125 が要る)。Node で試すのは `tools/wasm/run.mjs <wasm> <プロジェクト>` (host の import は clay の手本どおり)。
  `tools/wasm/check.sh` (2026-10-24) は clay main を `target/clay-main/<HEAD>` に組んで使い回し、mulay.wasm を組んで
  host_test を流す。`tools/test.sh` (全部の area のとき) の最後に回る (clay の木が無ければ飛ばす、`MULAY_SKIP_WASM=1` で飛ばす)。
  wasm でだけ組む target-when の分岐の誤り (native のテストでは組まれない) を見つけるため。
- **wasm で組めない C の呼び出しは target-when で分ける**。
  - 小さなもの (pid、stdout の flush、readlink、sleep、環境変数の一覧) は `lib/host` に置く (`pid`・`flush-stdout`・
    `read-link`・`pause-ms`・`environ`)。wasm では pid 1、flush と sleep は何もしない、readlink は ""、環境変数は空。
    呼び出し側: `rt/persist`、`rt/log`、`lib/time/tz`、`rt/ostore`、`rt/engine` (sem-acquire・parallel-foreach の待ち・
    until-successful)、`dw/lib/system`、`dw/lib/runtime`。
  - `lib/fs` は stat・create-new・rmdir・unlink・rename をまとめて分け、wasm ではメモリのファイル表 (`mem-*`) で作る。
    rename は wasm では EXDEV と同じ扱い (写して消す)。
  - `lib/osinfo` は全体を分け、wasm では固定の値 (wasm32、browser、user、/)。
  - DW の asin・acos・atan は wasm では clay の組み込み、native は今までどおり libm (clay 0.97.0 には組み込みが無い)。
  - SQLite の関数の sin・cos・tan・exp・ln・log10・log は `lib/libm` を通し、native は libm (glibc)、wasm は clay の組み込み
    (2026-10-24)。clay 0.98.0 で組み込みが clay.math の実装 (glibc と 1 ulp 以内の差) になり、本物の SQLite (libm) と
    sin(2.5) の最後の 1 ulp が違ったため。DW の数学関数は golden (実 DW) と合ったままなので替えていない。
    pow は両方とも `prim/fpow` (native は libm の pow を呼ぶ)。
- wasm の sleep は無い (clay ADR 122)。待ちの loop は、single thread の wasm では条件がすぐ成り立つ所だけに残る。

## 測った時間 (2026-10-24、Node 22、orders-api)

- インスタンスを作る: 約 8 ms。`load`: 約 36 ms。
- `run` 1 例 (JSON の往復を含む): 0.15〜0.6 ms。フローの実行だけなら 0.04〜0.12 ms。
- mulay.wasm は 6.5 MB (-O2)。

## 場所

- `mulay.wasm.main`: `load`・`run`・`get-value`・`components`・`unpack`・`split-props`、`mulay.note.run/props-json`・`load-dir-with`
- `tools/wasm/build.sh`、`tools/wasm/run.mjs`
- target-when の分け: `mulay.lib.host`、`mulay.lib.fs`、`mulay.lib.osinfo`、`mulay.dw.lib.math`
- テスト: `test/note/wasm_unpack_test.clay`、`test/note/note_test.clay` (system-properties-win-over-global-and-file、fixture は test/fixtures/livenote/props)
