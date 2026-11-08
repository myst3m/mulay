# 020 — DW のパーサで実 DW と意図して変えた点: head-tail 構築子は診断、正規表現は検査しない、`json---` は json

状態: **採用** (2026-09-28、ce64f08 の初版から)

## 決定
- **head-tail 構築子 `[h ~ t]` `{k: v ~ t}` は未対応として診断を出す**。AST に構築子のノードは無い。パーサは最初の
  要素の後ろの `~ tail` を読み飛ばして診断を積む (`ht-check`)。パターンの `case [head ~ tail]` と
  `case {k: v ~ tail}` は対応している (`PArrDestr`、`PObjDestr`)。
- **正規表現リテラルの中身はパース時に検査しない**。実 DW はパース時に Java の正規表現として検査する。mulay は
  本体の `\/` だけを `/` に戻し、それ以外のエスケープは正規表現エンジン (`mulay.lib.regex`、`ev/compile-regex`) に渡す。
- **`output application/json---` (改行なしの `---`) の内容の型を `"application/json"` と読む**。実 DW は
  `"application/json-"` と読む。subtype は `--` の手前で止める (`mime-end`)。

## 理由
- コードのコメントには「意図したもの」とだけあり、選んだ理由の記録は無い (初版 ce64f08 から)。
- head-tail 構築子は黙って別の形に読まず、未対応であることを診断で示す (AST にノードが無いため)。
- 正規表現は使うときに `ev/compile-regex` が組み立てるので、不正なパターンはそこで失敗する。

## 注意
- これらは `tools/dwparse/compare.py` の比較で既知の差として除く (ADR 018)。docs/compat/deviations.md の「意図した違い」に載せた。

## 場所
- `mulay.dw.parse/ht-check`、`mulay.dw.parse/p-array`、`mulay.dw.parse/p-object`
- `mulay.dw.parse/regex-body`、`mulay.dw.eval/compile-regex`
- `mulay.dw.parse/mime-end`
