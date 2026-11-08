# ADR 090: Salesforce コネクタの Bulk API とメタデータ API の操作の headers

日付: 2026-10-22。状態: 決定。対象は mule-salesforce-connector 11.3.4。ADR 089 (partner API の操作の headers) の続き。

## 背景

- Bulk API とメタデータ API の操作も `headers` (Map。属性の式か、子要素 `<salesforce:headers><salesforce:header key value/>`) を持つ。
  - Bulk v1: create-job、create-batch、create-batch-stream、create-batch-for-query、batch-result-stream、query-result-list、query-result-stream-by-id。
  - Bulk v2: create-job-bulk-api-v2、create-query-job-bulk-api-v2。
  - メタデータ: create / update / upsert / delete / rename / read / list / describe-metadata、retrieve-metadata、deploy-metadata。
    describe-sobject と describe-global は partner API を使うので ADR 089 で扱う。
- 実コネクタの扱いは、API ごとに違う (逆コンパイルした SalesforceUtils、BulkServiceImpl、ForceWSCConnection と、実 Mule での記録)。

## 決定

### Bulk v1

- 値を `toString` した文字列を HTTP ヘッダとして送る (実コネクタの addHeadersToBulkConnection)。
  - 値が null のヘッダは送らない。
  - Map は `{a=1, b=x}`、配列は `[a, b]` (Java の toString。rt/engine の java-str)。
- 送るのは create-job、create-batch-stream、create-batch-for-query、batch-result-stream、query-result-list、query-result-stream-by-id。
  - create-batch は headers を受け取るが送らない (実コネクタの executeBatchRequest は headers に null を渡す)。
- 既定のヘッダ (X-SFDC-Session、Content-Type) の後に足す。
- 主な使い道は `Sforce-Enable-PKChunking` (大きな query のジョブを Id の範囲で分ける)。

### Bulk v2

- ジョブを作る最初の POST (`/jobs/ingest`、`/jobs/query`) にだけ HTTP ヘッダとして付ける。
  - CSV を送る PUT、UploadComplete の PATCH、状態を読む GET には付けない。
- 既定のヘッダ (Authorization、Accept、Content-Type) の後に Java の HashMap に put するのと同じで、名前が同じ (大文字小文字も同じ) なら置き換える。
- 値は String に cast する。
  - 文字列でない値は MULE:UNKNOWN で、ClassCastException の文言になる
    ("class java.lang.Integer cannot be cast to class java.lang.String (java.lang.Integer and java.lang.String are in module java.base of loader 'bootstrap')")。
  - 値の Java のクラスは `^class` があればそれ、無ければ DW の値から決める (数は int に収まれば Integer、収まらなければ Long)。
  - null の値は送らない (実 Mule は成功する)。

### メタデータ

- ヘッダは送らない。ログに出すだけ。
  - 実コネクタ (addHeadersToMetadataConnection) は、ヘッダの名前から partner API のクラス (`com.sforce.soap.partner.*_element`) を作る。
    そのクラスで MetadataConnection の `__set<名前>` を探すが、メタデータ API のメソッドは `com.sforce.soap.metadata.*_element` を取る。
    そのため、メソッドが見つからない (NoSuchMethodException)。
  - 実 Mule 4.11.3 で、AllOrNoneHeader を付けた create-metadata が、成功する行を保存することを確かめた。
- ログの規則 (logger は SalesforceUtils、ERROR):
  - 知らない名前: "Invalid header name: <名前>"。12 種類の名前 (LocaleOptions を含み、PackageVersionHeader は含まない) を大文字小文字を区別せずに探す。
  - Map でない値: "The header <正しい綴りの名前> should be a Map"。
  - Map の値: "Header <列挙の名前 (ALL_OR_NONE など)> is incorrect, couldn't be added to the request"。
- 名前を先に見るので、知らない名前の null はログに出すだけになる。
  - 知っている名前の null は、操作が MULE:UNKNOWN で失敗する (NullPointerException の文言。ADR 089 と同じ)。
- ログは 1 回の操作で 1 度だけ出す。
  - 実コネクタは SOAP の呼び出しのたびに出す。deploy と retrieve は状態を見に行くたびに同じログが出て、その回数は相手の処理の時間で変わる。

### Bulk v1 の失敗の型 (この作業で見つけて直した)

- 実コネクタの対応表 (BulkApiV1ErrorMappingType) どおりにする。
  - 表にある exceptionCode: 説明は exceptionCode そのもの (例: "ClientInputError")。
  - InvalidSessionId: CONNECTIVITY で、説明は exceptionMessage。
  - 表に無いコード: 実コネクタは先に `valueOf` で列挙を引くので失敗する。MULE:UNKNOWN "No enum constant ..BulkApiV1ErrorMappingType.<code>" にする。
    この形は、逆コンパイルしたコードから決めた。実 Mule では確かめていない (表に無いコードを返させる方法が見つからない)。

## 実 Mule と違う点 (docs/compat/deviations.md)

- Bulk v1 の持ち越し:
  - 実コネクタは、ヘッダを BulkConnection の中の Map にも足し、その Map を消さない。
  - そのため、使い回す接続でのその後の POST (create-job、close-job、abort-job、create-batch など) に、前の操作のヘッダが付く。
  - 実 Mule で確かめた: chunkSize=999999 を付けた create-job の後、ヘッダの無い create-job が ClientInputError で断られた。
  - mulay は操作ごとに送るヘッダを決め、持ち越さない。
- Bulk v1 の POST では、実コネクタは同じヘッダを 2 度送る (ConnectorConfig と BulkConnection の両方から)。mulay は 1 度だけ送る。

## 確かめ方

- fixture test/fixtures/apps/salesforce-bulk-headers (d30、実 Mule 4.11.3 で記録、24 件)。
  - v1: chunkSize の大きすぎる PK chunking が ClientInputError で断られる (属性の式と子要素)。
    PK chunking を付けた query のジョブで、元のバッチが NotProcessed になり、分けたバッチが足される。null、数、Map の値。
  - v2: Content-Type を application/xml に置き換えると、400 "Content is not allowed in prolog." になる。数・Map の値の ClassCastException、null の値。
  - メタデータ: AllOrNoneHeader を付けても、成功する行は保存される。null、知らない名前、Map でない値。
  - 持ち越しの違いが出ないように、chunkSize の大きすぎる要求は v1 の最後に置く。
- 単体テスト test/conn/sf_headers_test.clay (meta-logs、bulk1-headers、bulk2-headers) と test/conn/sf_bulk1_err_test.clay。
- GET の操作 (batch-result-stream、query-result-list、query-result-stream-by-id) にヘッダが付くことは、Salesforce の応答からは見えない。
  そのため、逆コンパイルしたコードから決めた。
