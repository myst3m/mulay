# 032 — 失敗の位置と枠 (try の error.stack) は、失敗が抜けるときに DwErr に積んで作る

状態: **採用** (2026-09-29、a64a183)

docs/dw-eval.md §3 (DwErr の形) と docs/compat/deviations.md「try の失敗の stack」(外から見える違い) を補う。

## 決定
- 評価の失敗は位置なしで作り (`rt/err`)、**抜ける途中で位置と枠を足す**。
  - `dwe/at`: 位置がまだ無ければ付ける (最も内側の位置を残す)。いまの枠の中の位置 (`pend`) も同じ。
  - `dwe/exit-frame`: 名前付きの関数から失敗が抜けたら、いまの枠をその名前で閉じて `frames` に積み、呼び出し側の
    枠の位置を呼び出しの位置にする。ラムダ (`"<anonymous>"`、`"<filter>"` など) では閉じない。
  - 組み込み関数のオーバーロードの中で起きた位置の無い失敗には、標準ライブラリの native の関数の枠と .dwl の位置を
    付ける (`rt/native-frame`、表は ADR 031 の stdlib_locs)。native で書かれていない関数や対応の分からないものは
    そのまま。
- **末尾呼び出しの経路** (呼んだ関数と呼び出しの目印) は `call-def` のループで最初の `HOPS` (64) 段だけを持ち、
  失敗したら `unwind` が新しいものからたどって枠を閉じる。末尾呼び出しの続きは成功の DwErr (`rt/tail-mark`) の
  sp に呼び出しの位置を持つ。
- 成功の DwErr は共有の定数 `dwe/OK` (mulay.dw.err) (ADR 017)。

## 理由
- 枠の作り方そのものの理由はコメントに無い。HOPS で打ち切るのは、深い末尾再帰で 1 段ごとに経路を記録しないため
  (それより深い段で失敗すると途中の枠が欠ける。docs/compat/deviations.md)。

## 場所
- `mulay.dw.err/DwErr`、`mulay.dw.err/StackF`、`mulay.dw.err/err`、`mulay.dw.err/at`、`mulay.dw.err/exit-frame`、
  `mulay.dw.rt/native-frame`、`mulay.dw.err/tail-mark`、`mulay.dw.err/stack-of`
- `mulay.dw.eval/call-def`、`mulay.dw.eval/HOPS`、`mulay.dw.eval/unwind`、`mulay.dw.eval/lambda-name?`
- `mulay.dw.loc/stack-v`、`mulay.dw.loc/err-loc`
