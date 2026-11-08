# 002 — 任意精度の整数は clay.bigint の BigInt を使い、Java の BigInteger の意味に合わせる

状態: **採用** (2026-09-28、2026-10-25 に clay.bigint へ移した)

## 決定

- 任意精度の整数は Clay の標準ライブラリの `clay.bigint/BigInt` (clay 0.99.0 から) を使う。演算子 (`+ - * quot mod < =` など) で書ける。
- `mulay.lib.bigint` は BigInt の上の薄い関数の集まりとして残す (`from-int`、`mul-pow10`、`divmod-pow10`、`divmod-small` など)。
  呼ぶ側の名前と、失敗の文言 (Java と同じ "BigInteger divide by zero"、"BigInteger out of long range" など) を変えないため。
- 除算と剰余は Java と同じ切り捨て: 商は 0 の方向へ丸め、剰余の符号は被除数と同じ (BigInteger.divideAndRemainder)。clay.bigint の divmod も同じ。
- 10 の冪の乗除は `pow10` の値との `*`・`divmod`。clay.bigint は掛ける数・割る数の下の 0 のリムを先に外すので、どちらも線形。
- Int (64 ビット) の溢れ検知 (`add-ov?`・`sub-ov?`・`mul-ov?`) もこの ns に置く。
- 失敗しうる関数は `Values(T Str)` を返す (err が "" なら成功)。

## 理由

- 前は mulay が自分で基数 10^9 のリム列と Karatsuba を持っていた。DataWeave の `7 pow 9999999` に 40 秒以上かかり、実 DW (3〜4 秒) より遅かった。
  汎用の部品なので Clay の標準ライブラリに入れてもらい (NTT の乗算)、mulay は 1.4 秒 (10 進の文字列にするまで) になった。
- BigInt は中身を見せない型 (defopaque) なので、リムを直接読む所は作らない。`mulay.lib.dec/pow-digits` は桁数と上位 17 桁から常用対数を見積もる。
- 意味は Java の BigInteger に合わせる (実 Mule の DataWeave は BigInteger / BigDecimal の上で動く)。

## 場所

- `mulay.lib.bigint` (全体)、`mulay.lib.dec/pow-digits`、`parse` (`of-digits`)
- Int の溢れ検知と INT-MIN の扱いは ADR 001。
