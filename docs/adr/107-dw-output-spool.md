# 107 — DW の出力は spool に書き、512 KB を超えたら読み直せる流れ (PIPE) にする

状態: **採用** (2026-10-26。JSON・NDJSON・XML の出力、UTF-8 だけ)

## 決定

- set-payload・transform などの DW の出力 (`rt/engine` の `written-ns`) は、書き手を `fo/Sink` につなぎ、64 KB ごとに
  `lib/spool` に積む (`mulay.rt.outspool/write`)。初めの 512 KB (`rt/bodies/IN-MEMORY`) はメモリに、超えた分は
  `mulay.work.dir/<アプリ>/spool/<pid>/out-<n>` のファイルに書く。要求の本文 (ADR 104) と同じ置き場所と同じしきい値。
  実 Mule の EE の既定 (repeatable-file-store-stream、inMemorySize 512 KB) と同じ形。
- **書く前に値を入れ子まで読まない** (`v/whole-deep` をやめた)。書き手が並び (VSeq、ADR 105) から要素を引き出しながら書く。
  入力が並びなら、入力・変換・出力のどこでも全体をメモリに持たない。
- **TypedValue**: 512 KB を超えたら PIPE (値は持たない。読む所は spool から読み直す。JSON なら並びで読む)。
  512 KB 以下で、値に並びが無ければ今までどおり (JSON なら値と本文の両方 BOTH、他は RAW)。
  並びがあれば、JSON は書いた本文を読み直した値で BOTH にし、他は本文だけ (RAW)。並びを持つ値をそのまま残すと、
  使うたびに並びをもう一度評価する (大きな入力の流れを読み直す) ので残さない。BOTH を保つのは、値を持つかどうかで
  外から見える振る舞いが変わる所があるため (validation の文言は、値なら JSON、流れなら ManagedCursorStreamDecorator@..。
  `MULAY_DW_LAZY_ALL=1` の validation-ops で見つけた)。
- **持ち主と消す時**: PIPE の持ち主はイベントの rid (要求、または listener の無い flow の実行)。持ち主が抜けると
  (`stream/leave`)、spool のファイルを消す。DW の評価や書き出しが途中で失敗したら、その場で spool を消して、
  今までと同じ文言の誤りにする (評価は変換の段で最後まで行う。ADR 054 の deferred とは違い、誤りを後の段に持ち越さない)。
- **対象**: 書き手が Sink に流せる形式 (`reg/streams?`: JSON・NDJSON・XML) で、出力の文字コードが UTF-8 のとき。
  それ以外 (CSV などの書き手、UTF-8 以外の文字コード、rid の無いイベント) は今までどおり全体を 1 つの文字列にして書く。
- **XML の書き手** (`xml/write-ns-to`): 子の要素を 1 つ書くたびに Sink に流す。並び (同じ名前の要素の繰り返し) と遅延したオブジェクト
  (子の要素の列、ADR 105 第 5 段) から引き出して書く。空の要素 (`<a/>`) の判定は先頭の 1 つ、根が 2 つあるかの判定は先頭の 2 つだけを見る。
  書き手の状態 W の誤りは DwErr にした (並びを読む途中の DW の誤りを、種類を保って返すため。書き手の誤りは今までどおり WriterException)。
  100 万件の JSON を `{orders: {(payload map {order @(id: ..): {..}})}}` で XML に書く flow (tools/mule-bench の json2xml) は、
  ピーク RSS が 848 MB から 37 MB (出力は前とバイト単位で同じ)。
- spool のディレクトリは、初めて 512 KB を超えたときに作る (`outspool/ensure-dir`、作ったものを覚えて 2 回目からは調べない)。
- wasm では `lib/spool` はファイルに書かず、全部をメモリに持つ (clay.io の open・pread・pwrite が wasm に無い。target-when)。

## 理由

- 出力を 1 つの文字列にすると、出力の大きさの 2〜3 倍 (値の木、文字列、符号化した写し) をメモリに持つ。
  100 万件の JSON を map して JSON に書く flow (114 MB 入力、67 MB 出力) は、ピーク RSS が 408 MB だった。spool に流すと 42 MB
  (2026-10-26、CPU 0-3)。tools/mule-bench の json-filter は 260 MB から 38 MB、時間も 1.3 秒から 1.1 秒に縮んだ。
- 要求の本文 (ADR 104) と同じ PIPE にすれば、file:write (64 KB ずつ写す)・listener の応答・次の DW の入力 (JSON の並び) が
  そのまま流れで扱える。新しい状態を足さずに済む。

## 残ること

- CSV の書き手を Sink に流す (今は全体を書いてから)。
- UTF-8 以外の文字コードの出力を、塊ごとに符号化して流す。
- ADR 054 の決め打ちの流し方 (`run-streamed`) を、この一般の道で置き換えて消す。

## 場所

- `mulay.rt.outspool` (`write`、`open`)、`mulay.rt.engine` (`written-ns`、`spooled`、`written-whole`)、`mulay.dw.fmt.registry/streams?`
- `mulay.lib.spool` (wasm の target-when)
- 試験: test/rt/spool_out_test (512 KB を超える出力が PIPE になり 2 回読める、持ち主が抜けると消える、小さな出力はメモリ、
  途中の失敗で spool が残らない、並びを含む小さな JSON の出力は値を持つ、遅延したオブジェクトを XML で書いて spool に流す)
