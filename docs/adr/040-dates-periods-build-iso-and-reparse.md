# 040 — Dates / Periods の組み立て関数は ISO の文字列を組んで読み直す

状態: **採用** (2026-09-28 の記録。初期取り込みからこの形)

## 決定
- dw::core::Dates の date / dateTime / localDateTime / localTime / time は、範囲を検査してから ISO の文字列を組み、
  String として読む。月・日・時・分・秒は `as String {format: "00"}` (DecimalFormat、HALF_UP) で書く。
- dw::core::Periods の duration / period も、実 DW の Periods.dwl と同じく ISO の文字列 ("P1DT2H3M4.5S" など) を組んで
  Period として読む。duration の小数は下位の単位へ繰り下げ、下位のフィールドを明示すると繰り下がりは捨てる
  (`hours default 0 + ..` の優先順位)。

## 理由
- 実 DW の .dwl がこの形なので、同じ道筋で作れば小数の繰り上がり・文字列にできない値・2 月 30 日などの失敗の文言
  ("Cannot coerce String (2020-02-30) to Date") まで実 DW と同じになる。

## 場所
- `mulay.dw.lib.dates/build`、`mulay.dw.lib.dates/two`、`mulay.dw.lib.dates/date-str`、`mulay.dw.lib.dates/time-str`
- `mulay.dw.lib.periods/duration-of`、`mulay.dw.lib.periods/period-of`、`mulay.dw.lib.periods/parse-iso`
