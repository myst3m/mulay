# ADR 087: Avro のバイナリ符号化を lib/avro に置く

日付: 2026-10-22。状態: 決定。

## 背景

- Salesforce の Pub/Sub API は、イベントの本体を Avro のバイナリで返し (writer schema は GetSchema で別に取る)、発行するときも topic のスキーマで符号化した Avro のバイナリを受ける。
  Pub/Sub のコネクタ (別に書く) と、将来の DW の `application/avro` (schemaUrl を取る reader / writer、docs/todo.md) が使う。
- 正解は Apache Avro Java 1.11.5 の GenericDatumWriter / GenericDatumReader / Schema.Parser。
  `tools/gen-avro-golden.java` (Java 17) が符号化したバイト列、読み戻した値、失敗の文言、スキーマの正規形を test/avro/avro_golden_data.clay に書く。
- lib の層に置く (dw / mule / rt / conn に依存しない)。依存は lib の yaml (JSON の読み)、dec (Java の Float.toString と同じ文字列化)、ieee (float32) だけ。

## 決定

### スキーマ

- `Schema` は節点の表 (`Vec(SNode)`) と根の番号と完全名の表からなる。
  - items、values、union の枝、フィールドの型はすべて節点の番号 (Int)。
  - 参照カウントで GC が無い Clay では自己参照の record を値の入れ子にできないため。
  - record は名前をフィールドより先に登録する。自分への参照は通り、前方参照は Java と同じく "Undefined name" になる。
- 名前の解決は Avro の仕様と Java に合わせる: 名前にドットがあれば完全名 (namespace 属性は無視)、無ければ namespace 属性、それも無ければ囲んでいる record の namespace。
  参照は囲みの namespace、次に名前空間なしの順に探す。プリミティブの名前が先。
