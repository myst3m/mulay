# DataWeave のデータ形式と reader / writer プロパティ

実 Mule 4.11.3 同梱の DataWeave 2.11.2 で `dw::Runtime::dataFormatsDescriptor()` を評価した結果を一次資料とし、
型 (Type) は公式ドキュメント (docs-dataweave v2.11 の `dataweave-formats-*.adoc`) の表から補った。
既定値の列は実 DW の値。ドキュメントの既定値と食い違うものは「doc 既定値」の列に書いた。

- 既定値 `(なし)` は実 DW が `None` (未設定) を返すもの。`encoding` の `(なし)` は、入力/出力の既定の文字コード (多くは UTF-8) に従う意味。
- プロパティは `output application/csv separator=";"` のように output / input 指示子に書くか、Mule の `outputMimeType` の MIME パラメータで渡す。
- `read(x, mime, props)` は mime の文字列の引数 (`; separator=;`、`; charset=..`、multipart の `; boundary=..`) を使わず、第 3 引数だけを
  プロパティにする (実 DW 2.11.2)。失敗の文言には mime を渡されたまま出し (`'json'`、`'application/json; charset=UTF-16'`)、入力の
  文字列は 25 文字を超えると先頭の 23 文字に `...` を付ける。multipart は、String を読むときは boundary のプロパティが要り
  ("'boundary' configuration property is missing.")、Binary なら中身から見つける (`test/fixtures/dw/mime_test/read-*`)。
- 例は `test/fixtures/dw/docs/formats/` (ドキュメントの各形式ページ由来) にある。

## mulay の対応状況

全プロパティを実 DW と比べた結果 (`test/fixtures/dw/options_test/`、331 ケース。期待値は実 DW の出力。各形式の
プロパティを 1 つずつ変え、境界値と不正な値も入れた)。

- **値の検査** (実 DW と同じ文言):
  - `output` 指示子の値は型を厳密に検査する (`Option `indent` expects 'Boolean' but was 'String'`)。
  - `read()` / `write()` の引数と、`input` や MIME パラメータの文字列は緩く読む。Boolean は `"true"` だけが true でそれ以外は false、
    String は文字列にし、Number は数字の文字列も受ける (読めなければ `For input string: "x"`)。
  - `bufferSize` は 8 以上 (`Number 1 is out of valid range. Min Value: 8 `)。
  - `encoding` が知らない文字コードなら `Charset bogus is not supported` (NDJSON は Java の例外文言)。
  - `writeDeclaredNamespaces` は `All`、`regex:<正規表現>` (URI に全体一致)、`ids:<接頭辞,..>` だけ。
  - CSV の `separator` が空なら `Value for `separator` is not valid.`。
- **出力に効くもの**は、reader と writer の全プロパティを実装している。ほかに効くものを挙げる。
  - XML reader の `maxAttributeSize` (属性値の文字数)。
  - XML reader の `nullValueOn` (`blank` / `empty`。それ以外は null にしない)。
  - XML reader の `externalEntities` (`supportDtd=true` との併用で `file://` の実体を読む)。
  - XML writer の `defaultNamespace`。
  - XML writer の `writeDeclaredNamespaces`。
  - `urlencoded` の `encoding`。
  - DW writer の `maxCollectionSize`。
- **指定を受けるだけで出力に影響しないもの**は、実 DW でも出力は変わらない (確認済み)。
  - `streaming`、`optimizeFor`、`indexedReader`、`collectionPath` (XML reader)。
  - `bufferSize`、`deferred`。
  - DW reader の `privileges`、`externalResources`、`javaModule`。
- **eventstream** (`text/event-stream`、SSE): 実 DW の event-stream-module の EventStream.dwl を移した
  (`fmt/eventstream`、`test/fixtures/dw/eventstream_test/` 58 ケース)。reader は `:` のコメント行を飛ばし、
  空行でイベントを区切る。最初の `:` が 2 文字目 (`a: 1`) だと、名前と値に分けず行全体が名前になる。終わりの空行が無いと最後の
  イベントは出ない。writer は Object の Array を `名前: 値` の行にし、値の `\n` は空白にする。
