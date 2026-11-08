# 112 — APIkit は pom の mule-apikit-module の版に従う: 1.13 以上の OpenAPI 3.1 は別の検証器 (json-sKema の文言)

状態: **採用** (2026-11-02、ユーザーの判断)

## 実 Mule 4.11.3 の挙動 (APIkit 1.12.6 と 1.13.4 で同じ 8 アプリを記録して比べた)

- RAML、OpenAPI 3.0、scaffold、console は 1.12.6 と 1.13.4 で同じ。違うのは OpenAPI 3.1 の検証だけ。
- 1.12.6: 3.1 の `const` で配備しない。誤りの文言は 3.0 と同じ (everit: "is not a valid enum value"、"expected type: String, found: Integer")。
- 1.13.4 (test/fixtures/apps/apikit-oas31-v113、55 要求):
  - `const` を受け付ける (enum と同じ "the instance is not equal to any enum values")。
  - 文言: "expected type: string, actual: integer"、"required properties are missing: a"、"/x false schema always fails"、
    "N is lower than minimum M"、"... lower than or equal to minimum"、"actual string length N exceeds maxLength M"、
    "instance value did not match pattern P"、"instance does not match format 'date'"、"expected minimum items: M, found only N"、
    "the same array element occurs at positions i, j"、"negated subschema did not fail"、壊れた JSON は "Invalid json value was provided"。
  - 誤りはスキーマのキーワードの順に並ぶ (additionalProperties・required・properties を書いた順)。anyOf・oneOf が全部外れたら各枝の誤りを順に。
  - 型の並び `type: [integer, "null"]` は型ごとの anyOf になり、その型に効く制限 (minimum など) はその枝に入る
    (`[integer, null]` で minimum: 3 に 2 を送ると "2 is lower than minimum 3" と "expected type: null, actual: integer")。
  - 数の制限の値は、型が integer なら整数 (2.5 は 2 に切り捨て)、ほかは Java の double の書き方 (1 → "1.0")。
  - 引数 (path・query・header) も同じ検証器。ただし型に合わない値は前の文言 ("expected type: Integer, found: String")、
    型の無い引数 (enum だけ) は確かめない (`sort=up` が通る)。

## 決定

- アプリの pom の依存 (ADR 056、App の deps) から mule-apikit-module の版を読み、OpenAPI 3.1 で 1.13 以上なら新しい検証にする。
  版が分からない (pom が無い) ときは 1.12 の動き。
- AMF がする変換 (型の並び → anyOf、const → enum、数の制限の型) は `mulay.conn.amf31` に、検証そのものは汎用の
  `mulay.lib.jsonskema` (draft 2020-12、キーワードの順に評価) に分ける。仕様の文書は読んだ時に 1 度だけ変換する (Api の skema)。
- 1.12 の動き (`mulay.lib.jsonschema`) はそのまま残す (アプリが 1.12 を指すなら実 Mule もそう動く)。

## 未確認 (docs/todo.md)

- oneOf で 2 つ以上が合う時の文言、if/then/else、dependentRequired、form (x-www-form-urlencoded) の本文。

## 場所

- src/mulay/conn/amf31.clay、src/mulay/lib/jsonskema.clay、src/mulay/conn/apispec.clay (parse-oas の apikit・version-at-least?)、
  src/mulay/conn/apikit.clay (apikit-version、validate-json-skema、param-problem)

## 追記 (2026-11-02): AMF が落とす required

- 1.12.6 (OAS 3.0・3.1 とも) は、`type` も `properties` も持たないスキーマ (AMF が AnyShape と読むもの) の `required` を検査しない。
  anyOf・oneOf の枝の `{required: [a]}` は何にでも合う枝になる (anyOf はいつも通り、oneOf は "#: 2 subschemas matched instead of one")。
  `type: object` か `properties` があれば検査する。apikit-oas と apikit-oas31 の /probes・/transfers に記録した。
- mulay は 1.12 の経路で仕様を読む時に、スキーマの中のその `required` (配列) を落とす (`apispec/amf-doc`)。検証器 (lib/jsonschema) は
  JSON Schema のままにして、AMF の変換は仕様を読む側に置く (1.13 の `conn/amf31` と同じ分け方)。example・default・enum の中は触らない。
- 1.13.4 で同じかは記録していない。
