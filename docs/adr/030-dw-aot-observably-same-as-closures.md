# 030 — 事前コンパイルの生成コードは、閉包のコンパイルと評価の順・失敗・深さまで同じにする

状態: **採用** (2026-09-28、dcf7084。集計の合成は 2026-10-04、a6b7f2c)

docs/aot.md (使い方、登録表、節の番号、任せる節、段階、検証) を補う。

## 決定
- 生成するコード (`mulay.dw.gencode`) は、閉包のコンパイル (`ev/cx`、`ev/tx`) と**同じ順で評価し、同じ補助関数で
  同じ失敗を返す**。式ごとの対応 (as / is、補間、オブジェクトの項目の条件・キー・値の順、配列、式のキー、展開) は
  生成関数ごとに eval の対応する関数 (`ev-obj`、`ev-key`、`ev-interp`、`cond-ok`) に合わせる。
- **深さ (depth) の増え方も同じにする**。スタックあふれの失敗の位置が変わらないように (ADR 017)。末尾位置の式
  (`emit-t`) は `ev/tx` と同じくそこでは深さを調べない。ラムダの本体の展開 (`emit-body`) は `ev/tx` と同じく
  if と do の var は末尾をたどり、それ以外は d + 1 で評価する。
  関数の本体そのものが呼び出しなら、`ev/tx-body` と同じく末尾として扱わない (`emit-t-body`)。
- 高階関数の展開 (`hof-kind`) は次の場合に限る: dw::Core の map / filter / reduce / orderBy で、関数引数がその場の
  ラムダ、本体の末尾位置に呼び出しが無い (`tail-call?`。末尾呼び出しの深さの数え方が変わるため)、渡さない引数
  (3 番目以降) にすべて既定値があり、**オーバーロードの組 (alts) を持たない** (組は実行時に選ぶので展開しない)。
- 展開した orderBy は、鍵を map と同じく集め、core_coll の `sort-by-keys` (安定な並べ替え) で元の要素を並べる。
- 生成したモジュールを引く鍵は、スクリプトの本文と入力名の **FNV-1a 64 ビット (16 進)** (`gen/script-hash`)。

## 理由
- 実行の仕組みが 2 つになるので、同じ golden を両方で回して失敗の集合が同じことを確かめる (docs/aot.md §2、§5)。
  評価の順・失敗の位置・深さが食い違うと、その比較が成り立たない。

## 場所
- `mulay.dw.gencode/emit-v`、`mulay.dw.gencode/emit-t`、`mulay.dw.gencode/emit-t-body`、`mulay.dw.gencode/emit-body`、`mulay.dw.gencode/bind-params`、
  `mulay.dw.gencode/emit-hof`、`mulay.dw.gencode/hof-kind`、`mulay.dw.gencode/tail-call?`、`mulay.dw.gencode/fold-kind`、
  `mulay.dw.gencode/deep`
- `mulay.dw.gen/script-hash`、`mulay.dw.gen/nodes`、`mulay.dw.gen/make-g`、`mulay.dw.gen/assemble`
