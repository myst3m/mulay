# 093 — OS に触る所を lib/host に集める (wasm ではメモリのファイル表)

状態: **採用** (2026-10-24)

## 背景

ライブ・ノート (WebIDE) では、mulay を wasm32 にしてブラウザの Worker で動かす。clay の wasm には、ファイル・ディレクトリ・
環境変数が無い (`target-when` で外される)。clay main (ADR 121〜124) の CLI で試しにビルドすると、パーサー・実行・DW・
読み込み (`mule/load`) で止まるのはファイル操作だけだった (時計は host から読めるようになった)。

## 決定

- **`mulay.lib.host`** に、ファイル・ディレクトリ・環境変数の口を集める。native は clay の関数をそのまま呼び、wasm は
  `mount!` で渡されたファイルの表 (`FILES`、正規化した絶対パス → 中身) を読む。
  - `file-read`・`file-read-or`・`file-exists?`・`file-dir?`・`file-list`・`work-dir`・`file-write`・`file-append`・
    `make-dir`・`env`。clay.core と同じ名前にすると clay.core のものを隠すので、名前を変えてある。
  - wasm の表では、ディレクトリは「その下にファイルがあること」で決まる。`file-list` は直下の名前を辞書順で返す。
    `make-dir` は何もしない。`env` は常に「無い」。
  - 表の操作 (`mount!`・`mem-read`・`mem-list`・`mem-dir?`・`mem-exists?`・`mem-write`・`norm-path`) は native でも
    使えるので、native のテストで確かめる (`test/host`)。
- **時計と乱数も host に置く**。livenote の例 (Example) は固定の時計 (`clock`) と乱数の種 (`seed`) を持ち、now()・uuid()・
  random() を毎回同じにする (期待の判定が揺れないように)。
  - `set-clock!` (エポックからのミリ秒) を入れると `now-ns`・`now-ms` はその時刻を返し続ける。`clear-clock!` で実の時計に戻る。
    負の時刻は床除算で秒とナノ秒に分ける。`lib/time/tz` の `now-instant`・`now-instant-ns` (DW の now()、Timer、ログ) と、
    DW の properties 形式の日付行・multipart の境界はこれを読む。実の時計は native が clock_gettime、wasm が host の epoch-ms。
  - `set-seed!` を入れると `random-bytes` (`lib/random` 経由で uuid() と random()) と `rand-below` (multipart の境界) は
    splitmix64 の列を返す (8 バイトずつ、上位のバイトから)。同じ種なら同じ列になる。`clear-seed!` で実の乱数に戻る。
    種が無ければ実の乱数 (`real-random-bytes`) を使う。
  - 種で決まるのは暗号に使わない乱数だけ (2026-10-25 から): `lib/random/seeded-bytes` (DW の random()・uuid()、SQL の
    random()・randomblob()、Anypoint MQ の揺らぎ)。暗号に使う `lib/random/random-bytes` (`lib/crypto/random-bytes` も。
    SSH の鍵交換、seal の塩と IV、Salesforce の PKCE、Oracle の認証、WS-Security の nonce) は種を見ず、ネイティブでは
    いつも OS の乱数。前は note が例ごとに種を決めると、その間の鍵や nonce が誰でも作り直せる列になった (敵対的レビュー)。
  - `real-random-bytes` は native も wasm も `clay.crypto/random-bytes` (clay 0.112.0、clay の ADR 152)。native は OS の乱数
    (getrandom)。wasm は import の `env.clay_wasm_random(ptr, n)` で host から受け取る (tools/wasm/host.mjs は
    crypto.getRandomValues で 65536 バイトずつ埋め、失敗は 1 を返す)。host がこの import を持たないと、instantiate が
    LinkError になる。clay の random-bytes は 1 回 1 MiB までなので、1 MiB ずつ分けて呼ぶ。2026-11-05 までの wasm は、
    種が無いとき mono-us を種にした splitmix64 で、塩・IV・nonce が推測できた (脆弱性の点検)。
    試験: test/host/random_test (大きさ)、tools/wasm/host_test.mjs (scaffold の doc:id が crypto.getRandomValues から来る)。
  - 乱数が取れないとき (OS や host の失敗) は、弱い代わりの値を使わずに止める (clay の `fail`。Go の crypto/rand.Read と同じ)。
    native のサーバーでは、その要求だけが 500 になる (clay の ADR 024)。wasm では host に ClayTrap が届く。前は uuid4 が
    clay の `rand-int` に切り替え、`rand-below` は種が無いといつも `rand-int` だった。`rand-int` は rand-seed を呼ばないと
    どの起動でも同じ列なので (clay の仕様 10.1)、multipart の境界や関数の表示の番号が推測できた (2026-11-05、clay の指摘)。
    今の `rand-below` は種が無ければ実の乱数。app/otel の送り直しの揺らぎは `rand-int` のままでよい (推測されても困らない)。
  - note の例を実行する間は、uuid4 を使う所 (MCP のセッション ID、A2A のタスクの ID など) も種で決まる。例を毎回同じに
    するためで、そこで作る ID は記録を再生する模擬の中だけで使い、外へ出ない。
  - どちらも大域の atom で、native のサーバーは入れない (入れるのは例を実行する口だけ)。並行する要求の間で共有されるので、
    サーバーの中で入れてはいけない。
- 呼び出し側は、wasm の入口から届く所だけを替えた: `lib/res`、`lib/fs`、`lib/time/tz`、`dw/urls`、`dw/fmt/xml`、
  `rt/ops`、`rt/persist`、`mule/load`、`mule/props`。コネクタ (conn/*) は wasm の入口に入れない (記録の再生だけの登録表を
  別に作る) ので替えない。
- `FILES` の atom は `(atom (let [m: Map(Str Str) {}] m))` と型を書いて作る。`(atom {})` を def して後で型を書いて
  deref すると、clay 0.97.0 は「nth out of range (4/2)」とだけ言ってコンパイルに失敗する (clay に報告済み、2026-10-24)。
- タイムゾーンの規則 (`lib/time/tz`) は zoneinfo のファイルを host から読む。wasm の表には zoneinfo が無いので、
  wasm では当面 UTC と固定のオフセットだけになる (livenote と合意済み。サンプルの例の clock は UTC)。

## 場所

- `mulay.lib.host` (`set-clock!`・`clear-clock!`・`now-ns`・`now-ms`・`set-seed!`・`clear-seed!`・`random-bytes`・`rand-below`・`real-now-ns`・`real-random-bytes`)
- 時計と乱数の呼び出し側: `mulay.lib.time.tz/now-instant`・`now-instant-ns`、`mulay.lib.random/random-bytes`、`mulay.dw.fmt.text/date-line`、`mulay.dw.fmt.multipart/gen-boundary`、`mulay.dw.lib.multipart`
- 呼び出し側: `mulay.lib.res`、`mulay.lib.fs`、`mulay.lib.time.tz`、`mulay.dw.urls`、`mulay.dw.fmt.xml`、`mulay.rt.ops`、
  `mulay.rt.persist`、`mulay.mule.load`、`mulay.mule.props`
- テスト: `test/host/host_test.clay`、`test/eval/frozen_test.clay`
