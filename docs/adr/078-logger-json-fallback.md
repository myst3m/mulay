# 078 — logger の message の式は推論した形式で書き、その形式で書けなければ JSON で書く

状態: **採用** (2026-10-18)

## 決定
- logger の message の `#[..]` は、ほかの式と同じく出力の形式を入力から推論して書く (JSON の payload の `'id=' ++ payload.id` は
  `"id=7"`、入力の形式が混ざれば "Unable to infer a output media type ..")。ADR 061 の String の引数の扱いとは違う。
- 推論した形式の書き手が値を書けないとき (XML の根の無い文字列、CSV の配列でない値、記述子の設定の無い protobuf) は、失敗にせず
  application/json で書き直す (`"id=7"`)。書ける値はその形式のまま (CSV の payload の `{id: ..}` は `id\n7`)。
- `mulay.rt.engine/eval-log-pval` が推論の段を INFER-LOG で動かす (`run-script-whole` の INFER-NO / INFER-YES / INFER-LOG)。

## 理由
- 実 Mule 4.11.3 で記録した (2026-10-18、test/fixtures/apps/core-infer-mix の /log-str-xml、/log-str-csv、/log-obj-csv)。
  これまでの mulay は書き手の失敗をそのまま式の失敗にしていた (MULE:EXPRESSION)。
- protobuf の payload (gRPC のサーバー) の `'hello ' ++ payload.name` でも、実 Mule は `"hello Ann"` を出した。

## 場所
- `mulay.rt.engine`: `eval-log-pval`、`run-script-now`、`run-script-whole`、`run-logger`

## 追記 (2026-10-18): 変数だけの式

- `#[payload]` と `#[vars.名前]` だけの式は、値を読まずに TypedValue をそのまま返す (`mulay.rt.engine/eval-pval` の
  `identity-input`)。これまでは `payload` だけがそうで、`vars.名前` は DW の入力として読んでから推論で書き直していた。
  読めない値 (記述子の引数を mime に持たない protobuf など) では "Missing required ProtoBuf setting `descriptorUrl`" で失敗した。
  実 Mule 4.11.3 は読まずに渡す (grpc-basic の /var-pass、gRPC の client-streaming の `content="#[vars.msg]"`)。
