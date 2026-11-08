# 097 — AppModel の入口の一覧と API 仕様のモデル

状態: **採用** (2026-10-24)

## 背景

livenote (ADR 091〜095) は、画面の単位を「入口」(POST /orders、毎晩 2:00、キューの受信) にする。ブラウザは RAML や
OpenAPI を読まない決まりなので、入口の一覧と仕様の操作 (メソッド・パス・引数・型・ファイルの中の位置) は mulay が
AppModel で返す。

## 決定

- **仕様のファイルの位置は `mulay.lib.youtline`** で出す。YAML の block 形式の字下げだけを見て、キーごとに
  キーの範囲 (`ks`〜`ke`、引用符を含む) と塊の範囲 (`bs` = キーの行の先頭、`be` = 塊の最後の中身の行の改行の後) と親を返す。
  - 値を読む `lib/yaml` とは分ける (値の木は位置を持たず、位置のために値の読み込みを重くしないため)。
  - 見ないもの: `|` と `>` の本文、複数行の `{ }`・`[ ]` の中、コメントと空行 (塊の終わりに数えない)、`---` で切れた前の文書。
    `- ` の要素はキー `-` として親に付き、その後ろのキーは要素の子になる。
  - JSON で書いた仕様 (flow 形式) はキーが出ないので、位置は無し (null) になる。
- **入口の一覧 (`entries`)** は `am/build` が読み込んだアプリ (`m/App` の source) から作る。受け口のあるフローごとに 1 つ、
  HTTP は allowedMethods のメソッドごとに 1 つ。
  - `{"kind":"http","flow","source","element","method","path"}`: path は listener-config の basePath と listener の path を
    つないだもの (プロパティは解決済み)。allowedMethods が無ければ method は `*`。
  - `{"kind":"scheduler",..,"schedule":{"frequencyMs":n}}` か `{"cron":..,"timeZone":..}` (timeUnit はミリ秒に直す)。
  - それ以外の受け口は `{"kind":"connector",..,"element":"vm:listener"}`。
- **API 仕様 (`apis`)** は `conn/apikit/api-models` が apikit:config ごとに作り、`am/with-apis` で AppModel に足す
  (仕様を読むのは conn の層なので、mule の `am/build` には入れない)。wasm の load (note) と `mulay inspect --json` が使う。
  - `{"config","file","format":"oas3"|"raml","error","operations":[..]}`。file はプロジェクトからの相対
    (`src/main/resources/` + api)。Exchange の `resource::..` などプロジェクトの外の仕様は "" で、位置は無し。
  - 操作は `{"method","path","key","block","params":[{"name","in","required","type","example"?}],"requestMediaTypes","responses","flow","implemented","responseExamples":[{"status","mediaType","body"}],"requestExample":{"mediaType","body"}|null,"requestSample":{"mediaType","body"}|null,"requestRequired":[..]}`。
  - 仕様の例 (2026-10-25、livenote が地図の箱から scaffolder と同じ雛形を作るため)。responseExamples は応答の例を
    すべて (2xx 以外も、仕様の順)、requestExample は本文の例のある最初の mediaType、params の example は例が
    あるときだけ付ける。body は文字列で、JSON の mediaType は JSON の文字 (詰めて書く)、それ以外の文字列の例はそのまま。
    探す順は、OAS が `example` → `examples` の最初の `value` → `schema` (参照を解いた先) の `example`、RAML が
    `example` → `examples` の最初 (`value` があればそれ) → 参照している型の `example` (型をたどる)。RAML の本文に
    mediaType を書かなければ、既定の mediaType で読む。`!include` の先も読む。テストは amodel_test の
    operations-carry-the-spec-examples (fixture は livenote/apikit-examples)。
  - 最小の本文 (2026-10-25、livenote が作った直後の例を APIkit に通すため)。requestSample は、本文の schema を持つ最初の
    JSON の mediaType について `mulay.lib.jsonschema/sample` が作る本文。例 (requestExample) があっても作る。
    - 中身は必須の項目だけ (入れ子も)。値は、const、enum の最初、example、default の順。無ければ型で決める
      (string は "sample"、integer・number は 1、boolean は true、array は要素 1 つ (minItems まで))。
    - `$ref` を解き、allOf はまとめ、anyOf・oneOf は最初のものを使う。
    - string の format (date、date-time、time、email、uuid、uri、hostname、ipv4、ipv6、RAML の datetime-only・time-only)
      と、簡単な pattern (文字、クラスの最初の文字、`\d` `\w`、`{n}` `+` `*` `?`、グループの最初の選択肢) に合う値を作る。
      minLength・maxLength・minimum・maximum・multipleOf も見る。
    - 作った本文は、APIkit と同じ検査器 (`validate`) で確かめ、通らなければ null にする。
    - requestRequired は、同じ schema の一番上の required。
    - RAML の datetime-only と time-only は、schema に `format` として残す (検査器は知らない format を見ない)。
    - 実 Mule 4.11.3 + APIkit 1.12.6 で、OAS (uuid・date-time・minimum) と RAML (pattern・datetime-only・string[]) の
      本文を通し、`{}` は必須の項目が無いと断ることを確かめた (一時的な probe)。テストは test/schema/sample_test と
      amodel_test の operations-carry-a-minimal-request-sample。必須のヘッダー (OAS の in: header、RAML の headers) は
      前から params に入っている。
    key と block は仕様のファイルの中のバイト位置 (lib/youtline)。OAS は `paths` → パス → メソッド、RAML は入れ子の
    リソースのキーをつないでパスに合うものを探す。
  - flow は APIkit が呼ぶフローの名前。本物と同じ順 (本文の mediaType つきの名前、次に無しの名前) で、あるものを探す。
    無ければ最初の候補 (本文があれば mediaType つき。Studio の雛形と同じ) を入れ、implemented を false にする。
    本文の mediaType が複数あっても操作は 1 つ。
