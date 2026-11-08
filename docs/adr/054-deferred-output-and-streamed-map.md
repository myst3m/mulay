# 054 — deferred=true の出力と streaming=true の入力の map は、`A map F` を 1 要素ずつ書く

状態: **採用** (2026-10-03 0f915a8。断片ごとの書き込みと deferred でない map は 2026-10-03 8b675c9)

外から見える挙動と実 Mule との違いは docs/mule-runtime.md §4 と docs/compat/deviations.md にある。ここでは仕組みの選択を書く。

## 決定
- DW の `output .. deferred=true` は変換のときに評価しない。書き出したテキストの断片 (VStr) を出す行のストリーム (rt/stream)
  として登録し、payload は DEFER (ADR 052) にする。評価は読まれるときに行う。
- **入力の値は変換のときに決める** (payload を parse する)。ただし本体が `payload map F` (payload を他で使わない) で、payload が
  streaming=true の JSON の配列なら、payload は値にせず、テキストのまま要素を 1 つずつ読む (`lazy-text`)。
- 書き方: 本体が `A map F` で出力が JSON なら、A の要素ごとに F を呼んで 1 要素ずつ書く。それ以外 (CSV、XML、map でない本体、
  A が Array でないか F が関数でないとき) は最初に読むときに全体を評価して書く。
  - 状態 `St` の phase は 0 まだ、1 配列の要素を書いている、2 終わり。i は読んだ要素の数、n は書いた要素の数 (skipNullOn で
    消したものを除く)。
  - 次の最大 k 要素を 1 つの断片にして返す (`elems`)。断片はテキストのまま持ち、符号化は後でまとめて行う。
- 途中で評価が失敗したら、それまでに書いたテキストで終える。失敗の文言は stream のエラーとして残し、ファイルへの書き込みが見る。
- **deferred でなくても**、本体が `payload map F` で payload が streaming=true の JSON の配列なら、変換のときに同じ方法で
  1 要素ずつ書いてテキストにする (`run-streamed`)。入力と出力の値の木を作らない。途中で失敗したら [] を返し、呼び出し側が
  全体を評価し直してエラーの文言を作る。
- スクリプトごとの `A map F` の分解 (`eng/Staged`) は、スクリプトのテキストをキーに `STAGED` の atom に覚える。

## 理由
- 100 万件の JSON (232 MB) → map → 書き込みで、値の木を作らずに RSS と時間を実 Mule より小さくする (数値は docs/mule-runtime.md §4)。
- 入力の値を変換のときに決めておけば、読まれるときまで Event を持ち越さずに済む (docs/compat/deviations.md)。

## 場所
- `mulay.rt.deferred`: `St`、`per-elem?`、`start`、`elems`、`out-raw`
- `mulay.rt.engine`: `lazy-text`、`run-streamed`、`STAGED`、`run-script`
- `mulay.rt.event`: `drain`、`defer-open`

## 関連
- ADR 027 (dw 側の `A map F` の分け方)
