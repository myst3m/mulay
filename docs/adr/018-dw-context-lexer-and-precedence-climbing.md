# 018 — DW のパーサは手書きの再帰下降と precedence climbing にし、字句はパーサが文脈を渡して 1 トークンずつ読む

状態: **採用** (2026-09-28、ce64f08 の初版から)

## 決定
- **トークン列を先に作らない**。パーサ (`mulay.dw.parse`) が位置と文脈 (mode: `M-INFIX` / `M-PREFIX` / `M-TYPE`) を
  渡し、`lex/next-tok` が 1 トークンずつ返す。DataWeave の字句は文脈で変わるため:
  - `/` は前置の位置なら正規表現リテラル、中置の位置なら除算。
  - `|` は前置の位置なら日時リテラル `|2020-01-01|`、型の中なら union。
  - 型の中では `>>` を 2 つの `>` に分け (`Array<Array<String>>`)、`{|` `|}` `{-` `-}` を認める。
- 文字列トークンは引用符を含む全体を覆い、中身の解釈 (エスケープと補間) はパーサが行う。`a::b::c` の完全修飾名は
  1 トークン。
- **二項演算子は precedence climbing で読む**。強さは実パーサ (Mule 4.11、DW 2.11.2) で確かめた 10 段 (`L-AS` ..
  `L-TOP`)。DW の文法は階層型の PEG なので、ある強さで畳んだ後により強い演算子は続けられない
  (`x is String + 1`、`x <~ y * 2` は誤り)。precedence climbing の `cur` で同じ制約を課す。
- 前置の `-` と `not` は被演算子を `or` の強さまで伸ばす (`-a * b` は `-(a * b)`)。前置の位置の `-` の直後に数字が
  あれば負の数値リテラル、中置の位置では減算。
- 暗黙のラムダ化 ($ を含む中置の右辺) はパーサではしない (resolve の仕事)。

## 理由
- 文脈で字句が変わる言語で先にトークン列を作ると、`/` や `|` の解釈を後から直す必要がある。
- 階層型 PEG の受理/拒否を合わせないと、実 DW が拒むスクリプトを受け入れてしまう。

## 検証
- `tools/dwparse/compare.py` が実 DW (`tools/dwparse/dw-parse-oracle`) の AST をこの AST と同じ表記
  (`mulay.dw.astdump`) に直して比べる。golden は `test/fixtures/dwparse/*.golden`。変異させたスクリプト 1 万件でも、
  受理/拒否と木の形が実 DW と一致する (ADR 020 の違いを除く)。

## 場所
- `mulay.dw.lex/next-tok`、`mulay.dw.lex/M-INFIX`、`mulay.dw.lex/M-PREFIX`、`mulay.dw.lex/M-TYPE`
- `mulay.dw.parse/p-level`、`mulay.dw.parse/p-level-loop`、`mulay.dw.parse/p-unary`、`mulay.dw.parse/L-TOP`
- `mulay.dw.astdump` (golden 比較用の表記)
