# 036 — 遅延引数と「関数を返す」標準関数は、resolve が作る形を組み込みの側で受ける

状態: **採用** (2026-09-28 の記録。値の位置は 2026-09-29、a64a183)

## 決定
- 実 DW は `() -> R` の引数 (onNull、orElse、orElseTry の第 2 引数) に式を書くと遅延評価の関数にする。mulay は resolve が
  式を引数なしのラムダに包む (名前の参照は包まない)。そのため組み込みの側は、関数が来たら呼び、関数でない値が来たら
  その値を結果として使う。
- update / mask の newValueProvider も同じく、関数なら呼び、そうでなければその値に置き換える。
- replace(text, m)、update(value, sel)、mask(value, sel) は、実 DW と同じく「with に渡す関数」を返す。replace は内部の
  組み込み関数 `replace#regex` / `replace#string` (利用者のスクリプトから名前で呼べない) を部分適用した関数値を返し、
  with(f, r) は f(r) を呼ぶだけにする。
- dw::Runtime の location / locationString は、値が位置を持たないので、resolve が引数の式から値を作った式をたどって
  位置を隠れた 2 つ目の引数で渡す (利用者は 1 引数で呼ぶ)。たどれない値は実 DW の位置の無い値と同じ形にする。

## 理由
- resolve が式を包み、組み込みが「関数なら呼び、値ならその値」とするだけで、実 DW の遅延引数と同じ結果になる。
  名前の参照は包まないので、組み込みは関数でない値も受けなければならない。
- replace / update / mask を DW の定義どおり関数を返す形にすると、`with` を特別扱いしなくてよい。

## 場所
- `mulay.dw.lib.runtime/force`、`mulay.dw.lib.core_misc/on-null`、`mulay.dw.lib.values/provide`
- `mulay.dw.lib.core_text/builtins` (`replace#regex`、`replace#string`、`replace#null`)
- `mulay.dw.lib.runtime/builtins` (location、locationString の 2 引数のオーバーロード)
- resolve 側は `mulay.dw.resolve` の「値の位置」
