# 110 — `import .. from jsonschema!a::b::C` は JSON Schema を DataWeave の型の宣言に訳して、ふつうのモジュールとして読む

状態: **採用** (2026-11-01)

## 実 Mule 4.11.3 の挙動 (DW 2.11 の文書と test/fixtures/apps/dw-type-reuse の記録)

- `import * from jsonschema!example::schema::Person` は、クラスパス (src/main/resources) の `example/schema/Person.json` を読む。
  名前を選ぶ `import address from ..`、`import address as Addr from ..` も書ける。
- 最上位のスキーマが `Root`、`definitions` と `$defs` の各項目がその名前の型になり、`$ref` はその型を指す。
- 対応: string → String、integer・number → Number、boolean → Boolean、null → Null、array → Array (要素の型は確かめない。`tags: [1]` も
  合う)、object → オブジェクトの型 (required に無いものは `?`、`additionalProperties: false` は閉じた `{| |}`)、enum と const → 値の型
  (の和)、`type` の並び・anyOf・oneOf → 和、allOf → 積。
- format、minimum などの数の制限、pattern は見ない (`age: -5` も合う)。
- 型は実行時に効く (`is`、`match` の `case is`、`as`、型を書いた引数。合わない時の文言はふつうの型と同じ)。

## 決定

- モジュールの名前から読むファイルへの写しは `eng/module-path` 1 か所にする (`jsonschema!` → `.json`、`xmlschema!` → `.xsd`、
  ほかは `.dwl`)。アプリ、`mulay dw`、dw::Runtime の run の fs、HTTP の polling の読み手はすべてこれを使う。
- `jsonschema!` のモジュールを読んだら `mulay.dw.schematype/json-schema-module` で DataWeave の型の宣言 (`type Root = ..`) の文に訳し、
  あとはふつうのモジュールと同じく構文解析・解決する。文書が「次の型を宣言したのと同じ」と書く訳をそのまま作るので、型の検査・
  誤りの文言・名前の import は DataWeave の型の仕組みをそのまま使う。訳せない JSON は "Module <名前>: <理由>" の誤り。
- 名前の import (`import T from m`、`import T as U from m`) は、関数と変数に加えて型も受ける (U は T の別名の型)。前はユーザーの
  モジュールの型を名前で import できなかった。
- `java!` は JVM が無いので作らない (docs/compat/deviations.md)。`xmlschema!` は未実装。

## 場所

- `mulay.dw.schematype`、`mulay.dw.engine/module-path`・`module-source`、`mulay.dw.resolve` の `register-user-import`
