# 005 — 文字列は UTF-8 のバイト列のまま扱い、壊れた並びは最大部分ごとに U+FFFD にし、Unicode の表は生成して持つ

状態: **採用** (2026-09-28)

## 決定

- Clay の Str はバイト列で、mulay は UTF-8 として扱う。`mulay.lib.uni` は名前に "cp" (コードポイントの添字) と付かない限り、
  テキストを**バイトの位置**で指す。
- 壊れた UTF-8: `decode-at` は失敗しない。壊れた並びは U+FFFD に読み、JDK の CharsetDecoder が報告する長さを消費する
  (`clay.utf8/decode-at` の上に作る。2026-10-26 から)。ほとんどは「最大部分」(正しい並びの始まりでありえた最長の前置き、少なくとも 1 バイト) で、
  "\xE2\x82" は U+FFFD 1 つ、"\xFF\xFF" は 2 つ。ただし JDK の癖で、ED の後の範囲外の継続バイト (UTF-8 で書いたサロゲート ED A0..BF ..) は
  後ろの継続バイトまでまとめて 1 つ (ED A0 80 は U+FFFD 1 つ)。テキストを歩く関数 (cps、upper、lower、strip など) はこれを受け継ぎ、
  `sanitize` は置き換えを明示する。文字数は `clay.utf8/codepoint-count` (同じ規則。mulay の cp-count は 2026-10-26 に消した)。
- 2026-10-26 より前の uni はサロゲートを 1 バイトずつ拒んでいた (Unicode の推奨どおり)。乱数のバイト列 20 万個で JDK 17 と比べると
  270 個で食い違った。実 Mule は JDK で読むので JDK に合わせる。
- DW の text の読み手は、壊れた UTF-8 を置き換えずに、最初の壊れた並びの手前で切る (`uni/valid-prefix`。実 Mule の記録、fixture dw-utf8-malformed)。
- 大文字小文字と分類は java.lang.Character / String.toUpperCase(Locale.ROOT) の意味。表は `mulay.lib.unitab` (生成物、手で編集しない。
  tools/gen-unicode.py)。
- unitab の出どころ: 一般カテゴリ、完全な大文字小文字の対応、割り当て済みの文字の集合は Python の unicodedata (Unicode 16.0.0)。
  単純な対応 (UnicodeData.txt)、PropList、DerivedCoreProperties、Scripts は UCD 17.0.0 から、上の集合に絞って取る。Blocks.txt はそのまま。

## 理由

- U+FFFD の置き方は Unicode 標準 (3.9 節、U+FFFD の置き換え) の規則で、JDK の UTF-8 デコーダと WHATWG の encoding の仕様が従うもの。
- 注意: mulay の基準の Java 17 は Unicode 13.0 を実装する。13.0 より後に割り当てられた文字は JVM と分類が違いうる
  (正規表現への影響は ADR 004)。

## 場所

- `mulay.lib.uni/decode-at`、`next-index`、`valid-prefix`、`sanitize`、`mulay.lib.unitab` (生成物)