- **APIkit の入口**: 操作ごとに `{"kind":"apikit","flow","source":null,"element":"apikit:router","method","path","main","router","api","operation","implemented"}`。
  main は router (`config-ref` がその設定) を直下に持つフロー、router はその step のパス、path は main の listener の
  path から末尾の `/*` を除いたものと仕様のパスをつないだもの。main が無ければ main と router は null で、path は仕様のパス。
- **雛形 (`scaffold`、2026-10-24)** は `conn/apikit_scaffold`。wasm の export `scaffold` (入力
  `{"config","file"?,"listenerConfig"?,"path"?}`、最後の load に対して働く) が返すのは、XML を書き換えた結果ではなく
  **編集の一覧** `{"edits":[{"file","start","end","text"}],"flows":[足したフロー],"error"}`。livenote は今ある書き換えの
  仕組みでそれを当てる (位置は元のテキストの UTF-8 のバイト位置、重ならず昇順、後ろから当てる)。
  - 足すのは、まだ無い実装フロー (implemented が false の操作。同じ名前は 1 度) だけ。あるフローには触らない。
    2xx の応答に JSON の example があれば、それを返す `ee:transform`、無ければフロー名を出す `logger` (Studio の雛形と同じ)。
  - router を持つフローが無ければ、main フロー (`<仕様のファイル名>-main`、listener、router、APIKIT の 6 つのエラーを
    Studio と同じ文と状態コードで返す error handler) も足す。listener-config は listenerConfig か、アプリに 1 つだけ
    あるもの。path は既定で `/api/*`。httpStatus と outboundHeaders の変数名は apikit:config の設定に従う。
  - 足す先のファイルは file か、main フローのあるファイル、apikit:config のあるファイル、最初の XML の順。
    flow は根の閉じタグの前に、字下げは根の最初の子の行に合わせて入れる。
  - 使う名前空間 (doc、ee、http、apikit) が根に無ければ、最後の xmlns の後に足し、`xsi:schemaLocation` があれば
    その xsd も足す。接頭辞が別の URI で使われていれば番号を付ける。部品には `doc:id` (UUID) を付ける。

## 場所

- `mulay.lib.youtline` (`outline`・`children`・`child`・`find-path`)
- `mulay.mule.amodel` (`AEntry`・`AOp`・`AApi`・`source-entries`・`with-apis`・`join-path`)
- `mulay.conn.apikit/api-models`、`mulay.conn.apikit_scaffold` (`scaffold`・`to-json`)、`mulay.note.run/scaffold-json`、`mulay.wasm.main/scaffold`、`mulay.note.run/load-dir-with`、`mulay.cli.boot` の `inspect-json`
- テスト: `test/yaml/youtline_test.clay`、`test/amodel/amodel_test.clay` (entries-of-sources・apis-and-apikit-entries・raml-ops-and-missing-flows)、
  `test/note/note_test.clay` (apikit-model-has-entries-and-apis・scaffold-from-the-session)、`test/scaffold/scaffold_test.clay`、`test/conn/raml_test.clay` (oas-examples・raml-examples)

## apikit:console (2026-10-24)

Studio の雛形のアプリには必ず console フローがあり、mulay は `apikit:console` で 500 を返していた。実 Mule 4.11.3 で確かめた
動きに合わせる (fixture apikit-console、`conn/apikit/console`)。

- 相対パス (listenerPath の `/*` を除いた所からの requestPath) が空: config の httpStatusVarName の変数に 301、
  outboundHeadersMapName の変数に `{location: <scheme>://<Host><requestPath>/}`、payload は空。listener に応答の設定が
  無ければ 200 になるのも実 Mule と同じ。
- `/` と `/index.html`: HTML (text/html)、出力ヘッダーの変数に `{expires: "-1"}`。本文は自前 (deviations.md)。
- `/api/<ファイル>`: 根の仕様のディレクトリからの相対で、根と参照先 (RAML の include・uses。解析するときに読んだ
  ファイルを記録する) だけを application/raml+yaml でそのまま返す。メソッドは問わない (POST も同じ)。
- それ以外: APIKIT:NOT_FOUND、description は相対パス。
- 雛形 (scaffold) は、main フローを作るときに console フロー (`<名前>-console`、listener `/console/*`、応答の設定は main と同じ、
  `apikit:console`、APIKIT:NOT_FOUND を {message: "Resource not found"} と 404 にする受け口) も作る (Studio と同じ)。
  main フローが既にあるときは作らない。部品はどちらも実 Mule で動かした (main は fixture apikit-scaffold、console は apikit-console)。

## api 属性の api/ (2026-10-25)

Studio の雛形は `api="shipping-api.yaml"` と書き、仕様を `src/main/resources/api/` に置く。実 Mule 4.11.3
(mule-apikit-module 1.12.6) は、この形でも `api/shipping-api.yaml` の形でも仕様を見つけて振り分ける (fixture apikit-api-folder)。

- `conn/apikit/api-path`: 書いた名前で資源が見つかればそれ、見つからなければ `api/<名前>` を探し、あればそちらを使う。
  `::` を含む名前 (Exchange の参照) は替えない。両方にあるときは書いた名前を先にする。
- 仕様の読み込み (init)、AppModel の apis の file、console の配る範囲 (根のディレクトリ)、scaffold が、どれもこの解決した
  名前を使う。RAML の include も解決した名前からの相対になる。見つからないときのメッセージには書いた名前を出す。
- テスト: `test/note/note_test.clay` (apikit-finds-the-api-under-the-api-folder、fixture `test/fixtures/livenote/apikit-bare`)。
