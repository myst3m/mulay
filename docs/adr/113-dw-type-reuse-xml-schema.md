# 113 — `import .. from xmlschema!a::b::C` は XSD を、実 DW が作るのと同じ DataWeave の型の宣言に訳して読む

状態: **採用** (2026-11-02)

## 実 DW の挙動 (DW 2.11 の文書と、tools/dw-oracle/xsd-module で書き出した実 DW の訳)

実 DW (xmlschema-module) は XSD を DataWeave のモジュールに訳してから読む。tools/dw-oracle/xsd-module <クラスパス> <a::b::C> で
その訳を書き出せる (XmlSchemaModuleLoader と CodeGenerator を呼ぶ)。例 (test/fixtures/xsd/Order.xsd):

```
ns ns0 http://example.com/order
type ItemTypeDefinition = { ns0#ItemType: {- ns0#name: String, ns0#qty: Number -} }
type OrderTypeDefinition = { ns0#OrderType @(status: "NEW" | "DONE"): {- ns0#id: Number, ns0#item*: ItemTypeDefinition.ns0#ItemType, ns0#note?: String -} }
type StatusTypeDefinition = { ns0#StatusType: "NEW" | "DONE" }
type orderElementDefinition = {| ns0#order @(status: "NEW" | "DONE"): OrderTypeDefinition.ns0#OrderType |}
type Root = orderElementDefinition
```

- 名前: 大域の要素 x → `xElementDefinition` (閉じた 1 項目のオブジェクト)、名前の付いた complexType・simpleType X → 先頭を大文字にした
  `XDefinition` (`{ X: .. }` で包む)、`Root` は大域の要素の和。targetNamespace があれば `ns0`、大域の名前と qualified のものに付く。
- sequence → `{- -}`、all → `{ }`、choice → 1 項目の閉じたオブジェクトの和。minOccurs=0 → `?`、maxOccurs>1 → `*`。
  mixed は `"__text"*?: String` を先頭に、型の無い要素は `{- "__text"*?: String -}`、属性だけの型は `Object`。
- 属性は `@(..)` (use="required" 以外は `?`)。名前の付いた complexType を指す要素は、その型の属性をキーに付ける。
- complexContent の extension は基の項目と自分の項目を並べ、すべて `?` にする。simpleContent は `String`。
- simpleType: 文字列の enumeration は文字列の値の和、それ以外 (数の列挙、pattern、list、union) は基の型。組み込みの型は文書の表
  (数 → Number、date → LocalDateTime、dateTime → DateTime、time → Time、binary → Binary、ほか String)。
- 識別子でない名前と予約語は引用する。

## 決定

- `mulay.dw.xsdtype/xml-schema-module` が同じ型の宣言の文を作り、あとはふつうのモジュールとして解く (ADR 110 の jsonschema! と同じ)。
  test/eval/xsdtype_test が test/fixtures/xsd の 3 つの XSD について、実 DW の訳と宣言ごとに同じか確かめる (宣言の順は問わない)。
- 訳した型を正しく確かめるため、DataWeave の型の仕組みの方を実 DW に合わせた (別のコミット): 型のキーの名前空間と属性の型
  (object-type-ns-attrs.dwt)、後ろで宣言した型への参照 (forward-type-ref.dwt)、自分を指す型 (recursive-alias.dwt)。

## xs:import・xs:include (2026-11-02 追記)

- 実 DW は、import と include の schemaLocation を、その XSD の場所から解いたモジュール (`import xmlschema!schemas::common::Types`) にし、
  他のファイルの型は `<そのファイルの名前>::XDefinition.nsN#X` で指す。名前空間は自分のものが ns0、ほかは ns1 から。同じ名前空間の
  (include した) ファイルの型も宣言し、Root にはすべてのファイルの大域の要素が入る。mulay も同じに訳す (test/fixtures/xsd/schemas)。
- そのため DataWeave の ns の宣言をモジュールごとにした (別のコミット、test/eval/module_ns_test)。

## 未対応 (docs/todo.md)

- attributeGroup・group の参照、choice・sequence の入れ子の細部、substitutionGroup。

## 場所

- src/mulay/dw/xsdtype.clay、src/mulay/dw/engine.clay (module-source)、tools/dw-oracle/xsd-module と XsdModule.java、
  test/fixtures/apps/dw-xml-type-reuse (実 Mule で記録した 10 要求)
