# 023 — 数値の書式は Java 17 の DecimalFormat を移植し、ロケールの記号は CLDR の表を埋め込む

状態: **採用** (2026-09-28、ce64f08 の初版から)

## 決定
- `as String {format: ..}`、`as Number {format: ..}`、dw::util::Coercions の toString / toNumber が使う数値の書式は、
  実 DW 2.11.2 が使う **Java 17 の `java.text.DecimalFormat` の互換実装** (`mulay.dw.numfmt`) にする。基準にする経路は
  applyPattern / format(BigDecimal) / parse の setParseBigDecimal(true)。
- Java の内部の部品をそのまま写す: DigitList (`DL`、`round-dl`、`dl-dec`)、applyPattern (`compile-pattern`、
  `parse-sub`)、subparse (`subparse-number`)。Java の型の癖 (byte の `++` が 127 の次に -128、`(int)` キャストの下位
  32 ビット、DigitList.fitsIntoLong) も写す (`byte-inc`、`int32`、`fits-long?`)。
- ';' の無いパターンは、Java と同じく同じ文字列を負のサブパターンとしてもう一度読む (`"0E0E0"` のように負として
  読んだ接辞が正と食い違えば、負の数にもマイナスが付かない)。
- **ロケールの記号は Java 17 の DecimalFormatSymbols (CLDR) の値を表 (`SYMS`、`CURS`) で持つ**。言語だけのタグ
  (無ければ und) と同じ値の地域タグは省く。
  - タグは Locale.forLanguageTag と同じ規則で読む (`de_DE` のような `_` 区切りは不正なので und)。
  - 表は後ろの subtag を削りながら引き、最後は und (`table-find`)。
  - Unicode 拡張 `-u-nu-<数字体系>` は 0 の文字だけを差し替える (`nu-zero`。Java の CLDR が数字だけを差し替える)。
  - 既定のロケールは en-US。
- 丸めモードは `mulay.lib.dec` の定数 (UP .. UNNECESSARY)。

## 理由
- 正しさの基準は実 DW の出力と文言。DecimalFormat の手順を写すことで、丸め (0.0009 を "0.00" で UP にしても 0 に
  なる癖)、負の数が 0 に丸まったときの "-0.00"、空のパターンの既定値、不正なパターンの IllegalArgumentException と
  UNNECESSARY の ArithmeticException の文言まで同じにしてある。
- mulay は JVM の外で動くので、Java のロケールデータは表として持つ。

## 場所
- `mulay.dw.numfmt/compile-pattern`、`mulay.dw.numfmt/format-dec`、`mulay.dw.numfmt/parse-dec`、`mulay.dw.numfmt/parse-with`
- `mulay.dw.numfmt/SYMS`、`mulay.dw.numfmt/CURS`、`mulay.dw.numfmt/symbols`、`mulay.dw.numfmt/table-find`、`mulay.dw.numfmt/nu-zero`
- `mulay.dw.coerce_num/num-to-str`、`mulay.dw.coerce_num/str-to-num`
