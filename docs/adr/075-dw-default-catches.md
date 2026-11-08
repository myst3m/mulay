# 075 — DataWeave の default は、型変換の失敗と null を渡した関数の型違いだけを受ける

状態: **採用** (2026-10-17)

## 決定
- `a default b` は、`a` の失敗のうち次の 2 つだけを受けて `b` にする。ほかの失敗はそのまま上へ出す。
  - 型変換の失敗 (`Cannot coerce <型> (<値>) to <型>`)。kind は `CoercionException`。
  - 引数に null を含む関数の型違い (`abs(null)`、`substring("abc", null, 1)`)。kind は `InvalidFunctionArgsNull`
    (null を含まなければ `InvalidFunctionArgs`)。
- 受けないもの: `fail`、0 除算、null を含まない関数の型違い (`"x" + 1`)、読み取り・書き出しの失敗 (書き出しの
  `Cannot coerce ..` は受ける)、正規表現の誤り、比べられない型、スタックあふれ、初期化の前の変数、そして型変換でも
  別のクラスの失敗:
  - `Unable to coerce .. as Number using .. as format.` (kind `InvalidNumberFormat`)
  - `Invalid unit: ..` (kind `InvalidUnit`)
  - `Cannot coerce Binary to String because the specified base ..` (kind `UnsupportedBaseProperty`)
  - `Unable to transform String to hex binary ..` (kind `InvalidHexStringContent`)
  - `Unable to transform String to Base 64 Binary ..` (kind `InvalidBase64Content`)
- `dw::Runtime::try` の `error.kind` は kind に `Exception` を付けたもの。関数の型違いは実 DW と同じ
  `UnexpectedFunctionCallTypesException` にする。

## 理由
- 実 DW 2.11.2 (Mule 4.11.3 同梱) の `DefaultNode.doExecute` を javap で読んだ。
  - `disableExceptionHandlingOnDefaultOperator` が真の枝は、`UnsupportedTypeCoercionException` (とその子) と、
    実引数の型に Null を含む `UnexpectedFunctionCallTypesException` だけを受ける。
  - 偽の枝は、さらに `UserException`、`InvalidBase64ContentException`、`UnknownAlgorithmException`、
    `IllegalHMACArgumentException` も受ける。
  - 実 Mule では真の枝が動いている。base64、HMAC の空の鍵、`fail` は受けなかった。
- 失敗のクラスは `try(() -> ..).error.kind` で確かめた (`"a" as Number` は InvalidNumberException、`"x" as Boolean` は
  InvalidBooleanException でどちらも UnsupportedTypeCoercionException の子、書式は InvalidNumberFormatException など)。
- テストで守っているもの: test/fixtures/dw/default_catch_test の 53 件 (期待値は実 DW)。

## 残した差
- 実 DW の `map` などの結果は遅延していて、中の失敗は書き出すときに出るので `default` に届かない
  (`(["a"] map ($ as Number)) default 1` は失敗する)。mulay はその場で評価するので受ける
  (docs/compat/deviations.md の遅延評価の項)。

## 場所
- `mulay.dw.eval/default-catches?`、`mulay.dw.rt/call-types-kind`、`mulay.dw.loc/dw-kind`
- kind を付ける所: `mulay.dw.coerce`、`mulay.dw.coerce_num`、`mulay.dw.coerce_time` (`fail-unit`)、`mulay.dw.lib.binaries`、
  `mulay.dw.lib.core_io` (`write-impl`)
