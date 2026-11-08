# ADR 089: Salesforce コネクタの操作の headers (SOAP ヘッダ)

日付: 2026-10-22。状態: 決定。対象は mule-salesforce-connector 11.3.4 (逆コンパイルした `SalesforceUtils`、`ForceWSCConnection`、`SalesforceHeader`)
と force-partner-api 64 (ヘッダの要素の並び)。

## 背景

- partner API を使う操作 (query、create、update、delete、merge など 17 個) は `headers` (Map) を持つ。
  - 書き方は 2 つ: 属性の式 `headers="#[{AllOrNoneHeader: {allOrNone: true}}]"` と、子要素 `<salesforce:headers><salesforce:header key=".." value="#[{..}]"/>`。
- 値は「ヘッダ名 → 中身の Map」である。
  - 以前は `<salesforce:header key="AllOrNoneHeader" value="true"/>` (値が文字列) で試して「実 Mule でも効かない」と判断し、無視していた。
  - 実コネクタは値が Map でないヘッダを捨てるので、効かなかったのはこの形のせいだった。
- AllOrNoneHeader は結果 (全部成功か全部失敗か) を、AllowFieldTruncationHeader は書く値を変えるので、無視すると実 Mule と違う結果になる。

## 決定

- conn/sf_headers が `headers` を読み、SessionHeader の後に足す SOAP ヘッダの XML を作る (`headers-xml` は値から XML とログを作る純粋な関数)。
  - conn/sf_core の `soap-h` に渡す。
  - 同じ操作の queryMore にも同じヘッダを付ける (実コネクタの SFPagingDelegate と同じ)。
- 規則は実コネクタの `addHeadersToPartnerConnection` と同じにする。
  - 値が null: 操作が MULE:UNKNOWN で失敗する ("Cannot invoke \"Object.getClass()\" .. is null")。
  - 値が Map でない: "The header <名前> should be a Map" を ERROR でログに出し、そのヘッダを捨てる。
  - 名前は大文字小文字を区別しない。知らない名前は "Invalid header name: <名前>" をログに出して捨てる。
    - LocaleOptions は SalesforceHeader の表にはあるが partner の分岐に無いので、知らない名前として扱う。
  - 中身のキーも大文字小文字を区別しない。中身の値が読めない (例外) ときは、"Header <名前> is incorrect, couldn't be added to the request" をログに出してそのヘッダを捨てる。
    - 真偽 (`(Boolean)` の cast): 無ければ false。真偽以外 (文字列の "true" など) は捨てる。
    - batchSize、majorNumber、minorNumber (`(Integer)` の cast): 無い、または int に収まる整数でなければ捨てる。
    - 文字列 (`toString()`): assignmentRuleId、client、defaultNamespace は無ければ書かない。transferToUserId と namespace は無ければ捨てる。
    - OwnerChangeOptions の type は `OwnerChangeOptionType.valueOf` と同じく、17 個の名前に大文字小文字まで一致しなければ捨てる。execute は必須の真偽。
  - 同じヘッダが 2 度あれば、後のものが勝つ (失敗したものは前の値を消さない)。
- ヘッダの要素の中の並びは partner API の生成クラス (writeFields) と同じにする。
  - ヘッダどうしの並びは固定の順 (ORDER) で、Salesforce は並びを見ない。
- 対象の操作: query、query-all、create、update、upsert、delete、retrieve、search、query-xml-stream、merge、merge-multiple、convert-lead、
  find-duplicates、find-duplicates-by-ids、describe-sobject、describe-global、publish-platform-event-message。

## 実 Mule と違う点

- 実コネクタは partner の接続をプールして使い回し、headers を渡さない内部の呼び出し (describe など) では前の操作のヘッダが残る。
  mulay は操作ごとにヘッダを作るので、この持ち越しは無い。
- Bulk API と メタデータ API の操作の headers は ADR 090 で扱う。

## 確かめ方

- fixture test/fixtures/apps/salesforce-headers (d30、実 Mule 4.11.3 で記録)。
  - AllOrNone (create / update / delete)、AllowFieldTruncation、QueryOptions (batchSize 200 / 100 / 5000 / 文字列 / 空)。
  - 名前の大文字小文字、Map でない値、文字列の真偽、null、知らない名前、子要素の形。
- 単体テスト test/conn/sf_headers_test.clay (OwnerChangeOptions と PackageVersionHeader の形も)。
- batchSize が往復の回数を変えることは、実 Mule で 2000 件を読む時間で確かめた (既定 1 回 / 1000 で 2 回 / 200 で 10 回)。
  結果の件数は変わらないので、fixture では比べられない。