- `parse-schema` の失敗の文言は Java の SchemaParseException などと同じ (Undefined name、Can't redefine、Illegal character in、Duplicate in union、Nested union、Duplicate field、Invalid default for field、Record has no fields など)。
  - default は Java 1.11 と同じく検査する (union は先頭の枝で。`["string","null"]` に `null` は不可)。
  - doc、aliases、order、logicalType などの属性は節点とフィールドに文字のまま残す。
    使うのは `schema->json` (Java の `Schema.toString()` と同じ文字列) だけ。値の読み書きには使わない。logicalType は見ない (基底の型で読み書きする)。
- JSON の読みは lib/yaml を使う。JSON でない入力 (YAML として読めるもの) も通すことがあり、構文の誤りの文言は Jackson のものと違う。

### 値

`AVal` は ANull、ABool、AInt、ALong、AFloat、ADouble、ABytes、AStr、ARec、AEnum、AArr、AMap、AFixed。

- ARec、AEnum、AFixed は完全名を持つ。union の枝は Java の `GenericData.resolveUnion` と同じく、値から決まる名前で選ぶため (null は "null"、AInt は "int"、record・enum・fixed は完全名、AArr は "array"、AMap は "map")。
- ARec のフィールドは名前で引く (名前の列と値の列を持つ。順序どおりなら位置で引き当てる)。無いフィールドは null として扱う (Java の未設定のフィールドと同じ)。
- AMap は書いた順の組。復号では Java の LinkedHashMap と同じに、同じキーが重なれば最初の位置に最後の値を入れる。
- 文字列と bytes はバイト列のまま (UTF-8 の検査をしない。Avro の Utf8 と同じ)。

### 復号 (`decode schema bytes pos` → 値、終わりの位置、エラー)

- GenericDatumReader (reader と writer が同じスキーマ)。block の負の count (続くバイト数つき) を読む。末尾の余りは読まない (終わりの位置を返すので呼び出し側が見る)。
- int は 32 ビットで巻き戻る (5 バイト目の上位ビットは捨てる)。6 バイト目が続くなら "Invalid int encoding"、long の 11 バイト目は "Invalid long encoding"。boolean は 1 以外はすべて false。
- 失敗の文言は Java と同じ: "Index 2 out of bounds for length 2" (union と enum の番号)、"Malformed data. Length is negative: -1"、"Cannot read collections larger than 2147483639 items in Java library"。
  入力が足りないときは Java の EOFException (文言が null) の代わりに "Unexpected end of Avro data" にする。
- abort しない。長さは `長さ > 残り` で調べる (`位置 + 長さ` はあふれて負になる)。
  - block の count が残りのバイト数を超える入力は、0 バイトの要素 (null、空の record など) でなければ入力の不足にする。0 バイトの要素は合計 100 万個まで。
  - 入れ子は 1000 段まで ("Avro value is nested too deeply")。バイトを食わない自己参照 (`R {r: R}`) の暴走を止める。

### 符号化 (`encode schema value` → バイト列、エラー)

- GenericDatumWriter。array と map は 1 つの block (count、要素、0)、空は 0 だけ。
- 数値は union の外では Java の `Number.xValue()` と同じに変換する: long から int は下位 32 ビット、double から int / long は飽和 (NaN は 0)、int / long から float は丸め、float から double は厳密。
  union の中では昇格しない (AInt は int の枝にだけ当たり、`["null","long"]` に AInt を入れると失敗する。Java と同じ)。
- double の NaN はビットをそのまま書く (Java の doubleToRawLongBits)。float の NaN は 0x7fc00000 にそろう (Clay の Float は double のため、float の NaN のペイロードは持てない。復号も同じ)。
- 型の不一致や null の失敗の文言は Avro 1.11.5 と同じ。`tools/gen-avro-golden.java` の ECASES (84 件) で確かめている。
  - "null value for (non-nullable) string at R.a"
  - "value x (a java.lang.String) cannot be cast to expected type int at R.c[0]"
  - enum は "value null is not a E at ..."
  - fixed が短いときは "arraycopy: last source index 4 out of bounds for byte[2]"
  - "at" の後の path は、根が record なら短い名前 (R)、array と map ならその型の書き方 (`List<int>`、`Map<String, long>`、union は `[null, int]`)。
    要素は `[1]`、map のキーは `["k"]`、union の枝は `[Q]` (array と map の枝は `[array]`、`[map]`)、record のフィールドは `.name`。
  - union に枝が無いときは "Not in union <union の JSON>: <値>"。
  - この失敗は、通ってきた record のフィールドごとに作り直される (Java の仕様)。一番外のフィールドが勝ち、"Not in union <そのフィールドの型の JSON>: <そのフィールドの値> (field=<名前>)" になる (path は付かない)。
- 値の文字列は Java の toString に合わせる (record は GenericData.toString の `{"a": "x", "b": null}`、string はそのまま、map は `{k=v}`、array は `[a, b]`)。
  - 文字の escape は GenericData の writeEscapedString と同じ (制御文字、U+007F〜U+009F、U+2000〜U+20FF を \uXXXX にする)。
  - Float / Double は Java の toString (dec の `float32->shortest-str` と `float->shortest-str`)。

### Java との違い (意図したもの)

- ARec は名前でフィールドを引く。Java は位置で引き、名前を見ない。別の record を入れても Java は位置が合えば書いてしまう。
- 値を作るのは呼び出し側。Java の「型の名前 (java.lang.Integer など)」の文言は、AVal の種類から決めた名前 (ABytes は java.nio.HeapByteBuffer、AArr は java.util.ArrayList、AMap は java.util.LinkedHashMap、ARec は GenericData$Record) を使う。
  Java の値が別のクラス (HashMap や Utf8) なら文言のクラス名は変わる。
- Java は map を HashMap で復号して順序が不定だが、mulay は書いた順を保つ。
- 未設定のフィールドの record を文字にするとき、Java は全フィールドを `null` で出す。mulay は ARec が持っているフィールドだけを出す。
- Java の `[B@1a2b3c` (byte[] の toString) は再現しない。
- Schema の失敗の文言のうち、JSON の構文の誤りは Jackson の文言ではない。
- Java は logicalType を LogicalTypes で検査して不正なら無視するが、mulay は属性として残すだけ。

### 対象外

- reader と writer のスキーマが違うときの解決 (schema resolution: 名前の別名、promotion、default での補い)。
- Avro object container file (.avro。header、sync marker、codec)。
- JSON の符号化 (Avro の JSON encoder / decoder)、Single-Object Encoding。
- DW の `application/avro` (docs/todo.md)。これを土台にして作れる。

## 結果

- test/avro: 137 件の値 (符号化したバイト列と読み戻した値が Java と一致、先頭からの切り詰めがすべて入力の不足の失敗)、84 件の符号化の失敗の文言、復号の失敗と非標準の符号化 (負の count、複数の block、長すぎる varint) 51 件、スキーマの解析 77 件 (失敗の文言と `toString()`)。
