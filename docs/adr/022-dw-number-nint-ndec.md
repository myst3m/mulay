# 022 — DW の Number は 64 ビット整数 (NInt) と BigDecimal 相当 (NDec) の 2 通りで持ち、正規形を 1 つに決める

状態: **採用** (2026-09-28、ce64f08 の初版から。小さい小数の Int 経路は 7e761b0)

## 決定
- 実 DW (2.11) の数は java.math.BigDecimal の意味論を持つ。mulay の `num/Num` は 2 通り:
  - `NInt`: scale 0 で 64 ビットに収まる整数 (高速経路)。
  - `NDec`: それ以外 (小数、64 ビットを超える整数、負の scale を持つリテラル)。
- **正規形**: scale 0 で Int に収まる NDec は作らない (`mk` が NInt に倒す)。値の側でも整数は `VInt`、それ以外は
  `VNum` で、`VNum` に NInt は入らない (docs/dw-eval.md §2)。
- 両方の値が 64 ビットの整数に収まれば (scale によらず: `1e18`、`1.0`) 整数で計算する。実 DW もそうする
  (`1e3 / 1e1` は 100)。判定では整数部の桁 (precision - scale) が 19 を超えるものを調べずに外し、`1E+999999999`
  を展開しない (`long-of`)。
- BigDecimal の演算結果は `norm-result` で正規化する (0 は 0、scale > 0 なら末尾の 0 を削る、scale <= 0 はそのまま)。
  組み込み関数の結果 (pow など) にも使う。
- 加減乗算は (結果、失敗の理由) を返す。理由は Java の ArithmeticException の文言 (桁を展開しすぎる加減算は
  `d/TOO-BIG`、乗算の scale が Java の int を超えれば "Overflow" / "Underflow")。
- 除算・mod の商を展開しすぎるとき、商の scale が Java の int を超えるときは、実 DW と同じく "Division by zero"。

## 理由
- NInt は高速経路。Int で計算すれば bigint を経由せず、値の確保も 1 回で済む (ADR 017)。
- 正規形を 1 つに決めておけば、パターンは「整数なら NInt / VInt」を前提にできる。
- 負の scale を展開しないことで、`1e999999999 * 1` のような式が桁を作らない (展開の上限は
  docs/compat/deviations.md の「指数の大きい数を展開する演算」)。

## 注意
- 小数の末尾の 0 は読むときに削る。実 DW は値に残して表示で削る (docs/compat/deviations.md「小数の末尾の 0」)。
- 正規化の規則の実例は test/fixtures/dw/bignum_test。

## 場所
- `mulay.dw.num/Num`、`mulay.dw.num/mk`、`mulay.dw.num/strip-pos`、`mulay.dw.num/norm-result`、`mulay.dw.num/long-of`
- `mulay.dw.num/div`、`mulay.dw.num/rem-num`、`mulay.dw.num/dec-res`、`mulay.dw.num/op-error`
- `mulay.dw.val/num-v`