- **protobuf** (`application/protobuf`、`application/x-protobuf`): 実 DW の protobuf-module 2.11.2 (protobuf-java の DynamicMessage) と
  同じ規則 (`fmt/protobuf`、ワイヤ形式と記述子は `lib/protobuf`、`test/fixtures/dw/protobuf_test/` 58 ケース。下の protobuf の節)。
- **未対応の形式** (形式 ID は認識するが、読み書きは "not supported by mulay yet" で失敗する): avro、excel (xlsx)、flatfile、dwb。

## 形式の一覧

| ID | 既定の MIME | 受け付ける MIME | 拡張子 | バイナリ | 既定の文字コード | reader | writer |
|---|---|---|---|---|---|---|---|
| `avro` | `application/avro` | `application/avro` | .avro | no |  | 1 | 3 |
| `json` | `application/json` | `*/json`, `*/*+json` | .json | no | UTF-8 | 1 | 7 |
| `xml` | `application/xml` | `*/xml`, `*/*+xml` | .xml | no |  | 9 | 14 |
| `csv` | `application/csv` | `*/csv` | .csv | no |  | 8 | 13 |
| `binary` | `application/octet-stream` | `application/octet-stream`, `application/x-binary` | .bin | yes |  | 0 | 2 |
| `text` | `text/plain` | `text/plain` | .txt | no |  | 0 | 3 |
| `urlencoded` | `application/x-www-form-urlencoded` | `application/x-www-form-urlencoded` | .urlencoded | no |  | 0 | 3 |
| `multipart` | `multipart/form-data` | `multipart/*` | .multipart | yes |  | 2 | 3 |
| `properties` | `text/x-java-properties` | `*/x-java-properties`, `*/properties` | .properties | no |  | 0 | 3 |
| `dwb` | `application/dwb` | `application/dwb` | .dwb | no |  | 1 | 3 |
| `excel` | `application/xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `application/xlsx` | .xlsx | yes |  | 8 | 8 |
| `flatfile` | `application/flatfile` | `*/flatfile` | .flatfile .copybook | no |  | 13 | 15 |
| `java` | `application/java` | `*/java` |  | no |  | 0 | 2 |
| `protobuf` | `application/protobuf` | `application/protobuf`, `application/x-protobuf` | .protobuf .pb | no |  | 4 | 4 |
| `dw` | `application/dw` | `*/dw` | .dwl | no | UTF-8 | 4 | 6 |
| `yaml` | `application/yaml` | `application/yaml`, `text/yaml`, `application/x-yaml`, `text/x-yaml` | .yml .yaml | no | UTF-8 | 1 | 5 |
| `eventstream` | `text/event-stream` | `text/event-stream` | .sse .eventstream | no |  | 0 | 2 |
| `ndjson` | `application/x-ndjson` | `application/x-ndjson`, `application/x-ldjson` | .ndjson .ldjson .ldj .jsonl | no |  | 2 | 5 |

## avro (`application/avro`)

### reader プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `schemaUrl` | `String` | `""` |  | no |  | The URL for the Avro schema. |

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `schemaUrl` | `String` | `""` |  | no |  | The URL for the Avro schema. |
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |

## json (`application/json`)

### reader プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `streaming` | `Boolean` | `false` | `true`, `false` | yes |  | Streams input when set to `true`. |

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `writeAttributes` | `Boolean` | `false` | `true`, `false` | yes |  | Converts attributes of a key into child key-value pairs of that key. |
| `indent` | `Boolean` | `true` | `true`, `false` | yes |  | Write indented output for better readability by default, or compress output into a single line when set to `false`. |
| `encoding` | `String` | `UTF-8` |  | yes |  | The encoding to use for the output, such as UTF-8. |
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `skipNullOn` | `String` | (なし) | `"arrays"`, `"objects"`, `"everywhere"` | yes |  | Skips `null` values in the specified data structure. |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |
| `duplicateKeyAsArray` | `Boolean` | `false` | `true`, `false` | yes |  | Converts the values of duplicate keys in an object to a single array of values to the duplicated key. |

## xml (`application/xml`)

### reader プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `supportDtd` | `Boolean` | `false` | `true`, `false` | yes |  | Enable or disable DTD support. |
| `streaming` | `Boolean` | `false` | `true`, `false` | yes |  | Streams input when set to `true`. |
| `maxEntityCount` | `Number` | `1` |  | yes |  | Sets the maximum number of entity expansions. |
| `optimizeFor` | `String` | `speed` | `"speed"`, `"memory"` | yes |  | Configures the type of optimization for the XML parser to use. |
| `indexedReader` | `Boolean` | `true` | `true`, `false` | yes |  | Uses the indexed reader by default when reaching the threshold. |
| `maxAttributeSize` | `Number` | `-1` |  | yes |  | Sets the maximum number of characters accepted in an XML attribute. |
| `nullValueOn` | `String` | `blank` | `"empty"`, `"none"`, `"blank"` | yes |  | Indicates whether to read an element with empty or blank text as a `null` value. |
| `collectionPath` | `String` | `null` |  | yes |  | Sets the path to the location in the document where the collection is located. |
| `externalEntities` | `Boolean` | `false` | `true`, `false` | yes |  | Indicates whether to process external entities. |

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `writeDeclaration` | `Boolean` | `true` | `true`, `false` | yes |  | Writes the XML header declaration when set to `true`. |
| `indent` | `Boolean` | `true` | `true`, `false` | yes |  | Write indented output for better readability by default, or compress output into a single line when set to `false`. |
| `doubleQuoteInDeclaration` | `Boolean` | `false` | `true`, `false` | yes |  | Escapes double quotes in the XML declaration when set to `true`. |
| `encoding` | `String` | (なし) |  | yes |  | The encoding to use for the output, such as UTF-8. |
| `escapeGT` | `Boolean` | `false` | `true`, `false` | yes |  | Escapes '>' characters when set to `true`. |
| `defaultNamespace` | `String` | (なし) |  | yes |  | Specifies the default namespaces of the output XML. |
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `inlineCloseOn` | `String` | `empty` | `"empty"`, `"none"` | yes |  | Write an inline close tag, or explicitly open and close tags when the value is `null`. |
| `onInvalidChar` | `String` | (なし) | `"base64"`, `"ignore"`, `"none"` | yes |  |  |
| `writeNilOnNull` | `Boolean` | `false` | `true`, `false` | yes |  | Writes the `nil` attribute for a `null` value when this property is set to `true`. |
| `escapeCR` | `Boolean` | `false` | `true`, `false` | yes |  | Escapes `CR` characters when set to `true`. |
| `skipNullOn` | `String` | (なし) | `"elements"`, `"attributes"`, `"everywhere"` | yes |  | Skips `null` values in the specified data structure. |
| `writeDeclaredNamespaces` | `String` | (なし) |  | yes |  | Marks the namespaces to declare in the root element of the XML: * `All`: Write all declared namespaces in the root element. |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |

## csv (`application/csv`)

### reader プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `streaming` | `Boolean` | `false` | `true`, `false` | yes |  | Streams input when set to `true`. |
| `separator` | `String` | `,` |  | yes |  | Character that separates one field from another field. |
| `quote` | `String` | `"` |  | yes |  | Character to use for quotes. |
| `escape` | `String` | `\` |  | yes |  | Character to use for escaping special characters, such as separators or quotes. |
| `bodyStartLineNumber` | `Number` | `0` |  | yes |  | Line number on which the body starts. |
| `ignoreEmptyLine` | `Boolean` | `true` | `true`, `false` | yes |  | Indicates whether to ignore an empty line. |
| `header` | `Boolean` | `true` | `true`, `false` | yes |  | Indicates whether a CSV header is present. |
| `headerLineNumber` | `Number` | `0` |  | yes |  | Line number on which the CSV header is located. |

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `separator` | `String` | `,` |  | yes |  | Character that separates one field from another field. |
| `encoding` | `String` | (なし) |  | yes |  | The encoding to use for the output, such as UTF-8. |
| `quote` | `String` | `"` |  | yes |  | Character to use for quotes. |
| `escape` | `String` | `\` |  | yes |  | Character to use for escaping special characters, such as separators or quotes. |
| `lineSeparator` | `String` | `\n` |  | yes | `New Line` | Line separator to use when writing CSV, for example, `"\r\n"`. |
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `bodyStartLineNumber` | `Number` | `0` |  | yes |  | Line number on which the body starts. |
| `ignoreEmptyLine` | `Boolean` | `true` | `true`, `false` | yes |  | Indicates whether to ignore an empty line. |
| `header` | `Boolean` | `true` | `true`, `false` | yes |  | Indicates whether a CSV header is present. |
| `quoteHeader` | `Boolean` | `false` | `true`, `false` | yes |  | Quotes header values when set to `true`. |
| `headerLineNumber` | `Number` | `0` |  | yes |  | Line number on which the CSV header is located. |
| `quoteValues` | `Boolean` | `false` | `true`, `false` | yes |  | Quotes every value when set to `true`, including values that contain special characters. |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |

## binary (`application/octet-stream`)

reader プロパティ: なし

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |

## text (`text/plain`)

reader プロパティ: なし

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `encoding` | `String` | (なし) |  | yes |  | The encoding to use for the output, such as UTF-8. |
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |

## urlencoded (`application/x-www-form-urlencoded`)

reader プロパティ: なし

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `encoding` | `String` | (なし) |  | yes |  | The encoding to use for the output, such as UTF-8. |
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |

## multipart (`multipart/form-data`)

### reader プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `boundary` | `String` | (なし) |  | yes |  | The multipart `boundary` value, a string to delimit parts. |
| `defaultContentType` | `String` | `application/octet-stream` |  | yes |  | Sets the default Content-Type to use on parts of the `multipart/*` format. |

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `boundary` | `String` | (なし) |  | yes |  | The multipart `boundary` value, a string to delimit parts. |
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |

## properties (`text/x-java-properties`)

reader プロパティ: なし

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `encoding` | `String` | (なし) |  | yes |  | The encoding to use for the output, such as UTF-8. |
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |

## dwb (`application/dwb`)

### reader プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `indexedReader` | `Boolean` | `true` | `true`, `false` | yes |  | Uses the indexed reader by default when reaching the threshold. |

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |
| `writeIndex` | `Boolean` | `false` | `true`, `false` | yes |  | If it should add the token and hierarchical index at the end to avoid parsing again when this is read |

## excel (`application/xlsx`)

### reader プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `zipBombCheck` | `Boolean` | `true` | `true`, `false` | yes |  | Turns off the zip bomb (decompression bomb) check when set to `false`. |
| `streaming` | `Boolean` | `false` | `true`, `false` | yes |  | Streams input when set to `true`. |
| `tableLimit` | `String` | `Unbounded` |  | yes |  | Position of the last column in each row. |
| `maxEntrySize` | `Number` | (なし) |  | yes |  | Sets the maximum number of bytes a single entry in a ZIP file can have. |
| `minInflateRatio` | `Number` | (なし) |  | yes |  | Sets the ratio between de- and inflated bytes to detect zip bomb. |
| `ignoreEmptyLine` | `Boolean` | `true` | `true`, `false` | yes |  | Ignores an empty line by default. |
| `header` | `Boolean` | `true` | `true`, `false` | yes |  | Indicates whether the first line of the output contains header field names. |
| `tableOffset` | `String` | (なし) |  | yes |  | Sets the position of the first cell. |

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `zipBombCheck` | `Boolean` | `true` | `true`, `false` | yes |  | Turns off the zip bomb (decompression bomb) check when set to `false`. |
| `maxEntrySize` | `Number` | (なし) |  | yes |  | Sets the maximum number of bytes a single entry in a ZIP file can have. |
| `minInflateRatio` | `Number` | (なし) |  | yes |  | Sets the ratio between de- and inflated bytes to detect zip bomb. |
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `ignoreEmptyLine` | `Boolean` | `true` | `true`, `false` | yes |  | Ignores an empty line by default. |
| `header` | `Boolean` | `true` | `true`, `false` | yes |  | Indicates whether the first line of the output contains header field names. |
| `tableOffset` | `String` | (なし) |  | yes |  | Sets the position of the first cell. |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |

## flatfile (`application/flatfile`)

### reader プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `allowLenientWithBinaryNotEndElement` | `Boolean` | `false` | `true`, `false` | yes |  | When the schema contains elements of type Binary or Packed, the `lenient` option does not allow short records, regardless of the last element's format type. |
| `zonedDecimalStrict` | `Boolean` | `false` | `true`, `false` | yes |  | For COBOL copybook, uses the 'strict' ASCII form of sign encoding for zoned decimal values. |
| `structureIdent` | `String` | (なし) |  | yes |  | Structure identifier in the schema for flat file schemas. |
| `schemaPath` | `String` | (なし) |  | no |  | Path to the schema definition. |
| `missingValues` | `String` | (なし) | `"none"`, `"spaces"`, `"zeroes"`, `"nulls"` | yes |  | Fill character used to represent missing values. |
| `segmentIdent` | `String` | (なし) |  | yes |  | Segment identifier in the schema for fixed-width or COBOL copybook schemas. |
| `recordParsing` | `String` | `strict` | `"strict"`, `"lenient"`, `"noTerminator"`, `"singleRecord"` | yes |  | Specifies the expected type of separation between lines or records: * `strict`: Line break is expected at exact end of each record. |
| `enforceRequires` | `Boolean` | `false` | `true`, `false` | yes |  | Produces an error when set to `true` if a required value is missing. |
| `notTruncateDependingOnSubjectNotPresent` | `Boolean` | `false` | `true`, `false` | yes |  | Fills the entire group when the DEPENDING ON subject is not present. |
| `useMissCharAsDefaultForFill` | `Boolean` | `false` | `true`, `false` | yes |  | By default, the flat file reader and writer use spaces for missing characters and ignore the setting of the `missingValues` property. |
| `substituteCharacterAsMissingValue` | `Boolean` | `false` | `true`, `false` | yes |  | If set to `true` and if the `missingValues` property is set to `none`, with `useMissCharAsDefaultForFill` is set to `true`, the flat file parser handles the `0x1A` (SUB) character as the missing value. |
| `truncateDependingOn` | `Boolean` | `false` | `true`, `false` | yes |  | For COBOL copybook, truncates DEPENDING ON values to the length used. |
| `retainEmptyStringFieldsOnParsing` | `Boolean` | `false` | `true`, `false` | yes |  | Allow parsing behavior to keep missing string value fields with a default value in the output map |

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `zonedDecimalStrict` | `Boolean` | `false` | `true`, `false` | yes |  | For COBOL copybook, uses the 'strict' ASCII form of sign encoding for zoned decimal values. |
| `structureIdent` | `String` | (なし) |  | yes |  | Structure identifier in the schema for flat file schemas. |
| `schemaPath` | `String` | (なし) |  | no |  | Path to the schema definition. |
| `missingValues` | `String` | (なし) | `"none"`, `"spaces"`, `"zeroes"`, `"nulls"` | yes |  | Fill character used to represent missing values. |
| `segmentIdent` | `String` | (なし) |  | yes |  | Segment identifier in the schema for fixed-width or COBOL copybook schemas. |
| `fillRedefinesByMaxLength` | `Boolean` | `false` | `true`, `false` | yes |  | If set to `true`, the flat file module fills the `Redefines` components that are considered to be missing values up to the maximum number of characters set in the `maxLength` parameter. |
| `encoding` | `String` | (なし) |  | yes |  | The encoding to use for the output, such as UTF-8. |
| `trimValues` | `Boolean` | `false` | `true`, `false` | yes |  | Trim values that are longer than the width of a field. |
| `enforceRequires` | `Boolean` | `false` | `true`, `false` | yes |  | Produces an error when set to `true` if a required value is missing. |
| `recordTerminator` | `String` | (なし) | `"lf"`, `"cr"`, `"crlf"`, `"none"` | yes |  | Line break for a record separator. |
| `notTruncateDependingOnSubjectNotPresent` | `Boolean` | `false` | `true`, `false` | yes |  | Fills the entire group when the DEPENDING ON subject is not present. |
| `useMissCharAsDefaultForFill` | `Boolean` | `false` | `true`, `false` | yes |  | By default, the flat file reader and writer use spaces for missing characters and ignore the setting of the `missingValues` property. |
| `truncateDependingOn` | `Boolean` | `false` | `true`, `false` | yes |  | For COBOL copybook, truncates DEPENDING ON values to the length used. |
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |

## java (`application/java`)

reader プロパティ: なし

外から来たバイト列 (`Content-Type: application/java` の HTTP の本文など) は、実 Mule と同じく Binary として読む
(`^class` は ManagedCursorStreamProvider、`^raw` は受けたバイト列。core-http-request の /java/read)。

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `duplicateKeyAsArray` | `Boolean` | `false` | `true`, `false` | yes |  | Converts the values of duplicate keys in an object to a single array of values to the duplicated key. |
| `writeAttributes` | `Boolean` | `false` | `true`, `false` | yes |  | Converts attributes of a key into child key-value pairs of that key. |

## protobuf (`application/protobuf`)

mulay の規則 (実 DW 2.11.2 の protobuf-module を逆コンパイルして読み、golden で確かめた):
- 記述子 (`descriptorUrl`) は protoc の `--descriptor_set_out` で作った FileDescriptorSet (`.proto` は読めない)。`classpath://`、
  `file://`、そのままのパス (まずアプリのクラスパス、無ければファイル) を読み、URL ごとに覚える。`messageType` は記述子の最上位のメッセージだけから探す
  (入れ子の型は "Message Type .. not found on given descriptor.")。どちらかが無ければ "Missing required ProtoBuf setting `..`."。
- 読み: フィールドは記述子での宣言の順。単数のフィールドは値が無くても既定値で出す (メッセージ型は既定のインスタンスを変換したもの)。
  ただし oneof (proto3 の optional を含む) は値があるときだけ。repeated は要素ごとに同じキーを繰り返し (空なら出さない)、map は
  `{キーの文字: 値}` (空でも `{}`)。数は Java の Integer / Long / Float / Double をいったん double にした Number (int64 が
  `-9.0E+9`、uint32 と uint64 は符号付きで読む。NaN と無限大は `null as Null {NaN: true[, inf: ..]}`)。enum は
  `"名前" as String {protobufEnumIndex: n}` (知らない番号は `"-UNRECOGNIZED"`)。知らないフィールドは最後に
  `"-番号": 値 as .. {wireType: "Varint" | "32Bit" | "64Bit" | "LengthDelimited" | "Group"}`。well-known types: Timestamp は
  LocalDateTime (UTC)、Duration は Period、ラッパーはその値、Struct は Object、Value はその値 (どれも無ければ失敗)、ListValue は
  Array、Empty は `{}`、NullValue は null (Any と FieldMask はふつうのメッセージ)。
- 書き: オブジェクトのキーで記述子のフィールドを探し (`"-番号"` は知らないフィールド)、フィールド番号の順に書く。proto3 の存在を
  持たないフィールドの既定値は書かない。int32 などは Number を Java の intValue / longValue で切り詰める (3000000000 は負の int32、
  1.5 は 1)。文字列や配列は数にしない ("Can't write as an Int, while writing ProtoBuf at ..")。map のキーは文字から数などに読み直す
  ("Can't parse as an Int")。同じ単数のフィールドが 2 度、oneof の 2 つ目、知らない名前、enum の知らない名前は失敗。required が
  欠ければ "com.google.protobuf.UninitializedMessageException - Message missing required fields: ..".
- payload や変数を読むときの失敗は、文言の後に `\nTrace:\n  at main (Unknown), while reading `payload` as ProtoBuf.\nTrace:\n  at main (Unknown)`
  が付く (実 Mule 4.11.3、test/fixtures/apps/grpc-client)。`read(..)` の失敗は "Exception while reading 'Binary Content' .." で包む。
- 失敗の位置: 実 DW は ", while writing ProtoBuf at " の後に位置を出す。mulay は位置を出さない (null の値は実 DW と同じく
  ", while writing ProtoBuf.")。

### reader プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |
| `descriptorUrl` | `String` | `""` |  | no |  | The URL for the ProtoBuf descriptor. |
| `messageType` | `String` | `null` |  | no |  | The message type's full name taken from the given descriptor, including the package where it's located. |

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |
| `descriptorUrl` | `String` | `""` |  | no |  | The URL for the ProtoBuf descriptor. |
| `messageType` | `String` | `null` |  | no |  | The message type's full name taken from the given descriptor, including the package where it's located. |

## dw (`application/dw`)

### reader プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `privileges` | `String` | `""` |  | yes |  | Accepts a comma-separated list of privileges to use in the format, such as `'Resources,Properties'`. |
| `onlyData` | `Boolean` | `false` | `true`, `false` | yes |  | Handles only data and not other types of content, such as functions, when set to `true`. |
| `externalResources` | `Boolean` | `false` | `true`, `false` | yes |  | Enables the `readUrl` to read external entities. |
| `javaModule` | `Boolean` | `false` | `true`, `false` | yes |  | Enables Java module functions to load. |

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `indent` | `String` | `  ` |  | yes |  | String to use for indenting. |
| `ignoreSchema` | `Boolean` | `false` | `true`, `false` | yes |  | Ignores the schema when set to `true`. |
| `onlyData` | `Boolean` | `true` | `true`, `false` | yes |  | Handles only data and not other types of content, such as functions, when set to `true`. |
| `maxCollectionSize` | `Number` | `-1` |  | yes |  | Maximum number of elements allowed in an array or an object. |
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |

## yaml (`application/yaml`)

### reader プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `maxEntityCount` | `Number` | `1` |  | yes |  | Sets the maximum number of entity expansions. |

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `writeDeclaration` | `Boolean` | `true` | `true`, `false` | yes |  | Indicates whether to write the header declaration or not. |
| `encoding` | `String` | `UTF-8` |  | yes |  | The encoding to use for the output, such as UTF-8. |
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `skipNullOn` | `String` | (なし) | `"arrays"`, `"objects"`, `"everywhere"` | yes |  | Skips `null` values in the specified data structure. |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |

## eventstream (`text/event-stream`)

reader プロパティ: なし

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |

## ndjson (`application/x-ndjson`)

### reader プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `ignoreEmptyLine` | `Boolean` | `true` | `true`, `false` | yes |  |  |
| `skipInvalid` | `Boolean` | `false` | `true`, `false` | yes |  |  |

### writer プロパティ

| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |
|---|---|---|---|---|---|---|
| `writeAttributes` | `Boolean` | `false` | `true`, `false` | yes |  |  |
| `encoding` | `String` | `UTF-8` |  | yes |  |  |
| `bufferSize` | `Number` | `8192` |  | yes |  | Size of the buffer writer, in bytes. |
| `skipNullOn` | `String` | `null` | `"arrays"`, `"objects"`, `"everywhere"` | yes |  |  |
| `deferred` | `Boolean` | `false` | `true`, `false` | yes |  | Generates the output as a data stream when set to `true`, and defers the script's execution until the generated content is consumed. |

