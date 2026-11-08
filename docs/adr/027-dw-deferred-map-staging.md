# 027 — output の deferred=true で本体が `A map F` なら、A と F に分けたプログラムで 1 要素ずつ作る

状態: **採用** (2026-10-03、0f915a8)

## 決定
- 本体が dw::Core の `map` の呼び出し `A map F` (組み込み関数の直接呼び出しで引数 2 つ) のスクリプトは、
  **本体だけを A と F に替えた 2 つのプログラム** (`Staged` の `src` と `fnc`) に分ける。最上位の var と fun は
  そのまま (`sub-compiled`)。
- A を評価した Array の要素ごとに、F を評価した関数を map と同じく (要素, 添字) で呼ぶ (`stage-fn`、`stage-apply`)。
  F が関数でなければ値をそのまま返す。
- A が入力そのもの (`stage-src-input?`) で、その入力が streaming=true の JSON の payload なら、要素もテキストから
  1 つずつ読む (rt 側)。
- 形が合わなければ分けない (`stage-map` が空を返し、普通に評価する)。

## 理由
- deferred=true の出力は読まれるときに評価し、本体が `A map F` の JSON なら 1 要素ずつ書く (出力全体を文字列に
  しない。docs/mule-runtime.md「deferred の出力」、外から見える違いは docs/compat/deviations.md)。そのために map の
  結果を 1 要素ずつ作る入口が要る。

## 場所
- `mulay.dw.engine/Staged`、`mulay.dw.engine/stage-map`、`mulay.dw.engine/sub-compiled`、`mulay.dw.engine/stage-src-input?`、
  `mulay.dw.engine/stage-fn`、`mulay.dw.engine/stage-apply`

## 関連
- ADR 054 (rt 側の deferred 出力と streaming 入力の map)
