# 052 — TypedValue は state で値とバイト列の持ち方を分け、ストリームは ID で持つ

状態: **採用** (2026-09-28。CURSOR は 2026-10-03 d40d9d3、DEFER は 2026-10-03 0f915a8、PIPE は 2026-10-09 588c98c、
String の符号化は 2026-09-29 a231e46)

docs/mule-runtime.md §2 は VAL / RAW / BOTH の扱いを書く。ここではそれ以外の state と、境界のバイト列の規則を書く。

## 決定
- `ev/TV {val mime props raw state stream}` の state:
  - VAL: 値だけ (application/java や DW の中間結果)。RAW: バイト列だけ (最初に DW が読むときに mime で parse)。
    BOTH: 書き出したバイト列と、それを読み直した値と等価な値。
  - **FAILED**: 読むと失敗するストリーム (実 Mule で中身を読むと例外を投げる InputStream。File の timeBetweenSizeCheck で
    大きさが落ち着かなかったもの、読み終えた DEFER)。raw に Java の例外の文言 (`<クラス> - <文言>\n<クラス>: ..`)。
  - **CURSOR**: 行のストリーム (DB の select の結果)。raw にカーソルの ID (rt/stream。ADR 053)。DW が読むときと境界で
    書き出すときに全部読んで VAL にする (`realize`)。foreach と batch:job は少しずつ読む。
  - **DEFER**: DW の `output .. deferred=true` の結果 (rt/deferred。ADR 054)。raw にストリームの ID。読めるのは 1 回だけ
    (`drain`)。2 回目は Pipe closed で失敗する。
  - **PIPE**: 届いた分から読める本文 (http:request の streamResponse)。raw に rt/stream の ID (行は本文の断片の VStr)。
    listener の chunked 応答は届いた断片をそのまま書く。それ以外の読み方 (DW、ログ、ファイルへの書き込み) は全部届くのを
    待って RAW として読む (`pipe-raw`)。読んだ内容は持つので何度でも読める (実 Mule の repeatable なストリーム)。
- `stream` の欄: 実 Mule で InputStream (まだ読んでいないストリーム) の payload か。http:listener の
  responseStreamingMode=AUTO が chunked で返すかを決める (DW の output の結果、file:read、streamResponse の http:request の応答は
  true。文字列・Java の値・streamResponse でない応答は false)。
- 要求の外へ持ち出す値 (Object Store、VM のキュー、永続化) と表示には `settle` を通す: CURSOR は全部読んだ VAL に
  (読めなければ FAILED)。
- **VAL の String で、DataType がデータ形式** (application/java でも `*/*` でも text/plain でもない) なら、読むたびにその形式で
  parse する (`set-payload value='{"k": 1}' mimeType="application/json"`)。TV は VAL のまま返す (送るときに DataType の charset で
  符号化するため)。
- 境界のバイト列は 2 つ:
  - `bytes`: RAW / BOTH はそのまま。VAL は null が空、String と Binary はそのまま、それ以外は application/java (と `*/*`) なら
    Java の直列化 (rt/javaser)、他の mime ならその形式で書き出す。ファイルへの書き込みはこれ (String は UTF-8 のまま)。
  - `wire-bytes`: 送信 (HTTP の本文) 用。String の値は DataType の charset で符号化する (実 Mule と同じ)。それ以外は bytes と同じ。

## 理由
- 大きな結果 (select、deferred の出力、上流の本文) を値の木やバイト列にしてから渡すと、メモリと時間を使う。ID で持ち、
  読み方ごとに必要な分だけ読む。
- 一度しか読めないもの (DEFER) と読み直せるもの (PIPE、CURSOR の all) の違いは実 Mule の挙動に合わせた
  (test/fixtures/apps/dw-deferred、http-stream)。

## 場所
- `mulay.rt.event`: `TV`、`tv-pipe`、`pipe-raw`、`PIPE-CLOSED`、`drain`、`defer-open`、`realize`、`settle`、`string-value`、`bytes`、`wire-bytes`、`value-named`
