# 019 — DW の AST は綴りとバイト位置を持ち、名前の解決と数値への変換は後段に任せる

状態: **採用** (2026-09-28、ce64f08 の初版から)

## 決定
- すべての式ノードは `Node` (式の種類 `Ex` + ソース位置 `Span`) で包む。**位置はバイトオフセット**で持ち、行・列への
  変換はエラーを表示するときだけ行う (`mulay.dw.src`)。
- **数値リテラルは元の綴りを Str のまま持つ**。精度を落とさずに Int / Dec へ変換するのは eval 側
  (`num/parse-lit`)。
- **名前は解決前の綴りのまま持つ** (`"dw::core::Strings::camelize"`、`"$"`、`"$$"`)。スコープとモジュールの解決は
  resolve が行う。loader 付きの名前 (`java!pkg::Cls::m`、`import * from jsonschema!a::b`) もつづりのまま。
- DW の AST と違う写し方:
  - `++` `--` `default` と算術・比較・論理の演算子は `EBin` (op はつづり)。それ以外の中置呼び出し (`a map f`、
    `10 mod 3`、`1 to 5`、`"a" ++lower("b")` の `++lower`) は `ECall(ERef 名前, [左 右])`。
  - `unless (c) a else b` は `EIf` の条件を `EUnary "not"` で包む。
  - `x["k"]` (補間の無い文字列リテラルの添字) は `x."k"` と同じ `SelKey` (DW のパーサも書き換える)。
  - 名前を書かない match の case の bind は `""`。`case []` `case {}` は空の配列・オブジェクトの `PLit`。
  - 注釈の引数 (`@A(x = 1)`) は 1 エントリのオブジェクト `{x: 1}` の並び。式・引数・var の注釈は捨てる
    (`@Metadata` の付いた注釈だけは式の値にメタデータを付ける)。
  - テンプレートの呼び出し ``f `a$(x)b` `` は DW と同じく `f(["a", "b"], [x])`。
  - `%dw 2.5` 以上の `f<T>(x)` は型引数を捨てた呼び出し (2.4 以下と版の無いものは比較として読む)。
  - 型: `{_: T}` と `{(K): T}` のキーは `""`。属性の型 (`@(..)`) は捨てる。`T {..}` と `T <~ {..}` は `TMeta`。
- 回復したパースエラーは `EErr` として木に残し、結果全体は失敗にする (ADR 021)。

## 理由
- 位置の変換は失敗のときだけ要る。バイトオフセットなら全ノードで安く持てる。
- 数を早く Float や Int にすると精度と綴り (`1E+2` の表示) が失われる。DW の数は BigDecimal の意味論 (ADR 022)。
- 注釈・型引数・属性の型は実行に効かないので持たない。

## 場所
- `mulay.dw.ast/Node`、`mulay.dw.ast/Span`、`mulay.dw.ast/Ex`、`mulay.dw.ast/Ty`
- `mulay.dw.parse/parse`、`mulay.dw.parse/sel-node`、`mulay.dw.parse/p-level-loop`
- `mulay.dw.src/line-col`、`mulay.dw.src/render-diag`
