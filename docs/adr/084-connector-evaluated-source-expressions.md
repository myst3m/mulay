# ADR 084: source の式をコネクタが自分で評価する (raw-sources)

日付: 2026-10-20。状態: 決定。

## 背景

- `http:polling-source` には式の属性がある: `splitExpression`、`watermarkExpression`、`idExpression`、
  `<http:polling-request-*>` の key と value。
  - 式の中で `item` (分けた 1 件) と `watermark` (今の watermark) を使える。
  - これは Mule の束縛 (payload、attributes、vars など。m/BINDINGS) には無い。
- 実 Mule でも、これらの属性は XSD の上ではただの文字列 (`xs:string`) である。
  - コネクタ (HttpPollingSource) が、自分で束縛を作って評価する。
  - bytecode の定数: `payload`、`item`、`attributes`、`watermark`。
- mulay の mule/parse は `#[...]` を見つけると、決まった束縛で DW としてコンパイルする。
  - そのため `item` を使う式は "Unable to resolve reference" になり、アプリが起動しない。

## 決定

- Connector に `raw-sources` (要素の局所名の列) を足す。rt/conn の `parse-hints` が、これを Hints の `raw-sources` (`"<uri> <局所名>"`) に入れる。
- mule/parse は、raw-sources にある source を次のように扱う。
  - 属性はすべて `PLit` (書いたままの文字列) にする。
  - 子要素の式は集めない。
  - `${...}` の置き換えは、要素を読んだ時点で済んでいる。
- その source の式は、コネクタが `dw/engine` の `compile-with` (自分の束縛の名前の列) と `eval-compiled` で評価する。
  - 例: http は `["payload" "attributes" "item" "watermark"]` を使う。
  - DW のモジュールは SrcCall の `res` (アプリの資源) から読む。
- これらの式は解析の段で検査しない。コンパイルの失敗は、ポーリングのたびの失敗として出る (`Invalid expression '..' at HTTP Polling Source - ..`)。
  - 実 Mule では、source の開始の時点 (validateExpressions) で失敗する。この違いは docs/compat/deviations.md に書く。

## 理由

- 束縛を m/BINDINGS に足して rt/engine の `inputs` を広げる案は採らない。
  - 束縛の数は、コンパイル済みの式 (事前コンパイルの表を含む) の入力の並びとして固定されている。
  - 1 つのコネクタの source のために、全部の式の入力を変えることになる。
- 実 Mule と同じく、この式を解釈するのはコネクタの責任とする。rt はコネクタを知らないまま (ADR 081) で済む。
