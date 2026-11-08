# 024 — 暗黙のラムダと遅延引数は、型ではなく式の形と組み込み関数の引数型で決める

状態: **採用** (2026-09-28、ce64f08 の初版から。遅延引数 LAZY-ARGS は 2026-09-29、c683d39)

## 決定
- 暗黙のラムダ化は resolve が行う (パーサはしない)。中置の呼び出し `a f b` の引数 i を `$ $$ $$$` の 3 引数の
  ラムダに包むのは、次をすべて満たすとき (`rx-args`):
  - 組み込み関数のどれかのオーバーロードが、その位置で `Function` を取る (`wants-fn?`)。
  - 引数が値として関数を返す呼び出しでない (`fn-valued-call?`: 2 引数の `replace` は with に渡す関数を返すので
    包まない。`$` は外のもののまま)。
  - 引数が (入れ子の明示ラムダの外で) `$` を使う (`uses-dollar?`)、または関数値でありえない形
    (`maybe-fn?` が偽: リテラルや演算の結果)。名前・ラムダ・呼び出し・do・using・match は実行時まで分からないので
    「関数でありうる」として包まない。
- `$` の数え方は素直に数える: 引数の中の呼び出しの引数にある `$` も外側の式の `$` として数える。
- 前置の呼び出し `f(a, b)` では包まない (実 DW も前置では `$` の式を暗黙のラムダにしない)。
- 引数の無いラムダ `map() -> $ + 1` の本体の `$` は暗黙の引数として包み直す (`empty-lambda-dollar?`)。
- **遅延引数 (`() -> R` の引数、呼ぶまで評価しない) は表 `LAZY-ARGS` の位置だけ**
  (`dw::Runtime orElse 1`、`orElseTry 1`、`dw::Core onNull 1`)。ラムダと名前以外の式は引数なしのラムダにする
  (`lazy-arg?`、`lambda-or-ref?`)。

## 理由
- 実 DW は型を推論して判断する (`otherUser.name!` は関数でないので包む)。mulay は型を持たないので形で決める。
  形で決められない式 (名前や呼び出し) は包まない側に倒す。

## 場所
- `mulay.dw.resolve/rx-args`、`mulay.dw.resolve/wants-fn?`、`mulay.dw.resolve/maybe-fn?`、`mulay.dw.resolve/fn-valued-call?`
- `mulay.dw.resolve/uses-dollar?`、`mulay.dw.resolve/empty-lambda-dollar?`
- `mulay.dw.resolve/LAZY-ARGS`、`mulay.dw.resolve/lazy-arg?`、`mulay.dw.resolve/lambda-or-ref?`
