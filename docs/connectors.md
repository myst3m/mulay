# コネクタ

mulay が扱うコネクタと、その範囲。挙動の正は実 Mule 4.11.3 の記録 (`test/fixtures/apps/*`)。
実装は `src/mulay/conn/`、登録は `conn/registry.clay`。コネクタのインターフェースは `rt/conn.clay`
(操作は `OpCall` → `OpResult`、ポーリングするソースは `poll`、起動前の検査は `init`)。

## 対応状況の一覧

| コネクタ | 対応しているもの | 対応していないもの (TODO は docs/todo.md の「コネクタの未対応」) |
|---|---|---|
| HTTP | listener、request (basic / digest / OAuth client-credentials の認証)、polling-source、HTTPS (tls:context)、状態コードごとのエラー型、listener の responseStreamingMode と outputMimeType / outputEncoding、load-static-resource | request の認証 (NTLM、OAuth の他の grant)、`http:basic-security-filter` |
| ObjectStore | store / retrieve / contains / remove / clear / retrieve-all(-keys)、entryTtl、maxEntries、persistent | config-ref (DB などに置く店)、パーティション以外の分離 |
| File | read / write / list / copy / move / rename / delete / create-directory、matcher、listener | lock、ファイルの属性 (所有者・権限) の操作、symlink の追い方の指定 |
| SFTP | read / write / list / copy / move / rename / delete / create-directory、listener、パスワード認証、knownHostsFile | 鍵の認証 (identityFile)、proxy |
| APIkit | router (OpenAPI 3、RAML 1.0 / 0.8)、引数・本文の検証 | console、strict validation、Exchange の依存、RAML の一部 (discriminator など)、XML の本文のスキーマ検証、flowMappings |
| Salesforce | SOAP partner API の操作、Bulk API v1 / v2、メタデータ API、Apex、ストリーミング (発行と replay listener)、object listener、client-credentials / user-pass / basic / JWT / authorization code (+PKCE 拡張) の接続 | saml-connection、set-password 系、proxy / TLS、object listener の triggersQuery |
| Database | select / query-single / insert / update / delete / bulk-* / execute-script / execute-ddl / stored-procedure、listener、トランザクション、プール。SQLite、PostgreSQL、Oracle 23ai 以降、MySQL (generic-connection と my-sql-connection) | SQL Server など他のドライバ、XA、Oracle の 19c 以前・REDIRECT・TCPS・NNE、MySQL の RSA の鍵交換・LOAD DATA LOCAL |
| VM | publish / consume / publish-consume、listener、PERSISTENT のキュー、トランザクション | redelivery-policy (見ない) |
| A2A | サーバー (task-listener、ストリーム、resubscribe)、クライアント、push 通知、タスクの記録の置き場所、TLS | `<a2a:task-repository-object-store>` の子要素の形、記録に入る authentication / proxyConfig のオブジェクト |
| MCP | サーバー (tool / resource / prompt、セッション、on-new-session-listener)、クライアントの 7 操作、streamable-http と旧式の SSE | クライアントの authentication と tlsContext、file-image-data、outputSchemaDefinition、拒否ヘッダの null 値の 500 |
| secure-properties | `${secure::..}` と `p("secure::..")`、AES の CBC / ECB / CFB / OFB、fileLevelEncryption、key のプロパティ参照 | AES 以外のアルゴリズム、RSA、値の中の入れ子 |
| Validation | is-true / is-false / is-email / is-ip / is-url / matches-regex / validate-size / is-(not-)blank-string / is-(not-)empty-collection / is-(not-)null / is-number / is-time / is-(not-)elapsed / is-allowed-ip / is-not-denied-ip / all / any、DataWeave の Validation:: の 6 関数 | validation:config の i18n (文言の差し替え) |
| Vectors (`ms-vectors`) | embedding-generate-from-text (ollama-connection)、transform-chunk-text、transform-parse-document (Text)、store-add / query / store-remove (ephemeral-file-connection)、メタデータの条件 | ほかの埋め込みの接続 (OpenAI、Azure、Hugging Face など)、ほかの保存先 (pgvector、Chroma、Pinecone など)、multiformat (Tika) の読み取り、query-all |
| Web Service Consumer (`wsc`) | consume (document/literal の SOAP 1.1 / 1.2、WSDL の import、動的な config、body / headers / transport headers、forceXMLProlog)、Fault と HTTP・XML の失敗のエラー、WS-Security の UsernameToken (TEXT / DIGEST) と Timestamp | WS-Security の署名・暗号・検証・復号、MTOM と添付、http-transport-configuration (requesterConfig)、入力の要らない操作の本文の自動生成 |
| Salesforce Composite (`salesforce-composite`) | create-sobject-tree、execute-composite-batch / graph / request、sObject Collections (create / get / update / upsert / delete)、pre-* と post-* (post-query のページ)、token-connection と oauth-client-credentials-connection (oauth-user-pass-connection は未照合) | oauth-jwt-connection、oauth-saml-connection、config-with-oauth-connection、proxy と tls:context (mutual TLS)、gzip の応答 |
| Inference (`ms-inference`) | openai-compatible 接続の chat-answer-prompt / chat-completions / agent-define-prompt-template / tools-native-template (ai-inference 45/45) | 他の提供元の接続 (anthropic、openai など)、mcp-tools-native-template、画像・moderation の操作、streamingStrategy |
| jmx (自作モジュール) | get-recent-logs、list-log-files、tail-log-file、search-log-file、collect-metrics / cpu / memory / gc / threads (mulay のプロセスの値) | get-recent-logs の exception |
| gRPC (`grpc`) | サーバーの unary-method / server-streaming-method (send-stream-message、end-stream) / client-streaming-method / bidirectional-streaming-method (http2-support の listener の h2c、error-response、maxInboundMessageSize) (grpc-basic 26/26、grpc-stream 6/6、grpc-stream-live 16/16)、クライアントの unary-call (no-auth-connection の平文 h2c、request-headers) (grpc-client 21/21)、server-streaming-call-with-response / -with-delegation、client-streaming、bidirectional-streaming と server-streaming-delegated-listener / bidi-streaming-listener (grpc-client-stream 11/11、grpc-client-live 17/17) | server-streaming-subscriber-source、TLS、OAuth と Google の接続 |
| Anypoint MQ (`anypoint-mq`) | publish / consume / ack / nack、subscriber (AUTO / MANUAL / IMMEDIATE、prefetch / polling)、標準・FIFO のキューと交換、outputMimeType / outputEncoding、失敗の型と文言 (anypoint-mq-ops 77/77、anypoint-mq-sub 31/31) | circuit breaker、クロスリージョンのフェイルオーバー、tlsContext / proxy / TCP の設定、reconnection、フローへの並行な配信 |

## 外のコネクタ (本体と別の package。ADR 081)

組み込みでないコネクタは、Clay のソースの package として書き、mulay と一緒にビルドする。見本は `templates/connector`、確かめるのは `tools/pkg-check.sh`。
この script は、見本のコネクタを mulay の今の commit (HEAD。作業中の変更は入らない) と組み、操作 (`toy:shout`) と、listener に経路を足すソース (`toy:ping-listener`) に要求を送る。
続けて、できた配布物の実行ファイルで `mulay build` をし (アプリと事前コンパイルした DataWeave を埋め込む)、その実行ファイルにも同じ要求を送る。
配布物の `build` は、実行ファイルのディレクトリに入り口 (stub が名乗る path) があれば、そこをソースの root にする (ADR 082)。

- **コネクタの package**
  - `clay.pkg` に、mulay を `git: <mulay の url> <commit>` で書く。
  - `.clay` で `mulay.rt.conn` などを `:require` し、`(conn/connector name 名前空間URI run)` に `assoc` で足して `Connector` を返す関数を出す。
  - 足せるもの: `:sources`・`:push`・`:poll`・`:init`・`:tx-end`・`:source-elems`・`:op-chains`・`:each-child`・`:error-parents`・`:error-classes`・`:consumers`・`:mounts`・`:routed`。
  - http:listener のポートに経路を足すソース (A2A・MCP・gRPC のサーバーのような) は、`:mounts` に `Fn(m/App Values(Vec(conn/Mount) Vec(Str)))` を書く。
    - `conn/Mount` は、listener の設定の名前、経路、メソッド、basePath の下に付けるか、本文を流して読むか、処理 (`Fn(conn/Host conn/At hm/Request hm/Response)`) を持つ。
    - 処理は `Host` の `run` (フローを番号で動かす) と `eval`・`eval-tv`・`eval-str` (式の評価) を使える。`At` は受けたポート・basePath・scheme。
    - そのソースの名前は `:routed` にも書く (polling の対象から外す)。見本は `templates/connector/toy` の `toy:ping-listener`。
- **配布物の package**
  - `clay.pkg` に、mulay とコネクタを `git:` で書く。mulay は、コネクタと同じ url・同じ commit にする (1 つの url に使える commit は 1 つ)。
  - 入り口の `.clay` は `(def BOOT: boot/Boot (boot/boot-from-argv (conj (creg/all) (toy/connector)) (aot/aot)))` と `(defn main Int [] (boot/run-main BOOT))` だけを持つ。
  - 事前コンパイルの stub (見本は `aot.clay`、ns `aot`) を 1 つ持ち、入り口が `aot/aot` を渡す。stub は自分の ns・path・入り口の path を名乗る。`mulay build` はこれを差し替える (ADR 082)。
  - `mulay.cli.main` を `:require` しない。
- **まだできないこと**
  - 実装しない属性の表 (`mule/ignored`) は本体にしか無いので、外のコネクタの属性は名前で推す扱いになる。

## HTTP (`http`)

listener (app 層) と request。docs/mule-runtime.md を参照。

- polling-source: path、method、outputMimeType、`<http:polling-request-body>`、`<http:polling-request-headers>` /
  `-uri-params>` / `-query-params>` (key と value に式。`watermark` で今の watermark を使える)、response-validator、
  splitExpression (`payload` と `attributes`)、watermarkExpression と idExpression (`item` が分けた 1 件)。
  - 要求は http:request と同じ処理で送る (request-config の接続、認証、TLS)。本文の Content-Type は付けない (実 Mule の記録)。
  - 分けた 1 件は、応答の mime で書いた文字列の payload になる。attributes はどの件も応答の HttpResponseAttributes。
  - watermark と id は文字列にして比べる。そのため数値の watermark は辞書順になる (実 Mule と同じ。ADR 085)。
  - 応答が失敗の状態コードなら、フローは動かず、ログに出る。
  - 式は http コネクタが自分で評価する (ADR 084)。属性の形 (pollingRequestHeaders など、大域の要素の参照) は読まない。
  - シナリオ: http-polling (5/5)。

## ObjectStore (`os`)

store、retrieve、contains、remove、clear、retrieve-all、retrieve-all-keys。`<os:object-store>` の entryTtl、maxEntries、
expirationInterval (期限と上限は周期ごとの確かめで消える。実 Mule と同じく確かめるまでは残る)、persistent (既定 true)。
store は `failIfPresent` (既定 false。true で既存のキーなら OS:KEY_ALREADY_EXISTS "ObjectStore already contains an object for key '<k>'") と
`failOnNullValue` (既定 true。値が null なら OS:NULL_VALUE。false なら何も保存せず成功する。既存の値は残る)。シナリオ: objectstore-store (12/12)。
persistent の店 (既定の店を含む) は `<mulay.work.dir (既定 .mulay)>/<アプリ>/objectstore/` のファイルに書き、再起動をまたぐ。
シナリオ: objectstore-test (19/19)、objectstore-limits (11/11)。

## File (`file`、mule-file-connector 1.5)

| 操作 | 対応 |
|---|---|
| read | path、outputMimeType、outputEncoding。mime は拡張子から (Mule の mime.types)。attributes は LocalFileAttributes |
| write | path、`<file:content>` (無ければ payload)、mode (OVERWRITE / APPEND / CREATE_NEW)、createParentDirectories |
| list | directoryPath、recursive、`<file:matcher>` か matcher="名前"。要素は {payload, attributes} |
| copy / move | sourcePath、targetPath (ディレクトリとして扱う)、overwrite、createParentDirectories、renameTo |
| rename / delete / create-directory | 実 Mule と同じ失敗の型 (FILE:ILLEGAL_PATH、FILE:FILE_ALREADY_EXISTS) と文言 |
| listener | directory、recursive (既定 true)、matcher、autoDelete、moveToDirectory、renameTo、applyPostActionWhenFailed (既定 true。false なら失敗したファイルは後処理しない)、watermarkEnabled、outputMimeType、`<scheduling-strategy>` |
| matcher | filenamePattern (glob、`regex:`)、pathPattern、directories / regularFiles / symLinks (INCLUDE / REQUIRE / EXCLUDE)、minSize、maxSize、updatedInTheLast、notUpdatedInTheLast、createdSince / createdUntil / updatedSince / updatedUntil / accessedSince / accessedUntil (ファイルの時刻をこの機械の時間帯の LocalDateTime にして比べる。作成時刻は Linux の Java 17 と同じく更新時刻。accessedUntil は実コネクタと同じく Since と同じ比べ方) |

timeBetweenSizeCheck (と timeBetweenSizeCheckUnit。操作か listener に無ければ file:config のもの): read と listener は、
中身を読む前にその時間だけ待って大きさを比べる (実コネクタの AbstractFileInputStreamSupplier と同じく 4 回まで)。
落ち着かなければ、payload を DW で読んだときに FileBeingModifiedException の文言 (MULE:EXPRESSION) で失敗する。
list では待たない。lock は受け付けるが、何もしない (deviations.md)。

## SFTP (`sftp`、mule-sftp-connector 2.7)

- conn/sftp と lib/sftp (SFTP v3。SSH は純 Clay の lib/ssh で、外部のライブラリは要らない)。接続は設定ごとに使い回す。
- 設定: `<sftp:connection host port username password workingDir connectionTimeout connectionTimeoutUnit>` (パスワード認証だけ)。
- 操作: read、write (mode OVERWRITE / APPEND / CREATE_NEW、createParentDirectories)、list (recursive)、copy、move、rename、
  delete (ディレクトリは中身ごと)、create-directory。パスと失敗の型・文言は File コネクタと同じ規則 (SFTP:ILLEGAL_PATH、
  SFTP:FILE_ALREADY_EXISTS)。接続の失敗は SFTP:INVALID_CREDENTIALS / SFTP:CANNOT_REACH。
- read の mime は拡張子から (コネクタ同梱の Tika の表。conn/sftp_mimes は tools/gen-sftp-mimes.java で作る。File コネクタの表とは違い
  `.json` は application/json)。attributes は SftpFileAttributes (fileName、symbolicLink、regularFile、directory、path、size、
  permissions、name、timestamp)。list の要素の payload はパスの文字列 (実 Mule の記録)。
- knownHostsFile: クラスパスの資源、無ければファイルのパス。行の無いホストと鍵の違うホストは SFTP:CANNOT_REACH "Server key did not validate" (実 Mule と同じ)。指定が無ければ鍵を確かめない (実 Mule の既定と同じ)。
- listener: directory (workingDir から)、recursive (既定 true)、matcher (`<sftp:matcher>` の参照か中に書いたもの。filenamePattern、
  pathPattern、directories / regularFiles / symLinks、minSize / maxSize、updatedInTheLast / notUpdatedInTheLast、timestampSince / timestampUntil)、
  autoDelete、moveToDirectory (無ければ作る) + renameTo、applyPostActionWhenFailed (既定 true)、watermarkEnabled (更新時刻。同じ秒のものはパスで覚える)、
  timeBetweenSizeCheck、outputMimeType / outputEncoding。payload は読み切った内容、attributes は read と同じ SftpFileAttributes。
  起動の時点 (最初のポーリング) でディレクトリが無ければ、実 Mule と同じく "could not be reconnected. Will be shutdown" を出してその source を止め、
  後でディレクトリができても読まない。
- 未対応: 鍵の認証 (identityFile)、proxy。
- シナリオ: sftp-ops (39/39)、sftp-listener (26/26。見るディレクトリはシナリオの `sftpdir` で起動前に作り直す)。サーバーは手元の Kubernetes の mulay-sftp (atmoz/sftp:debian、`mulay:mulay:1001::upload`)。
  ホストの `127.0.0.1:2222` に転送がある。構築の手順はこのリポジトリの外にある。
  `latest` タグは 2024 年から更新が止まっているので `:debian` を使う。サーバーの鍵は `known_hosts_good` に書いた鍵と
  同じでないと鍵の検査のシナリオが落ちる (控えは `~/srv/mulay-sftp/keys/`)。

## APIkit (`mule-apikit`、mule-apikit-module 1.12)

`apikit:config` の `api` は API 仕様の資源のパス。OpenAPI 3 (YAML か JSON) と RAML 1.0 / 0.8。起動時に読み、
壊れていれば (存在しない型の参照、読めない !include を含む) 起動しない。

- RAML (`conn/raml`): !include (.raml / .yaml は YAML、.json は JSON Schema)、uses (ライブラリ)、
  traits と resourceTypes (引数、`<<resourcePath>>`、`<<resourcePathName>>`、"get?")、入れ子の資源と
  uriParameters の引き継ぎ、queryParameters と headers (1.0 は既定で必須、0.8 は任意)、型
  (組み込み型、継承、`T[]`、`A | B`、ファセット、`?` の付いたプロパティ)、JSON Schema (!include と
  0.8 の schemas)、formParameters。型は JSON Schema にして OpenAPI と同じ検証器で検証する
  (実 APIkit と同じ文言)。

- router: 相対パス (listener のパスの `/*` より後) で資源を引く。無ければ APIKIT:NOT_FOUND、メソッドが
  無ければ APIKIT:METHOD_NOT_ALLOWED、実装フロー (`get:\items\(id):config`、本文の型ごとなら
  `post:\items:application\json:config`) が無ければ APIKIT:NOT_IMPLEMENTED。
- 検証: URI 引数、クエリ (既定値を queryParams に足す、繰り返し)、ヘッダ、Accept (APIKIT:NOT_ACCEPTABLE)、
  Content-Type (APIKIT:UNSUPPORTED_MEDIA_TYPE)、本文 (JSON Schema、form の required)。失敗は
  APIKIT:BAD_REQUEST で、説明は実 Mule と同じ文言と並び (`lib/jsonschema`)。disableValidations。
- 実装フローには uriParams を差し替えた attributes を渡し、outboundHeaders の変数を {} にしておく。
  httpStatus の変数が無ければ、仕様の最初の 2xx にする。

扱わない: apikit:console、queryParamsStrictValidation / headersStrictValidation、RAML の型の
discriminator と example の検証、ライブラリの中の uses (入れ子のライブラリ)、Exchange の依存
(`resource::...`) の仕様。

## Salesforce (`salesforce`、mule-salesforce-connector 11.3)

実コネクタと同じく SOAP の partner API (版 65.0) を使う。レコードは partner API の sObject の形の Map
(値は文字列、`type` と `Id` が必ずある) で、キーは java.util.HashMap の順 (`lib/jhash`)。
書くレコードの値には、実コネクタ (wsc) と同じく値の型を `xsi:type` で付ける (文字列 xsd:string、数 xsd:int / long / double、
真偽 xsd:boolean、Date xsd:date、DateTime xsd:dateTime)。そのため、文字列を日付やチェックボックスの項目に、数や真偽をテキストの項目に
書くと、Salesforce が INVALID_TYPE_ON_FIELD_IN_RECORD「必須種別以外の値」で断る (文字列を数の項目に書くのは通る)。
読んだ値は String (`^class` は java.lang.String)。実 Mule の記録は test/fixtures/apps/salesforce-types。
partner API の操作の `headers` は SOAP ヘッダとして送る (ADR 089)。値は「ヘッダ名 → Map」
(`headers="#[{AllOrNoneHeader: {allOrNone: true}, QueryOptions: {batchSize: 200}}]"`、または `<salesforce:header key="AllOrNoneHeader" value="#[{allOrNone: true}]"/>`)。
実コネクタの 12 種類 (AllOrNone、AllowFieldTruncation、AssignmentRule、CallOptions、DisableFeedTracking、DuplicateRule、Email、Mru、OwnerChangeOptions、
PackageVersion、QueryOptions、UserTerritoryDelete) を扱い、Map でない値や読めない値のヘッダは実 Mule と同じくログに出して捨てる。
QueryOptions の batchSize は 1 回の応答の件数 (既定は最大の 2000) で、続きを取る queryMore にも効く。実 Mule の記録は test/fixtures/apps/salesforce-headers。
Bulk と メタデータ API の操作の `headers` (ADR 090、実 Mule の記録は test/fixtures/apps/salesforce-bulk-headers):
Bulk v1 は値を toString した HTTP ヘッダとして送る (`headers="#[{'Sforce-Enable-PKChunking': 'chunkSize=100000'}]"` で query のジョブを分けられる。create-batch は送らない)。
Bulk v2 はジョブを作る最初の POST にだけ付け、名前の同じ既定のヘッダを置き換える。値は文字列だけで、数などは実 Mule と同じく ClassCastException の MULE:UNKNOWN。
メタデータ API の操作は、実コネクタと同じくヘッダを送らない (partner API のクラスを渡そうとして失敗し、ログに出すだけ)。

| 種類 | 対応 |
|---|---|
| 接続 | oauth-client-credentials-connection、oauth-user-pass-connection、basic-connection (SOAP の login)、jwt-connection (keyStore の鍵で RS256 の JWT。keyStore は中身で JKS か PKCS12 かを見分ける (実コネクタの KeyStore.getDefaultType() と同じ)。PKCS12 は最初の鍵を使う。鍵が取り出せなければ CONNECTIVITY "Failed signing payload"、トークンが取れなければ INVALID_INPUT "Invalid status code: .."。鍵は起動のときに読む)、config-with-oauth-connection (認可コード。oauth-callback-config の listenerConfig に authorizePath (authorizationUrl へ 302) と callbackPath (code をトークンに替える) を足す。トークンが無ければ CONNECTIVITY "OAuth authorization dance not yet performed for resourceOwnerId null"、401 なら refresh_token で取り直す。unauthorize はトークンを捨てる)。セッションは設定ごとに持ち、切れたら取り直す |
| 操作 | query、query-all (parameters、queryMore、escapeSpecialCharactersForParametersValue は値を SalesforceUtils と同じに逃がす)、query-xml-stream、create、update、upsert、delete (BulkOperationResult)、retrieve、search (parameters)、describe-sobject、describe-global、get-user-info、get-server-timestamp、get-updated、get-deleted、merge (MergeResult)、merge-multiple (MergeResult の配列)、convert-lead (LeadConvertResult)、find-duplicates、find-duplicates-by-ids |
| Bulk API v1 | async API (XML)。create-job (create-job-request の contentType・concurrencyMode・externalIdFieldName)、close-job、abort-job、job-info、create-batch (レコード)、create-batch-for-query、create-batch-stream (CSV など)、batch-info、batch-info-list、batch-result (BulkOperationResult)、batch-result-stream (XML)、query-result-list、query-result-stream-by-id (`*/*` の Binary)。JobInfo / BatchInfo の日時は UTC の LocalDateTime |
| Bulk API v2 | ingest (create-job は CSV を送って UploadComplete まで、get-job-state、abort-job、delete-job、get-all-jobs、成功・失敗・未処理の結果) と query (create-query-job、get-query-job-info、abort、delete (void)、get-all-query-jobs、get-query-job-results)。値は実コネクタのクラス (BulkJobState、QueryJobState、QueryJobInfo、BulkJobV2Result、QueryJobsInfoResult、Job*RecordResult) で、キーの並びは実 Mule の記録のまま。一覧は nextRecordsUrl、query の結果は Sforce-Locator (maxRecordsPerPage) のページを、読み進めたときに取りに行くカーソル (最初のページは操作のときに読む。途中の失敗は読んだところで SALESFORCE:<型>)。失敗は "Invalid status code: <状態>, response body: <本文>" (404 は NOT_FOUND、4xx は INVALID_INPUT、それ以外は MULE:UNKNOWN) |
| メタデータ API | describe-metadata、list-metadata、read-metadata (WSC のオブジェクトの Map: 型のフィールドすべてとその `__is_set`。型の表は tools/gen-sf-metatypes.py が force-metadata-api 65.0.0 から作る)、create / update / upsert / rename / delete-metadata。結果の形は実コネクタの写し (delete の fullName と upsert の created は写さない)。retrieve-metadata (packageNames、specificFiles、unpackaged の package.xml。結果は zip のバイト列で、実コネクタと同じく application/xml が付く)、deploy-metadata (deploy-metadata-request の stream の zip。payload は変えない)。どちらも 1 秒から倍々に待って状態を見る |
| Apex | invoke-apex-rest-method (methodName の "メソッド^URL^Http 動詞^戻り値の型^引数=型" で呼ぶ。結果は {"<メソッド>Output": 値} の HashMap、値は戻り値の型で Long / Date / Map の {key, value} に。2xx でなければ CONNECTIVITY)、invoke-apex-soap-method (Body の要素の XML。fault は NOT_FOUND)。応答のヘッダ (attributes) は持たない |
| ストリーミング | publish-topic、publish-streaming-channel (無ければ作り、あれば更新。Result)、push-generic-event (PushEventResult の配列)、publish-platform-event-message (Result の配列) |
| ソース | new-object-listener、modified-object-listener、deleted-object-listener (`<scheduling-strategy>`、since。payload は全項目の java.util.HashMap。deleted は queryAll の IsDeleted = true)、replay-topic-listener、replay-channel-listener (CometD の long-polling、replayOption。payload は PushTopic なら sobject、それ以外はメッセージ全体。attributes は channel と event の項目) |
| エラー | SOAP の fault の exceptionCode から SALESFORCE:INVALID_INPUT など。説明は exceptionMessage |

扱わない: saml-connection (起動時に止める)、set-password / reset-password / change-own-password。
basic-connection と oauth-user-pass-connection は実 Mule と照合していない (d30 のパスワードを使わない)。
config-with-oauth-connection は、認可の口のリダイレクト先、認可の前と unauthorize の後の失敗を実 Mule と照合した
(salesforce-oauth。認可は sf CLI のセッションで自動で通す `%%% sfauth`)。d30 の接続アプリは PKCE を外せず (新しく
作っても isPkceRequired が true になる)、PKCE を送らない実 Mule と mulay はどちらも Salesforce に 400 で断られるので、
コールバックでのトークンの受け取りと取り直しは test/rt/oauth_test.clay の偽のトークンの口で確かめた。
mulay だけの拡張として、プロパティ `mulay.salesforce.pkce=true` で PKCE (S256。RFC 7636) を送れる (実 Mule は
コネクタ 12.0.4 まで PKCE を送らず、PKCE を求める組織では認可コードの接続が使えない)。d30 で、認可からトークンの
受け取り、問い合わせ、unauthorize まで通ることを手で確かめた (salesforce-oauth/pkce-check.py、2026-10-04)。
replay listener の FROM_LAST_REPLAY_ID はプロセスの中で覚えるだけ (実コネクタは Object Store に持つ)。

シナリオ `test/fixtures/apps/salesforce-ops`、`salesforce-ops2`、`salesforce-bulk2`、`salesforce-oauth`、`salesforce-meta`、`salesforce-apex`、`salesforce-stream`、
`salesforce-jwt` (接続アプリに sf-jwt.jks の証明書を載せておく。sf-jwt.p12 はそれを keytool -importkeystore で PKCS12 にしたもの。鍵ストアも sf-secret.yaml と同じくリポジトリに入れない)
(Apex のクラスと Platform Event は `test/fixtures/apps/salesforce-apex/sfdx/` を sf CLI で deploy しておく) は実際の org (d30) に対して動く。認証情報
(各アプリの `src/main/resources/sf-secret.yaml`: sf.clientId、sf.clientSecret、sf.tokenUrl。salesforce-jwt と salesforce-oauth はほかのキーも使う) はリポジトリに入れない。
無ければ `mule-oracle` はこのアプリを飛ばす (`%%% requires`)。

## Database (`db`、mule-db-connector 1.16)

- 設定は `<db:generic-connection url=.. user=.. password=..>`。ドライバは url で選ぶ: `jdbc:sqlite:` (libsqlite3 の FFI、
  db/sqlite)、`jdbc:postgresql:` (clay.postgres の拡張クエリ、db/pg。値の型、パラメータの型、失敗の文言は pgjdbc に合わせる)。
  PostgreSQL の TLS は URL の ssl / sslmode / sslrootcert / sslfactory (pgjdbc 42.7 と同じ規則。既定は prefer で、サーバーが
  断れば平文。prefer / require は証明書を確かめず、verify-ca は鎖だけ、ssl=true と verify-full は名前も確かめる)。接続できなければ
  xapool の "Cannot get connection for URL <url> : <文言>" (DB:CONNECTIVITY)。
  `<db:oracle-connection>` と `jdbc:oracle:thin:` (純 Clay の thin、db/oracle。値の型と失敗の文言は ojdbc11 に合わせる。
  TIMESTAMP は oracle.sql.TIMESTAMP のバイト列の bean、CLOB は String、生成されたキーは ROWID か指定した列)。
  Oracle は 23ai 以降だけ (19c 以前の接続の手順、TCPS、OUT バインドは未対応)。
  `jdbc:mysql:` と `<db:my-sql-connection host port user password database>` (純 Clay のクライアント・サーバー・プロトコル、
  db/mysql と db/mywire。値の型、パラメータの書き方、失敗の文言は mysql-connector-j 9.2 に合わせる。下の「MySQL」)。
- 接続は設定ごとのプールから借りて返す。並行するフローが同じ接続を同時に使わない。壊れた接続 (SQLState 08xxx) は捨てる。
  `<db:pooling-profile>` の maxPoolSize と maxWait (maxWaitUnit) を守る: 満杯なら空くのを待ち、待ちきれなければ
  DB:CONNECTIVITY "An attempt by a client to checkout a Connection has timed out." (maxWait 0 は無期限)。profile が無ければ上限なし。
  select の結果は行のストリーム (rt/stream): 読み切るか要求が終わるまで接続を持つ (実 Mule と同じ。読まないまま同じ設定の
  select を続けると checkout の待ち時間切れ)。DW で読むと全部読んで接続を返す。
  Oracle は fetch で少しずつ読む (1 回に fetchSize 行、既定 500)。foreach (collection を省いて payload を回すとき) は
  batchSize 行ずつ取り出すので、大きな結果もメモリに置かない (select → foreach batchSize → bulk-insert の移行で
  100 万行を約 10 秒、RSS 45 MB。実 Mule は約 17〜21 秒、RSS 970 MB。2026-10-03、Oracle 23.26 Free)。
  SQLite も sqlite3_step で少しずつ読む (最初の fetchSize 行は select のときに読み、失敗はそこで出す。100 万行の select →
  foreach batchSize 1000: 0.63 s、RSS 30 MB。実 Mule は 2.8〜3.5 s、0.98 GB)。PostgreSQL は全部読んでから接続を持つ。
- listener (`<db:listener table watermarkColumn idColumn>`、ポーリング): `SELECT * FROM <table>` を引き、watermark があれば
  `WHERE <watermarkColumn> > :watermark` を付ける (実コネクタの RowListener と同じ文)。行を 1 件ずつ流し、payload は select の行と同じ
  (列の名前から値、Java の型)、attributes は null。列の名前は大文字・小文字を区別せずに引く。watermark と id の判定は ADR 085 (rt/poll)。
  表が無いときは、ポーリングのたびに "Failed to query table '..' for new rows. .." をログに出し、表ができたら読む。
  maxRows・fetchSize・queryTimeout は select と同じ。transactionalAction / transactionType は読まない。シナリオ db-listener (6/6。表は `startsql` で作る)。
- 操作: select、query-single、insert (autoGenerateKeys)、update、delete、bulk-insert / bulk-update / bulk-delete、
  execute-script、execute-ddl。SQL の種類の検査 (DB:BAD_SQL_SYNTAX) と :name のパラメータは mule-db-client と同じ規則
  (db/sqltext)。値は JDBC ドライバが返す Java の型 (class のメタデータ) で持つ。
- stored-procedure: IN / OUT / IN OUT、Oracle の REF CURSOR (行の配列)、`{? = call f(..)}`。結果は resultSetN、updateCountN、
  OUT の名前 (キーは HashMap の順)。OUT の値の Java の型は output-parameter の type で決まる。Oracle は ojdbc と同じく
  PL/SQL の BEGIN .. END に、PostgreSQL は pgjdbc の既定と同じく `select * from f(..) as result` に書き換える
  (PostgreSQL のプロシージャは実 Mule と同じく "is a procedure" で失敗する。書き換えた文面は pgjdbc の
  Parser.modifyJdbcCall と同じで、call の後ろは空白もそのまま、OUT の ? は void で送る)。
  引数の種類 (IN / OUT / IN OUT) は、db:config ごとに SQL の文面で最初の呼び出しのものを覚えて使い続ける (実 Mule の
  DbConnectionProvider の cachedTemplates、50 件)。同じ文面を output-parameter と in-out-parameter で使い分けると、
  2 回目は覚えた種類で動く (OUT のままなら値を送らない。IN OUT なのに値が無ければ MULE:UNKNOWN の
  "Parameter '..' was not bound for query '..'")。
- トランザクション: try の transactionalAction (ALWAYS_BEGIN、BEGIN_OR_JOIN) の中の操作は、設定ごとに 1 本の接続を
  トランザクションに結び付けて使う。try の終わりに、エラーが無いか on-error-continue で扱えば commit、そうでなければ
  rollback。操作の transactionalAction: JOIN_IF_POSSIBLE (既定)、ALWAYS_JOIN、NOT_SUPPORTED (外で自動コミット)。
  XA は未対応。
- 失敗の型は mule-db-client の DbExceptionHandler と同じ規則 (SQLSyntaxErrorException は DB:BAD_SQL_SYNTAX で文言は例外の
  toString、SQLState 08xxx は DB:CONNECTIVITY、それ以外は DB:QUERY_EXECUTION)。
- execute-script の file は SQL のファイル (UTF-8) を資源から読む。資源に無い絶対パスはファイルシステムから読む。無ければ MULE:UNKNOWN
  "Unable to read script file: <file>" (実 Mule と同じ。相対パスは資源だけを見る。実 Mule は Mule の作業ディレクトリも先に見る)。
- execute-script は文を executeBatch で流したときと同じ: 途中の失敗の文言はドライバの BatchUpdateException (SQLite "batch entry N: .."、
  PostgreSQL "Batch entry N <SQL> was aborted: .."、Oracle はサーバの文言。Oracle は SELECT を含む本文を実行の前に ORA-17080 で断る)。
  結果は int[]。PostgreSQL は pgjdbc と同じ Sync の区切り (先頭の 255 文、その後は 256 文ずつ) ごとに文を続けて送り、1 回の往復に
  する。自動コミットでは区切りごとに 1 つのトランザクション (途中で失敗すると、その区切りの中の前の文は取り消され、前の区切りまでは残る)。
- bulk-insert / bulk-update / bulk-delete は JDBC の executeBatch と同じ: 結果は組ごとの件数の int[]、失敗の description は
  例外の toString (`java.sql.BatchUpdateException: ..`)。Oracle は全部の組を 1 回の実行 (配列の DML) で送り、途中の組で
  失敗するとそれより前の組は残る。PostgreSQL は pgjdbc と同じ Sync の区切り (先頭の 255 組、その後は 256 組ずつ) ごとに 1 回の往復
  (Parse + 組ごとの Bind/Execute + Sync) で送り、自動コミットでは区切りごとに 1 つのトランザクション (途中で失敗すると、
  その区切りの中の前の組は取り消され、前の区切りまでは残る)。失敗の文言は pgjdbc の "Batch entry N <値を埋め込んだ SQL>
  was aborted: .."。値はサーバが推論した引数の型に合わせて渡す (Mule の ParameterMetaData と同じ)。SQLite は文を 1 回だけ
  準備して組ごとに実行する (前の組は残る。文の準備の失敗は Mule の "A problem occurred while trying to acquire a cached
  PreparedStatement .."、それ以外は `org.sqlite.SQLiteException: ..`)。
- `queryTimeout` / `queryTimeoutUnit` (execute-ddl 以外の全操作、既定 0 = 無制限。ADR 076): 秒に直すときは端数を切り上げる
  (500 ms は 1 秒)。負なら MULE:UNKNOWN "Query timeout must be positive"。時間を過ぎると実行中の文を中断する。
  - PostgreSQL: DB:QUERY_EXECUTION "ERROR: canceling statement due to user request" (bulk と execute-script はバッチ全体で 1 つの
    時間で、途中の組の "Batch entry N .. was aborted: ERROR: canceling statement .." になる)。
  - MySQL: DB:QUERY_EXECUTION "Statement cancelled due to timeout or client request" (bulk だけは失敗にせず、止めた文の結果を返す)。
  - 中断の後も接続はそのまま使う (db-pg、db-mysql の /qt/*)。
  - Oracle は中断しない (ojdbc は TCP の緊急データで合図する。clay に口が無い)。SQLite は実 Mule も中断しない
    (sqlite-jdbc は busy timeout にするだけ。mulay の SQLite には接続どうしのロックが無い)。docs/todo.md。
- select の `maxRows`: 先頭の N 行までにする (0 以下は上限なし。リテラルか式。3 つのドライバとも db-sqlite、db-pg、db-oracle の select-max で実 Mule と照合)。
- MySQL (mysql-connector-j 9.2 の既定と同じ。実 Mule の記録は db-mysql):
  - TLS は sslMode (既定 PREFERRED: サーバーが持てば TLS。証明書は確かめない。REQUIRED (確かめない)、DISABLED、
    VERIFY_CA、VERIFY_IDENTITY。旧い useSSL / requireSSL / verifyServerCertificate も Connector/J と同じく読み替える)。
    **本番では `sslMode=VERIFY_IDENTITY` にする。** PREFERRED と REQUIRED は証明書を確かめないので、中間者がつなぎを
    横取りでき、caching_sha2_password の全部の認証で送るパスワードも読まれる。信頼する CA は
    `trustCertificateKeyStoreUrl=file:/path/truststore.jks` (`trustCertificateKeyStoreType` は JKS か PKCS12、
    `trustCertificateKeyStorePassword`)。指定が無ければ OS の CA で確かめる。VERIFY_CA は鎖だけを確かめ、名前は
    確かめない (Connector/J と同じ。MySQL が自動で作る証明書でもつながる)。
  - サーバーから読む 1 つのパケット (行など) は maxAllowedPacket (既定 64 MiB) まで。超えると PacketTooBigException。
    認証は caching_sha2_password (全部の認証は TLS の上でパスワードを送る。平文なら Connector/J と同じく
    "Public Key Retrieval is not allowed") と mysql_native_password。
  - パラメータは SQL のリテラルにして送る (クライアント側の prepared statement。文字列は ' を ''、\ を \\ に。
    Boolean は 1 / 0、LocalDateTime は小数部の末尾の 0 を削る、DateTime は実行環境の地域の時刻、Binary は X'..')。
  - 値の Java の型: TINYINT(1) と BIT(1) は Boolean、TINYINT / SMALLINT / MEDIUMINT / INT は Integer (INT UNSIGNED は Long)、
    BIGINT は Long (UNSIGNED は BigInteger)、DECIMAL は BigDecimal、FLOAT は Float、DOUBLE は Double、DATE と YEAR は
    java.sql.Date (YEAR は 1 月 1 日)、DATETIME は LocalDateTime、TIMESTAMP は java.sql.Timestamp、TIME は java.sql.Time
    (DW には 1970-01-01 の LocalDateTime に見える)、文字列・TEXT・JSON・ENUM・SET は String、BINARY・BLOB・BIT(n) は byte[]。
  - 生成キーは列 GENERATED_KEY (BigInteger)。update の件数は変わった行ではなく見つかった行 (useAffectedRows=false)。
  - bulk と execute-script は 1 文ずつ送り、途中で失敗しても残りを送る (continueBatchOnError)。最初の失敗を返す。
    execute-script の結果セットを返す文 (SELECT、WITH、SHOW、`(` など) は送らずに "Statement.executeUpdate() or
    Statement.executeLargeUpdate() cannot issue statements that produce result sets." で断る。
  - stored-procedure: OUT と IN OUT は Connector/J と同じくユーザー変数 `@com_mysql_jdbc_outparam_<名前>` で受ける
    (SET → CALL → SELECT)。`{? = call f(..)}` は `SELECT f(..)`。CALL の失敗は DB:QUERY_EXECUTION。
  - 失敗の class は SQLState で決まる (42 は SQLSyntaxErrorException で DB:BAD_SQL_SYNTAX、1406 と 1264 は
    "Data truncation: .." の MysqlDataTruncation)。接続できなければ "Communications link failure ..."。
  - サーバーは手元の Kubernetes の mulay-mysql (MySQL 8.4、`127.0.0.1:13306`、mulay / mulay / DB mulay)。
- シナリオ: db-sqlite (53/53)、db-pg (92/92)、db-oracle (65/65、Oracle 23.26 Free)、db-mysql (69/69、MySQL 8.4)。
- db-pg と db-pool のサーバーは手元の Kubernetes の mulay-pg (PostgreSQL 16、`localhost:15432`、mulay / mulay)。
  ホストの `127.0.0.1:15432` に転送がある。構築の手順はこのリポジトリの外にある。
  転送は 127.0.0.1 にだけ待つ (LAN に出さない)。

## VM (`vm`、mule-vm-connector 2.0)

- 設定は `<vm:config>` の `<vm:queues>`。宣言していないキューは `MULE:UNKNOWN` ("queue 'x' is not defined")。
- 操作: publish (`<vm:content>`、無ければ payload)、consume (時間切れは `VM:EMPTY_QUEUE`)、publish-consume (listener の
  フローの結果を待つ。時間切れは `VM:QUEUE_TIMEOUT`、フローの失敗は `VM:PUBLISH_CONSUMER_FLOW_ERROR` "型: 説明")。
- ソース: listener。取り出した message の attributes は VMMessageAttributes {queueName, correlationId, timestamp}。
  相関 ID は publish した側のものを引き継ぐ。publish / publish-consume の `correlationId` (式) で送る値を変えられ、`sendCorrelationId`
  (操作に書けばそれ、無ければ `<vm:config>` のもの、既定 AUTO) が NEVER なら送らない: consume の attributes.correlationId は null、
  listener のフローには新しい相関 ID を振る。操作に AUTO と書くと、設定が NEVER でも送る (vm-test の /vm/cid/*)。
- キューはメモリに持ち、PERSISTENT のキューは `<mulay.work.dir>/<アプリ>/vm/` のファイルにも書く (再起動をまたぐ)。
  listener は numberOfConsumers (既定 4) 個が並行に流す。
- トランザクション (try の transactionalAction で始めたもの): publish は commit でキューに入り、rollback で捨てる
  (同じトランザクションの consume からは見えない)。consume した message は rollback でキューの先頭に戻る。
  操作の transactionalAction が NOT_SUPPORTED ならトランザクションの外、トランザクションの外の ALWAYS_JOIN は
  `MULE:TRANSACTION`。listener の transactionalAction="ALWAYS_BEGIN" はフローをトランザクションの中で流し、失敗
  (on-error-continue で扱ったものを除く) なら rollback して message をキューの先頭に戻す (成功するまで流れ直す。
  その中の publish は捨てる)。redelivery-policy は見ない。
- シナリオ: vm-test (17/17)、vm-tx (7/7)。

## A2A (`a2a`、mule4-a2a-connector 1.1.1)

A2A の型の JSON は、実コネクタと同じく a2a-java-sdk 0.3.3 (Jackson 2.17.0) の形に読み直して書き出す (`conn/a2a_spec`)。
キーの並び (@JsonCreator の引数の順)、null の省略、既定値 (Task の history は []、TaskStatus の timestamp は今の UTC)、
読めないときの Jackson の文言 (位置と参照の連鎖) まで同じ。期待値は `tools/gen-a2a-golden.java` が実 SDK で作る。

- サーバー (`<a2a:server-config>`): `<a2a:connection listenerConfig agentPath>` の listener-config のポートに、
  `GET <basePath><agentPath>/.well-known/agent-card.json` (カード) と `POST <basePath><agentPath>` (JSON-RPC) を足す。
  経路は `<a2a:task-listener>` のあるときだけ。カードは `<a2a:agent-card><a2a:json>` か `file` (読めなければ起動しない)。
  - message/send を task-listener のフローに流す。payload は MessageSendParams (text/json)、attributes は
    RequestAttributes。応答は `<a2a:response>` の response (無ければ payload) を EventKind (Message か Task) として読み直す。
    フローの失敗は INTERNAL_ERROR (A2A の型の raise-error ならその型) で、description が message。
  - JSON-RPC の失敗の文言と状態コードは実コネクタと同じ (不正な JSON、知らないメソッド、params の失敗、知らないタスク、
    終わったタスク、違うコンテキスト、応答の ID の不一致、カードの capabilities に無いストリーム・プッシュ通知)。
  - タスクの記録 (taskHistoryEnabled、既定 true) はプロセスのメモリに持つ。要求と応答のメッセージを履歴に足し、
    応答が Task なら記録のタスクにする (artifacts は前のものに足す)。記録なしのサーバーはタスク ID を検査しない。
  - 認可の要るメソッド (tasks/get、tasks/cancel など) は `<a2a:authorization-listener>` のフローを先に流し
    (payload は params、application/json)、失敗すれば 403 Unauthorized。リスナーが無ければ 403
    "Authorization listener required for <method>"。
  - tasks/get は履歴の最後の historyLength 件 (既定 0) を付けて返す。Message しか返していないタスクと、選んだ履歴に
    状態のメッセージの無い Task の応答が混じるときは "Task not found" (実コネクタと同じ)。
  - tasks/cancel は終わっていないタスクを canceled にして 202 で返す。
  - プッシュ通知 (カードの capabilities.pushNotifications): `<a2a:push-notification-config-listener>` が必須
    (無ければ起動しない。逆にカードが宣言しないのに listener があっても起動しない)。設定 (message/send の
    configuration.pushNotificationConfig と tasks/pushNotificationConfig/set) はそのフローを先に流し、失敗すれば
    "Push notification config rejected: <説明>"。URL は http / https でなければ断る。設定の id は受けたときの UUID。
    - message/send に設定があれば、すぐ 202 で submitted の Task を返し、task-listener のフローを別に流して、その
      JSON-RPC の答えを最後の設定の URL に POST する (送った後で設定を消す)。
    - tasks/pushNotificationConfig/get・list・delete は認可の要るメソッド。
    - `<a2a:send-push-notification>` は Task か Message をそのタスクの設定すべてに送る (id は UUID)。
    - 通知の POST は Content-Type: application/json と、token があれば X-A2A-Notification-Token。リダイレクトは追わない。
    - 送り先の名前を引いた結果のアドレスに 1 つでも内側のもの (loopback、リンクローカル (169.254/16、fe80::/10)、
      プライベート (10/8、172.16/12、192.168/16、100.64/10、fc00::/7)、0.0.0.0、::、マルチキャスト、それらを埋め込んだ IPv6) があれば送らず、
      WARN `Push notification refused: '<URL>' resolves to the internal address <アドレス> ..` を出す (mulay だけ)。
      送るときは調べたアドレスにつなぎ (Host と TLS の SNI は URL の名前)、調べた後に名前の向き先を変えられても内側に届かない。
      手元や社内の受け手に送るなら `mulay.a2a.allowPrivatePushUrls=true` (`a2a-push` のシナリオの `%%% jvm`)。
      `<a2a:on-config-accepted>` の additional-headers は送らない (実 Mule でも送られないことを記録で確かめた)。
- クライアント (`<a2a:client-config>`): 最初の操作のときにカードを取り、カードの url を以後の送り先にする。
  要求には `<a2a:authentication>` (http:basic-authentication / digest-authentication。http:request と同じ動き)、
  `<a2a:default-headers>`、requestTimeout / requestTimeoutUnit (既定 30 秒)、HTTPS の `tls:context` (その場のものか
  tlsContext の参照) が効く。サーバーも HTTPS の listener-config に経路を足せる。
  get-card (カードの本文をそのまま。ResponseAttributes)、send-message、get-task、cancel-task
  (`<a2a:additional-properties>` は要求のヘッダ)。JSON-RPC の失敗は
  `A2A:<型>` "Error <code>: <message>" (型は code から)。

- ストリーム (カードの capabilities.streaming。`<a2a:task-stream-listener>` が必須): message/stream は SSE の応答を
  開いて、最初に submitted の task のイベントを送り、task-stream-listener のフローを別に流す。フローの中の
  `<a2a:update-task-status>` / `<a2a:update-task-artifact>` がイベント (`event: 種類` と `data: JSON-RPC の応答`、id は
  文字列) を送り、final の status-update で閉じる。フローが失敗すれば failed の final を送る。
- クライアントの `<a2a:send-stream-message>` / `<a2a:task-resubscribe>`: イベントごとに `<a2a:on-task-status-update>` /
  `<a2a:on-task-artifact-update>` の経路を流し (payload はイベントの data の文字列)、payload は `{"events": [...]}`、
  attributes は StreamingResponseAttributes (finalEventFound)。実 Mule は経路を並行に流すが、mulay は受けた順に流す。

- tasks/resubscribe (サーバー側。認可の要るメソッド。`a2a-resub`): message/stream で始めたタスクにつなぎ直す。
  カードに streaming が無ければ 400 "Streaming not supported for this agent!"、message/send で作ったタスクと
  知らない ID は 404 "Task not found: <id>"。つなぐと SSE の応答で、最初に今のタスク (task のイベント) を送り、
  そのタスクがこれまでに送ったイベント (update-task-status / update-task-artifact のもの) を順に送り直す。
  final の status-update を送った後なら閉じ、途中なら続きのイベントも届いて final で閉じる。
  イベントの JSON-RPC の id は元の message/stream の要求のもの (つなぎ直す要求の id ではない)。
  コネクタが作る failed の final (task-stream-listener のフローの失敗) は記録されない: つなぎ直しても今のタスクだけが届き、
  閉じない。params が無いときの文言には位置が付かない。送り直すためのイベントの記録は最大 1000 タスク分で、古いものから捨てる
  (実コネクタの保持の上限は不明。docs/compat/deviations.md)。

- タスクの記録の置き場所 (`a2a-taskstore`): 既定はプロセスのメモリ。メモリの記録は最後に書き換えてから 1 日で消し
  (実コネクタの既定の店の期限と同じ)、10000 タスクを超えたら終わったタスクの古いものから (足りなければ終わっていないものも) 消す。`<a2a:history taskRepositoryObjectStore="名前"/>` に
  `<os:object-store>` の名前を書くと、その店に実コネクタと同じキーと値でしまう。`task-<taskId>` は TaskRepositoryItem、
  `context-<contextId>` は ContextRepositoryItem (Java のオブジェクト。DW で読むと `^class` と、historyLength /
  streamingContext / contextId / history / taskState / task / pushNotificationConfigs のフィールド)。
  streamingContext は bufferedEvents (eventId / eventType / eventData)、workerInstanceId (`ホスト名..アプリ名`)、requestId。
  店が正本で、`os:remove` で task- を消すと tasks/get は "Task not found" になる。persistent の店なら再起動をまたぐ
  (tasks/get も tasks/resubscribe の送り直しも続く)。`<a2a:task-repository-object-store>` の子要素の形は扱わない。
- on-config-accepted の `authentication` / `proxy-config` / `additional-headers` / `requestTimeout` は、実コネクタ 1.1.1 も
  通知の送信には使わない (`a2a-push-opts`: Authorization は付かず、proxy にも向かわず、時間切れでも再送しない)。
  mulay も使わない。`requestTimeout` (既定 60 秒) は、記録の pushNotificationConfigs の `timeout` (ミリ秒) にだけ入る。

扱わない: `<a2a:task-repository-object-store>` の子要素の形、記録に入る authentication / proxyConfig のオブジェクト。

## MCP (`mcp`、mule-mcp-connector 1.5.0)

比べた版は 1.5.0 (Maven の latest。2026-10-07 時点)。実 Mule 4.11.3 の記録 (`test/fixtures/apps/mcp-tools`、`mcp-rp`、`mcp-sess`、`mcp-client`、`mcp-sse`) に合わせる。
実装は `conn/mcp` (サーバーのプロトコル、セッション、応答の形)、`conn/mcp_schema` (parametersSchema の検査)、`conn/mcp_client` (クライアント)。

### サーバー (`<mcp:server-config>` の `<mcp:streamable-http-server-connection>`)

- Origin の検査 (mulay だけ。streamable-http と旧式の SSE の全部の経路): 要求に Origin ヘッダーがあり、そのホストが loopback
  (localhost、127.x.x.x、[::1]) でなく、`mulay.mcp.allowedOrigins` (カンマ区切りの Origin の完全一致、`*` はすべて) にも無ければ、
  403 (content-type application/json、本文 `{"jsonrpc":"2.0","error":{"code":-32600,"message":"Origin not allowed: <Origin> (mulay.mcp.allowedOrigins)"}}`)。
  Origin の無い要求 (ブラウザでないクライアント) は通す。ブラウザの画面から別のホスト名で呼ぶなら、その Origin を
  `mulay run <app> mulay.mcp.allowedOrigins=https://app.example.com` のように渡す (`mcp-origin`、ADR 118)。
- 設定: `listenerConfig`、`mcpEndpointPath` (既定 /mcp)、`responseContentType` (JSON か SSE。既定 SSE)。serverName / serverVersion は
  initialize の serverInfo。listener-config のポートに経路を足す (POST / GET / DELETE)。
- POST: JSON-RPC。`initialize` (セッションを作り Mcp-Session-Id を返す。protocolVersion は 2024-11-05、2025-03-26、2025-06-18 ならそのまま、
  それ以外は 2025-06-18。capabilities は固定)、`notifications/*` と応答 (202)、`ping`、`tools/list`、`tools/call`、`resources/list`、`resources/read`、`prompts/list`、`prompts/get`、
  `resources/templates/list` (空)、`logging/setLevel` (空の result)、それ以外は -32601 "Method not found: <method>"。
- Accept に、JSON モードなら `application/json`、SSE モードなら `text/event-stream` が無ければ 400 (-32600、大文字小文字を区別し `*/*` も不可)。
- セッション: Mcp-Session-Id が無ければ 500 (-32000 "Cannot process message because this session hasn't been initialized yet")、
  知らない ID は 404 "Session not found"。DELETE は 202 (知らない ID は 404、ヘッダ無しは 400 "Invalid SessionId")。GET は 405。
- 応答: JSON モードは content-type、(initialize だけ) mcp-session-id、mcp-protocol-version。SSE モードは `event: message` の 1 件を
  text/event-stream で返し、常に mcp-session-id を付ける。
- `<mcp:tool-listener>` (name、`<mcp:description>`、`<mcp:parameters-schema>` は必須): tools/call のたびにフローを流す。payload は引数の Map
  (`java.util.Collections$UnmodifiableMap`)、attributes は RequestAttributes (clientCertificate、sessionId、requestId (文字列)、
  additionalProperties (要求ヘッダ、小文字の名前))。`<mcp:responses>` の項目 (text-tool-response-content、image-tool-response-content、
  text-resource-tool-response-content、blob-resource-tool-response-content、`<mcp:audience>`、priority) を成功の後の Event で評価して
  content にする。失敗は `<mcp:on-error-responses>` (無ければエラーの説明の text 1 つ)、isError: true。
- 引数の検査 (parametersSchema): 実コネクタは networknt json-schema-validator。type、enum、minimum、maximum、minLength、maxLength、pattern、
  minItems、maxItems、items、properties、required、additionalProperties (false) を、実 Mule と同じ文言と並び (スキーマの書いた順) で検査する。
  違反は -32602 "Invalid tool parameters: <ptr>: <説明>; ..."。arguments が無ければ "Parameters cannot be null"、オブジェクト以外は Jackson の文言。
- 起動の失敗 (実 Mule と同じ文言): listenerConfig や tool-listener の config-ref が無い (`Referenced component 'X' must be one of stereotypes [..]`)、
  parameters-schema が JSON でない (Jackson の文言)。
- 実 Mule は同じ mcpEndpointPath の 2 つの設定や、tool の無い設定でも起動する。mulay も同じ。
- `<mcp:resource-listener>` (name、uri、resourceMimeType、`<mcp:description>` は必須): resources/read の uri に合うものにフローを流す。payload は
  `{requestedUri}`、attributes は tool と同じ。フローが成功したら `<mcp:resource-listener-content>` の `text-resource` (text) か
  `blob-resource` (blob。文字列を base64 にして返す) を評価して contents にする (uri と mimeType は listener の設定)。知らない uri は
  -32002 "Resource not found" (data は {uri})。uri が無い params は NullPointerException の文言 (-32603)。resources/subscribe、
  completion/complete は -32601。
- `<mcp:prompt-listener>` (name、title、`<mcp:description>`、`<mcp:prompt-arguments>` の `prompt-argument` (name、description、required)、
  `<mcp:messages>`): prompts/get のたびにフローを流す。payload は `{promptName, arguments}`。messages は text-prompt-message-content (text)、
  image-prompt-message-content (mimeType、`image-data/inline-image-data` の imageData。base64 にして返す)、resource-link-prompt-message-content
  (uri、name、description、mimeType、size)、embedded-resource-prompt-message-content (uri、mimeType、`resource-content/` の
  text-embedded-resource か blob-embedded-resource)。role は USER (既定) か ASSISTANT。必須の引数が無い (null も同じ) と -32602
  "Missing required prompt arguments: <名前>"、知らない名前は -32602 "Invalid prompt name" (data "Prompt not found: <名前>")。
  prompts/list は title と description が空なら省き、arguments は常に出す。
- `<mcp:on-new-session-listener>`: initialize のたびに (セッションを作る前に) フローを流す。payload は {clientCertificate、sessionId、additionalProperties
  (要求ヘッダ、小文字の名前)}、attributes は null。フローの失敗は 500 (content-type 無し、本文は `org.mule.runtime.api.exception.DefaultMuleException: <説明>`)。
  成功の後、`<mcp:rejection>` があれば `rejectWithStatusCode`、`rejectWithMessage`、`reject-with-headers` (key と value の式) を評価し、
  rejectWithStatusCode が null でなければ、その状態・本文 (message、無ければ "null")・ヘッダ (書いたものだけ。content-type 無し) で拒否して
  セッションを開かない。null (や属性なし) なら普通に initialize に答える。rejection を書かなければ必ず受け入れる。
- `<mcp:default-response-headers>` (streamable-http-server-connection の中の `default-response-header` key / value。式は使えない): 有効な応答
  (200 と 202。拒否 (400 / 405 / 500 / 404) と DELETE は除く) に付く。JSON モードは先頭、SSE モードは固定のヘッダの後・Mcp-Session-Id の前。
- `<mcp:session-handling sessionIdleTimeout sessionIdleTimeoutUnit sessionsObjectStore>`: mulay は sessionIdleTimeout (既定 5 分) より長く
  要求の無いセッションを消し、その後の要求は 404 "Session not found" になる (クライアントは initialize からやり直す)。
  実 Mule は 10 分待っても (sessionIdleTimeout 2 秒) セッションを切らない (docs/compat/deviations.md)。
  セッションは全部で 10000 までで、超えたら最も長く使われていないものから消す (旧式の SSE のつながっているセッションは消さない)。
  セッションは mulay のメモリに持ち、sessionsObjectStore の中身は使わない。
- resource や prompt のフローの失敗は JSON-RPC の error (-32603、message は説明、data は "DefaultMuleException: <説明>")。

未対応: file-image-data (prompt の画像をファイルから)、rejection の header の value が null のときの 500 (実 Mule は IllegalArgumentException の文言で 500)、
outputSchemaDefinition、parameters-schema の上記以外のキーワード。

### 旧式の SSE (`<mcp:sse-server-connection>` と `<mcp:sse-client-connection>`)

- サーバー: `listenerConfig`、`sseEndpointPath` (既定 /sse)、`messagesPath` (既定 /message)、`<mcp:default-sse-response-headers>` (ストリームの応答に付く)、
  `<mcp:default-message-response-headers>` (POST の 202 に付く)。ツール / resource / prompt の flow と、応答の中身は streamable-http と同じ。
  - sseEndpointPath: どのメソッドでも (GET も POST も) 閉じない SSE を開く。応答のヘッダは content-type: text/event-stream、cache-control、pragma、
    access-control-allow-origin: *。最初のイベント `endpoint` の data が `<messagesPath>?sessionId=<ID>`。
  - messagesPath: POST だけ (他は 405 "Method not allowed for endpoint: <path>")。検査の順は、sessionId (無いか空なら 400 "Missing session id")、
    Content-Type (application/json でなければ 400 "Unsupported content type: <型>"、無ければ `null`)、ストリームが開いているか (503
    "No active SSE connection for sessionId: <ID>")、本文 (JSON のオブジェクトで jsonrpc と method (か result / error) が無ければ 400 "Invalid message format")。
    受け付けたら 202 "Accepted" (Mcp-Protocol-Version はそのセッションの版) を返し、結果は SSE のストリームに `event: message` で流れる。
  - initialize の前の要求は 500 (-32000 "Cannot process message because this session hasn't been initialized yet")。
  - 実 Mule の `-Dmule.http.service.implementation=NETTY` は、シナリオの `jvm` で指定して記録した (docs/fixtures.md)。
- クライアント: `serverUrl`、`sseEndpointPath` (既定 /sse)、`requestTimeout`、`<mcp:default-request-headers>`。最初の操作で GET を開き (別スレッドで読み続ける)、
  最初の endpoint の URL へ POST する (Accept: */*、Mcp-Protocol-Version、User-Agent: Mule HTTP Client)。応答はストリームに届くので id を合わせて受け取る。
  initialize と notifications/initialized は最初の操作で済ませる。つながらなければ `MCP:CONNECTIVITY` "Message endpoint not received"、
  応答が届かなければ `MCP:REQUEST_TIMEOUT`。操作と結果の形は streamable-http と同じ。
- `<mcp:on-new-session-listener>`: sseEndpointPath への接続のたびに (ストリームを開く前に) フローを流す。payload は streamable-http と同じ
  (sessionId は endpoint イベントで知らせる ID)。フローが失敗すると 500、rejection の rejectWithStatusCode が null でなければその状態で拒否する。
  どちらも**本文もヘッダも空**で、rejectWithMessage と reject-with-headers は使われない (実 Mule の記録)。通ればストリームを開く。
- 未対応: sessionIdleTimeout などの session-handling (SSE の接続にはそもそも無い)、サーバーの `requestTimeout`、
  クライアントの `reconnectionDelay`、`authentication`、`tlsContext`。

### クライアント (`<mcp:client-config clientName clientVersion>` の `<mcp:streamable-http-client-connection>`)

- 設定: `serverUrl` (必須)、`mcpEndpointPath` (既定 /mcp)、`requestTimeout` (既定 30)、`requestTimeoutUnit` (既定 SECONDS)、
  `<mcp:default-request-headers>` の `default-request-header` (key / value)。設定ごとに 1 つのセッションを持つ。最初の操作で initialize
  (protocolVersion 2025-06-18、clientInfo は clientName / clientVersion) と notifications/initialized を送り、Mcp-Session-Id を以後の要求に付ける
  (404 ならセッションを作り直して 1 度だけやり直す)。要求のヘッダは Content-Type: application/json、Accept: application/json, text/event-stream、
  User-Agent: Mule HTTP Client、Mcp-Protocol-Version。
- 操作と結果 (Java のオブジェクトの形で、DW で書くとキーの並びも実 Mule と同じ):
  - `call-tool` (toolName、`<mcp:arguments>` の式。無ければ payload、extractStructuredContent 既定 true): payload は `{error, contents: [{audience, data, resource,
    mimeType, priority, type, text}]}`、attributes は `{rawMcpResponse}` (同じ形)。ツールの失敗 (isError) はエラーにならず `error: true`。
    extractStructuredContent が true で、contents が text 1 つ、その先頭の `{` から JSON のオブジェクトが読めるときは、payload がそのオブジェクト
    (後ろに文字が続いてもよい。配列、読めないもの、複数の content、image はそのまま)。image の data と resource の blob は base64 を戻した値。
  - `list-tools` は `[{inputSchema (JSON の文字列)、description、name}]`、`list-resources` は `[{description、mimeType、uri、name}]`、
    `list-prompts` は `[{description、title、name、arguments: [{description、title、required、name}]}]`。attributes は null。
  - `read-resource` (uri) は最初の contents の `{mimeType、uri、blob、text}`。`get-prompt` (promptName、`<mcp:prompt-args>` の式) は
    `{description、messages: [{role (USER / ASSISTANT)、content}]}` (content は type で持つ項目が違い、text なら `{text}`、image なら `{data、mimeType}`)。
  - `ping` は payload と attributes をそのまま残す。target / targetValue は他の操作と同じ。
- 失敗: 初期化で接続できなければ `MCP:CONNECTIVITY`、初期化の応答が 2xx でなければ `MCP:SERVER_ERROR` (どちらも "Client failed to initialize by explicit API call")。
  JSON-RPC の error は code で `MCP:PARSE_ERROR` (-32700)、`INVALID_REQUEST` (-32600)、`METHOD_NOT_FOUND` (-32601)、`INVALID_PARAMS` (-32602、未知の tool / prompt、
  引数の検査、必須の prompt 引数)、`INTERNAL_ERROR` (-32603、リソースのフローの失敗)、`SERVER_ERROR` (-32099 から -32000、未知の resource の -32002 など)、
  それ以外は `JSON_RPC_ERROR`。説明は error の message。
- 未対応: `authentication` (http:basic-authentication など)、`tlsContext`、`additionalProperties` (操作の追加のプロパティ)、
  `streamingStrategy`、エラー型 UNAUTHORIZED / REQUEST_TIMEOUT / INVALID_URI / SCHEMA_VALIDATION_FAILED が起きる条件 (code の対応だけ入れた)。

## secure-properties (`secure-properties`、mule-secure-configuration-property-module 1.3.1)

`<secure-properties:config name file key>` のファイル (`.yaml` / `.properties`。資源のパス) を読み、`![<base64>]` の値を復号して
`${secure::名前}` と DataWeave の `p("secure::名前")` で使えるようにする (mule/props の `load-secure`、復号は lib/secure)。
`![..]` で囲まれていない値はそのまま使う (実モジュールは警告だけ出す)。

- 方式 (実モジュールと mule-encryption 1.9.3 のコードに合わせた): 値は base64 を戻して `<algorithm>/<mode>/PKCS5Padding` で復号する。
  鍵は文字列のバイト列 (AES は 16 / 24 / 32 バイト)。`useRandomIVs` が true なら暗号文の先頭 16 バイトが IV、false なら鍵の先頭 16 バイトが IV
  (ECB は IV なし)。
- 設定: `file`、`key` (`${secure.key}` でシステムプロパティ、`mulay run <app> secure.key=..` でも渡せる)、`fileLevelEncryption` (ファイル全体が
  base64 の暗号文)、子要素 `<secure-properties:encrypt algorithm mode useRandomIVs>` (既定は AES、CBC、**useRandomIVs=false**。実 Mule で確認)。
- 失敗は起動時のエラー: 鍵の長さが不正 `The key is invalid, please make sure it's of a supported size (actual is N)`、鍵違いや壊れた暗号文
  `Could not encrypt or decrypt the data.`、ファイルが無い、`.yaml` / `.properties` でない。**エラーに鍵や復号した値は入れない**。
- 未対応: AES 以外のアルゴリズム (Blowfish、DES、DESede など。OpenSSL 3 の legacy 暗号。起動時に名前を挙げて止める)、RSA (鍵ストア)、
  値の中の `${secure::..}` の入れ子、`encoding`、`expiration-policy`、fips モードの文言。
- 実 Mule は Java 17 では 1.2.5 を読み込めない (Java 8 / 11 まで)。fixture は 1.3.1 を使う (`new-pom.sh <dir> secure`。~/.m2 に無ければ
  `mvn dependency:get -Dartifact=com.mulesoft.modules:mule-secure-configuration-property-module:1.3.1:jar:mule-plugin
  -DremoteRepositories=mulesoft-releases::default::https://repository.mulesoft.org/nexus/repository/releases/` で 1 度取る)。
- 暗号文の期待値は `tools/gen-secure-golden.java` が実クラスで作る。シナリオ: props-secure (2/2)。

## できないこと (コネクタごとの一覧)

実 Mule のコネクタにあって mulay に無いもの。使うと、未対応の操作は `MULE:UNKNOWN` (Unsupported operation)、
未対応のソースと接続は起動時の失敗になる。黙って無視するもの (属性) は「無視」と書く。

### HTTP
- request: 認証 (NTLM、client-credentials 以外の OAuth)、ntlm-proxy。
- multipart: DW の `output multipart/form-data` (`multipart/mixed` など) で組み立てた本文を http:request で送り、listener で受けて読む
  (test/fixtures/apps/http-multipart)。multipart/mixed の writer は Content-Disposition を付けず、reader は名前の無い部分を `part<番号>` と呼ぶ。
- HTTPS (`tls:context`、clay 0.53 の TLS): 待ち受けと要求はできている (https-test)。残り:
  - trust-store の insecure 以外の検証の細かい設定、listener の revocation-check。
  - enabledProtocols は TLSv1.2 / TLSv1.3、enabledCipherSuites は clay.tls の 9 つ (ECDHE と AEAD) から選ぶ (それ以外は捨てる。deviations)。
  - trust-store の無い HTTPS の listener の起動時の文言 ("KeyStore must be configured for server side SSL") は実 Mule で未確認。
  - attributes.clientCertificate の値は、https-test で記録したプロパティ (subjectDN、issuerDN、serialNumber、notAfter、
    type、version、sigAlgName、subjectX500Principal と名前の集合) だけ実 Mule と照合した。extensions などは null。
- listener: `http:basic-security-filter`、`deferredResponse` (無視)。
- `http:load-static-resource` (ADR 117、http-static): `resourceBasePath` (ふつうは `${app.home}/web`) の下のファイルを返す。
  - listener の path (`/static/*` なら `/static`) を requestPath から外し、ベースに付けて `..` を畳む。ベースの外なら HTTP:NOT_FOUND。
  - ディレクトリなら `defaultFile` (既定 index.html) を足す。
  - Content-Type は拡張子の表 (大文字と小文字を区別する。表に無ければ application/octet-stream)。出力には既定の charset (UTF-8) が付く。
  - 無ければ HTTP:NOT_FOUND ("Resource '<path>' was not found."、path は HTML の文字参照に符号化)。
    listener は 404 "Not Found" で返す (エラーが listener の応答の属性を持つため)。操作の後の attributes は null。
  - `${app.home}` の下は、アプリの資源 (プロジェクトなら src/main/resources、JAR なら中身) から読む。ほかのパスはファイルシステム。
- listener の `outputMimeType` / `outputEncoding`: 受け取った本文の DataType を outputMimeType の type/subtype (引数の charset は
  捨てる) と outputEncoding (無ければ UTF-8) に付け替える。要求の Content-Type の charset は引き継がない (core-http-attrs の /out-*)。
- listener の応答の状態コードが 400、408、411、413、414、417、500、501、503、505 なら `Connection: close` を付けて接続を閉じる
  (実 Mule の Grizzly と同じ一覧。core-http-attrs の /conn-close)。
- listener の `responseStreamingMode` (AUTO / ALWAYS / NEVER): ALWAYS は常に `Transfer-Encoding: chunked`、NEVER は Content-Length、
  AUTO は payload が読み残しのストリームのときだけ chunked (DW の output の結果、`file:read`、`streamResponse="true"` の http:request の応答。
  文字列・Java の値・streamResponse でない応答は Content-Length)。実 Mule の記録は test/fixtures/apps/http-stream。
  streamResponse の応答を payload のままフローの最後に返す (AUTO か ALWAYS) と、上流から届いた断片をそのまま listener の応答へ流す
  (中継。ログや DW が先に読むときは全部届くのを待つ。読んだ内容は持つので、何度でも読める)。上流が終わる前に 1 つ目の断片が着くことは
  test/rt/passthrough_test.clay で確かめる (実 Mule とのタイミングの照合はできない)。それ以外のストリーム (DW の output、file:read) は
  全部できてから chunked で送る。

### HTTP request の proxy
`<http:request-connection>` の `<http:proxy-config><http:proxy host port username password nonProxyHosts/></http:proxy-config>`、
または `proxyConfig="名前"` が指す大域の `<http:proxy name=..>`。username があれば `Proxy-Authorization: Basic` を送る。
`nonProxyHosts` は実 Mule の記録 (test/fixtures/apps/http-proxy) に合わせ、コンマで分けて前後の空白を除いた各項目が、宛先のホスト名と
大文字小文字を区別して完全一致したときだけ proxy を使わない。`*.example.com` のようなワイルドカード、`|` や `;` の区切り、
ポート付きの書き方は効かない (すべて proxy を通る)。扱わない: `http:ntlm-proxy`、式で書いた host / port。

### HTTP request の OAuth (`<oauth:client-credentials-grant-type>`、mule-oauth-module)
`<http:request-connection>` の `<http:authentication>` に置く。最初の要求の前に tokenUrl へ POST して (`grant_type=client_credentials`、
`scope` は scopes。clientId:clientSecret は Basic 認証。`encodeClientCredentialsInBody="true"` なら本文の `client_id` / `client_secret`)、
`access_token` を設定ごとに (tokenManager があればその名前で共有して) 持ち、要求に `Authorization: Bearer ..` を付ける。応答が 401 / 403 なら
トークンを捨てて取り直し、1 度だけ送り直す (それでも失敗なら HTTP:UNAUTHORIZED / FORBIDDEN)。取れないときは HTTP:SECURITY:
`Exception when calling token URL '..'.` (接続できない)、`Error response when calling token URL '..'. Response was:\n<応答の Java オブジェクト>\n<本文>` (4xx / 5xx)、
`Could not extract access token or refresh token from token URL '..'. Response was:..` (access_token が無い)。実 Mule の記録は test/fixtures/apps/http-oauth。
未対応: refreshTokenWhen / responseAccessToken などの式の指定、tlsContext、proxyConfig、customParameterExtractors、authorization-code-grant-type。
expires_in は見ない (実 Mule も 401 / 403 で取り直す)。トークンと secret はログにもエラーにも出さない。

### ObjectStore
- `os:object-store` の config-ref (DB などに置く店)、パーティション以外の分離。

### File
- lock (無視)、list の timeBetweenSizeCheck (無視)。
- list の payload は読み込み時に全部読む (実 Mule は触ったときに読む)。parse できないファイルは Binary。
- listener は 1 件ずつ順に流す (並行にしない)。
- ファイルの属性 (所有者・権限) の操作、symlink の追い方の指定。

### APIkit
- apikit:console。
- queryParamsStrictValidation / headersStrictValidation (無視。仕様に無い引数も通す)。
- Exchange の依存 (`api="resource::..."`) で指定した仕様。
- RAML: discriminator、example の検証、ライブラリの中の uses (入れ子のライブラリ)、annotation。
- XML の本文のスキーマ検証 (OAS / RAML のスキーマ付きの XML は実 Mule と同じく cvc-elt.1.a で失敗、
  スキーマ無しは通す)。応答の検証 (実 APIkit もしない)。
- flowMappings による実装フローの対応付け。

### Salesforce
- 接続: saml-connection (起動時に止める)、proxy / TLS の設定。basic-connection と oauth-user-pass-connection は実装済みだが実 Mule と未照合。
- 操作: set-password、reset-password、change-own-password。
- ソース: object listener の triggersQuery。replay listener の FROM_LAST_REPLAY_ID はプロセスの中で覚えるだけ (実コネクタは Object Store)。
- Bulk API とメタデータ API の操作の headers (送らない)、readTimeout (無視)、
  ストリーミングの戦略 (結果は一度に読む)。
- 失敗した項目の exception にスタックトレースは入らない。POJO (describe など) のキーの並びは固定
  (実 Mule は実行ごとに変わる)。search の結果の要素の形は未確認。

### SFTP
- 鍵の認証 (identityFile)、proxy。

### Database
- SQL Server など、SQLite / PostgreSQL / Oracle / MySQL 以外のドライバ。
- MySQL: 利用者の証明書 (clientCertificateKeyStore*)、平文の caching_sha2_password の RSA の鍵交換
  (allowPublicKeyRetrieval)、LOAD DATA LOCAL INFILE、複数のホスト (フェイルオーバー)、サーバー側の prepared statement
  (useServerPrepStmts)、allowMultiQueries。
- XA トランザクション。
- Oracle: 19c 以前、REDIRECT、TCPS、ネットワーク暗号化 (NNE)、配列や OBJECT 型のパラメータ。

### VM
- redelivery-policy (見ない)。

### A2A
- `<a2a:task-repository-object-store>` の子要素の形、記録に入る authentication / proxyConfig のオブジェクト。
- on-config-accepted の authentication / proxy-config / additional-headers / requestTimeout は、実コネクタ 1.1.1 も送信に使わないので、mulay も使わない。

### MCP
- サーバー: file-image-data (prompt の画像をファイルから)、outputSchemaDefinition、parameters-schema の type / enum / minimum / maximum /
  minLength / maxLength / pattern / minItems / maxItems / items / properties / required / additionalProperties (false のみ) 以外のキーワード、
  rejection の header の value が null のときの 500、session ObjectStore の中身、SSE のサーバーの `requestTimeout`。
- クライアント: `authentication`、`tlsContext`、`additionalProperties`、`streamingStrategy`、`reconnectionDelay`、
  エラー型 UNAUTHORIZED / REQUEST_TIMEOUT / INVALID_URI / SCHEMA_VALIDATION_FAILED が起きる条件。
- 実コネクタの不具合らしい挙動 (SSE の拒否で rejectWithMessage と reject-with-headers が届かないなど) は、実 Mule に合わせてある (docs/compat/deviations.md)。

### Salesforce Composite

- oauth-jwt-connection、oauth-saml-connection、config-with-oauth-connection (CONNECTIVITY で失敗させる)。
- proxy と tls:context (mutual TLS の 8443。書けば CONNECTIVITY で失敗させる)、connectionTimeout、maxConnections、
  Content-Encoding: gzip の応答。実コネクタの XSD が手元 (Studio のキャッシュ) に無いので、ignored-attrs の表に入っていない
  (使わない属性を書いても警告しない)。

### Web Service Consumer

- WS-Security の署名・暗号・検証・復号・受け取る Timestamp の検査は `WSC:SECURITY`、http-transport-configuration (requesterConfig)
  は `WSC:CANNOT_DISPATCH` で失敗させる (黙って落とさない)。MTOM と添付 (base64Binary の項目) は扱わない。
- 入力の要らない操作の本文の自動生成 (本文が空なら必ず BAD_REQUEST)。

### Vectors

- 埋め込みの接続は ollama-connection だけ、保存先は ephemeral-file-connection だけ (ほかは操作の失敗)。tlsContext / proxyConfig は読まない。
- transform-parse-document の multiformat (Apache Tika) の読み取り、query-all (ephemeral-file ではもともと使えない)。

### Validation

- validation:config の i18n (bundlePath、locale): 読まない (起動時に警告。文言はいつも既定の英語)。

### Anypoint MQ
- subscriber の `circuitBreaker` (`<anypoint-mq:circuit-breaker>`) とクロスリージョンのフェイルオーバー (`cross.region.failover.feature.enabled`、
  `_fb` のキュー、サービスレジストリの予備のリージョン) は読まない (無視)。
- 接続の tlsContext、proxy、TCP のソケットの設定、reconnection は読まない (無視)。
- subscriber はフローに 1 件ずつ順に流す (実 Mule はフローの maxConcurrency まで並行に流す)。prefetch の手元のロックは、流す直前に
  8 割の時間が過ぎていれば延ばす (実コネクタは 0.5 秒ごと)。
- subscriber を始めるときの失敗 (認証、存在しないキュー) は実 Mule と照合していない (mulay はログに出して 5 秒ごとにやり直す。
  キューが無ければその subscriber を止める)。
- アプリの XML の検査: 実コネクタの XSD が手元 (Studio のキャッシュ) に無いので、ignored-attrs の表に入っていない
  (使わない属性を書いても警告しない)。実 Mule の XSD (mule-maven-plugin がビルドで検査する) には `sendCorrelationId` / `correlationId` は無い。

### jmx (自作モジュール)
- collect-* の値は JVM のものではない (docs/compat/deviations.md)。
- get-recent-logs の `exception` (例外のスタック)。

## 実コネクタの XSD との照合 (2026-10-08)

Anypoint Studio のキャッシュにある XSD (salesforce 11.3.3、file 1.5.6、sftp 2.7.2、db 1.16.3、vm 2.0.2、a2a 1.1.1、
mcp 1.4.0 (1.5.0 の XSD は無い)、http 1.11.3、objectstore 1.3.1、apikit 1.12.6、validation 2.0.8 (2.0.11 の XSD は無い。2026-10-10 に追加)、ms-vectors 1.0.0、wsc 2.2.2) の操作・ソース・接続・属性を、
mulay の `src` に名前が出てくるか (camelCase か kebab-case) で機械的に照合した。名前が出てこないものは読まれない
(未対応の操作は `MULE:UNKNOWN`、未対応のソースと接続は起動時の失敗、属性は無視される)。名前があっても中身が
実コネクタと同じとは限らない (それは各節とシナリオで確かめる)。java / email / jms / sockets / websockets / wsc / ftp などの
mulay が扱わないコネクタは対象外。

**読まない属性は起動時に警告する。** 実 Mule が受け付ける属性なので起動は止めず、`mulay run` と `mulay validate` が
`warning: <file>:<line>: <db:select>: attribute 'queryTimeout' is not supported and is ignored (docs/connectors.md)` と出す
(mule/lint。表は `src/mulay/mule/ignored.clay` で、`tools/ignored-attrs.py gen` が XSD と src から作る。属性を実装したら gen し直す。
`tools/test.sh` は実装済みなのに表に残っているものを検査する)。要素 (`<db:parameter-types>` など) の警告はまだ無い。

操作は、次を除いて XSD の操作がすべて実装されている (file、vm、os は全部):

| コネクタ | 操作・ソース・接続で無いもの |
|---|---|
| Salesforce | set-password、reset-password、change-own-password、`saml-connection` |
| SFTP | list の matcher |
| Database | `data-source-connection`、`derby-connection`、`mssql-connection` |
| A2A | クライアントの set-push-notification-config、get-push-notification-config、list-push-notification-configs、delete-push-notification-config (サーバー側の JSON-RPC は実装済み) |
| HTTP | `basic-security-filter` |
| APIkit | `console` |

読まれない属性 (実コネクタにあるもの):

- **Salesforce**: 全操作の readTimeout / readTimeoutUnit、接続の loginRequestTimeout、objectTTLTimeout、proxyConfiguration、serviceEndpoint
  (basic-connection)、authServerTlsContext / authServerProxyConfig、object listener の triggersQuery、replay listener の autoReplay /
  cacheEventsInMemory / bufferSizeInBytes / throwExceptionWhenOrganizationDailyLimitExceeded、create-batch の batchSobjectMaxDepth、
  invoke-apex-soap-method の apexHeaders。
- **File**: read / write の lock、list の subset、listener の watermarkMode。
- **SFTP**: 接続の identityFile、preferredAuthenticationMethods、sftp-proxy-config、sshConfigOverride、idleTimeout、responseTimeoutUnit、
  kexHeader、prngAlgorithm。read / write の lock、write の writeStrategy / bufferSizeForWriteStrategy。
- **Database**: useColumnNumbers、parameterTypes (`<db:parameter-types>`)、
  insert / update / stored-procedure の autoGeneratedKeysColumnIndexes、接続の transactionIsolation、useXaTransactions、
  columnTypes、cacheQueryTemplateSize、connectionProperties (my-sql-connection のものだけ読む)、generic-connection の driverClassName (ドライバは url で選ぶ)。
- **VM**: listener の transactionType。
- **A2A**: get-card の useExtendedCard、connection の tlsContextRef。
- **MCP**: sse-client-connection の reconnectionDelay / reconnectionDelayUnit、streamable-http-server-connection の sessionsObjectStore
  (セッションはプロセスのメモリだけ)。
- **HTTP**: request-connection の maxConnections、
  connectionIdleTimeout、usePersistentConnections、responseBufferSize、connectivityTest、clientSocketProperties、
  listener の deferredResponse、listener-connection の readTimeout。

## Inference (`ms-inference`、mule4-inference-connector 1.2.0)
実 Mule の記録は test/fixtures/apps/ai-inference。偽の OpenAI 互換の口を同じアプリに置き、コネクタが送る要求も記録した。
接続は `<ms-inference:text-generation-config>` の `<ms-inference:openai-compatible-connection>` だけ。
`apiKey`、`openAICompatibleURL` (末尾に `/chat/completions` をそのまま足す)、`openAICompatibleModelName` (既定 gpt-4o-mini)、`maxTokens` (500)、
`temperature` (0.9)、`topP` (0.9)、`timeout` / `timeoutUnit`、`<ms-inference:custom-headers><ms-inference:default-header key value/>`。
要求は `Authorization: Bearer`、本文は `{model, messages, max_tokens, temperature, top_p[, tools]}`。

- `chat-answer-prompt` (prompt)、`chat-completions` (messages: `{role, content}` の配列)、
  `agent-define-prompt-template` (template / instructions / data: system に `template - instructions`、user に data)、
  `tools-native-template` (上と同じ + tools: 関数定義の配列)。
- prompt / template / instructions / data は String の引数なので、式は値として評価する (出力形式を推論しない。JSON と Java の
  変数を混ぜた `write(..)` も失敗しない: `/mixed`)。messages の各要素は `{role, content}` だけを送る (実コネクタの
  ChatPayloadRecord。tool_calls や tool_call_id は落ちるので、tool の役割のメッセージでツールの結果を返すことはできない)。
- 結果の payload は `{"response": ..}` と `{"tools": [tool_calls]}` (どちらも無ければ省く)。本文は Jackson の空白の無い JSON、
  mime は `application/json; charset=UTF-8`。attributes は
  `{tokenUsage: {outputCount, totalCount, inputCount}, additionalAttributes: {promptFilterResults, contentFilterResults, finishReason, model, id}}`。
  **tools-native-template はツールを実行しない** (LLM が選んだ tool_calls を返すだけ)。ループ (実行して結果を次の data に
  積んで問い直す) はフローで書く (templates/agent-harness)。ツールを実行するのは mcp-tools-native-template (未対応)。
- 失敗: HTTP 429 は `MS-INFERENCE:RATE_LIMIT_EXCEEDED`、他の HTTP の失敗と接続できないときは `CHAT_OPERATION_FAILURE`
  (`Request failed with status code: <n> and message: <本文>`)。応答が JSON でない・choices が空のときは、chat 系は `CHAT_OPERATION_FAILURE`、
  tools-native-template は `TOOLS_OPERATION_FAILURE`。文言は Jackson / Java のもの (JSON の読み取りの失敗は先頭の語から作る簡易版)。
- 接続の失敗の文言は http:request と同じ Mule の HTTP クライアントのもので、末尾の `.` が無い (`Connection refused: localhost/127.0.0.1:18499`、
  相手が切った・RST・本文が途中で切れた・chunk が終わらないときは `Remotely closed`、HTTP でない応答は `invalid version format: HELLO`、
  コロンの無いヘッダ行は `No colon found`)。時間切れは `Timeout exceeded.`。ai-inference の rawserver で記録した。
- 記録していない: 時間切れの文言、usage の無い応答の attributes、content と tool_calls の両方がある応答、tools の中身の検証。

## Validation (`validation`、mule-validation-module 2.0.11)

実 Mule の記録は test/fixtures/apps/validation-ops (217 件)。conn/validation が操作、dw/lib/validation が数・時刻・正規表現の検査と
DataWeave の関数 (dw::Validation)、lib/validate がメール・IP・URL の判定。

- 操作はどれも payload と attributes を変えない。失敗は `VALIDATION:<型>` (親は VALIDATION:VALIDATION、その親は MULE:VALIDATION)。
  説明は message 属性 (空白だけでなければ。式は検査の前に評価し、失敗すれば検査が通っても MULE:EXPRESSION) か、モジュールの既定の文言 (validation-messages.properties)。
  文言の数は MessageFormat の形 (`#,##0.###`、HALF_EVEN: `1,500 is lower that 2,000`、`0.0005` は `0`)。
- 引数の null: 必須の文字列 (email、ip、url、value、regex、time、ipAddress) は MULE:UNKNOWN の "Required parameter '..' was
  assigned with value '..' which resolved to null. ..."。is-not-null / is-null の value と validate-size の value は検査しない
  (validate-size は MULE:UNKNOWN "Cannot check size of a null value")。is-not-blank-string と is-*-collection の既定は payload。
- 判定は実物のライブラリと同じ (golden は tools/gen-validation-golden.java と tools/gen-validation-dw-golden.java が実物で作る):
  - is-email: 前後に空白があれば不可、あとは commons-validator 1.10.1 の EmailValidator (TLD は tools/gen-tlds.java が作る lib/tlds)。
  - is-ip: Guava 33.6 の InetAddresses.isInetAddress。is-url: `new java.net.URL(s)` (JDK 17 の既定のプロトコル。classpath: などは不可)。
  - matches-regex: commons RegexValidator (全体の一致。caseSensitive="false" は CASE_INSENSITIVE)。正規表現の誤りは MULE:UNKNOWN。
  - is-number: commons の Integer/Long/Short/Double/FloatValidator (前後の空白を除き、NumberFormat か DecimalFormat(pattern) で
    全部を読む。記号は COMPAT)。minValue / maxValue は既定のロケール (en) で読み、読めなければ黙って無し。
  - is-time: `DateTimeFormatter.ofPattern(pattern).withLocale(locale).parse(time)` (SMART)。pattern が無ければ MULE:UNKNOWN "pattern"、
    パターンの誤りは MULE:UNKNOWN (Java の文言)。
  - validate-size: Java の値 (mime が application/java か */*) は String の長さ (UTF-16) か要素の数、ほかは DataWeave の sizeOf。
    文言の値はストリームなら `org.mule.runtime.core.internal.streaming.bytes.ManagedCursorStreamDecorator@..` (数は揺れる)、
    JSON の値は整形した JSON、Java の値は toString。
  - is-elapsed / is-not-elapsed: `now < since + Duration.of(time, timeUnit)` で判定。文言の now、Duration、since は Java の toString。
  - is-allowed-ip / is-not-denied-ip: 一覧は子要素 `<validation:allow-list>` / `<validation:deny-list>` (`<validation:ips><validation:ip
    value/>` か ips 属性の式)、または大域の `<validation:ip-filter-list>` を allowList / denyList で指す。ip は IPAddressFactory の
    正規表現で IPv4 / IPv6 と見分け (`010.1.1.1` は可、`::ffff:1.2.3.4` は INVALID_IP)、1〜3 個の数だけの項目は「項目.」を含むか
    (`10` は `110.0.0.1` にも当たる)、ほかはアドレスか CIDR。
- all / any: 子の検査を全部動かし (mule/parse が子を 1 つずつの経路にする)、検査の失敗 (VALIDATION:VALIDATION の子孫) を集める。
  all は 1 つでも、any は全部が失敗すれば VALIDATION:MULTIPLE (説明は子の説明を改行でつないだもの、error.childErrors に子の Error)。
  検査でない失敗 (式の失敗、子の error-mapping で他の型にしたもの) が出たらそこで止めてその失敗を返す。
- 操作の引数を Java の型へ変換できないときの文言 (Collection に JSON のオブジェクトを渡したなど) は実 Mule と同じ
  `"Cannot coerce Object ({a: 1} as Object {encoding: .., mediaType: ..) to Array" evaluating expression: "payload".`
  (rt/engine の coerce-param-err)。
- DataWeave の関数: `Validation::isEmail(s)`、`isIp(s)`、`isUrl(s)`、`matchesRegex(value, regex[, caseSensitive])`、
  `isTime(time, pattern[, locale])`、`isNumber(value, numberType)` (既定のロケール、パターン無し)。どれも Boolean。

## Vectors (`ms-vectors`、mule4-vectors-connector 1.0.0)

実 Mule の記録は test/fixtures/apps/vectors-ops (102 件)。埋め込みは同じアプリの偽の Ollama (`/ollama/api/embeddings`)、保存先は
ephemeral-file。実 Mule のアプリは mule-maven-plugin の additionalPluginDependencies で langchain4j-core と langchain4j (1.1.0) を
足す必要がある (コネクタの pom では provided。tools/mule-oracle/new-pom.sh の `vectors`)。

- 出力はコネクタと同じく org.json の JSON の文字列 (`application/json; charset=UTF-8`、空白なし、キーは Java の HashMap の順、
  数は末尾の `.0` を落とす。メタデータは `new JSONObject(map)` の容量の順)。
- embedding-generate-from-text: 入力 (inputs の文字列の配列) の 1 つごとに `POST {baseUrl}/api/embeddings {model, prompt}` を呼び、
  `{embeddings: [[..]], text-segments: [{metadata: {index}, text}], dimension}` を返す (値は float に丸める)。attributes は
  `{otherAttributes, embeddingModelDimension, tokenUsage, embeddingModelName}`。inputs を書かなければ payload。接続できない・200 でない・読めない応答は
  EMBEDDING_OPERATIONS_FAILURE "Failed to generate embeddings"、入力が空なら "Index 0 out of bounds for length 0"。
- transform-chunk-text: langchain4j の DocumentSplitters.recursive(maxSegmentSizeInChar, maxOverlapSizeInChars) (lib/textsplit)。
  属性を書かなければ 0 で、maxSegmentSizeInChar が 0 以下なら中身をそのまま (application/json として) 返す。式の値が null なら
  MULE:UNKNOWN "Could not create parameter group"。空白だけの text は TRANSFORM_OPERATIONS_FAILURE "text cannot be null or blank"。text は InputStream の引数なので、JSON の文字列を渡すと
  引用符ごと分ける (`#[output text/plain --- payload.text]` と書く)。結果は文字列の JSON 配列、attributes は null。
- transform-parse-document (text-document-parser-parameters): 中身をそのまま text/plain で返す。attributes は `{documentParserName: "Text document parse"}`。
- store-add: 埋め込みの操作の出力を受け、断片ごとに UUID を付け、メタデータに source_id (呼び出しごとの UUID)、ingestion_timestamp
  (エポックミリ秒)、ingestion_datetime (Instant の toString) と metadata-entries を足して `<workingDir>/<storeName>.store`
  (langchain4j の InMemoryEmbeddingStore の Jackson の JSON) に書く。ディレクトリが無ければ STORE_OPERATIONS_FAILURE
  "java.nio.file.NoSuchFileException: <path>"。入力の形が違えば INVALID_PARAMETER (`JSONObject["embeddings"] not found.` など)。
  メタデータは断片のもの、取り込みの項目、metadata-entries の順に重ねる (後のものが勝つ)。text-segments は省けるが、断片の数が
  埋め込みの数と違えば "The list of ids and embeddings and embedded must have the same size"。結果は `{sourceId, embeddingIds, status: "updated"}`。
- query: InMemoryEmbeddingStore.search と同じ (スコアは (cos + 1) / 2、積は float、PriorityQueue で上位 maxResults、同じスコアの並びも同じ)。
  ファイルが無ければ空の結果。入力の断片が 2 つ以上・埋め込みが 1 つでなければ INVALID_PARAMETER ("You must provide one .. only.
  Received: n")、ベクトルの長さが違えば "Length of vector a (n) must be equal to the length of vector b (m)"。結果は
  `{minScore, question, sources: [{score, metadata, embeddingId, text}], response (text を空行でつなぐ), maxResults, storeName}`
  (断片が無ければ question は無い)。maxResults が 0 以下、minScore が 0〜1 の外なら langchain4j の文言の STORE_OPERATIONS_FAILURE。
- store-remove: ids (の配列) か condition で消す。どちらも無ければ保存先のファイルごと消す。結果は `{status: "deleted"}`、
  attributes の ids に配列。ids と condition を両方書くと実 Mule はビルドで断る (mulay は ids を使う)。
- query-all: ephemeral-file では実コネクタと同じく STORE_UNSUPPORTED_OPERATION "File iteration is not supported for this vector store."。
- メタデータの条件 (condition): 実コネクタの MetadataFilterHelper.fromExpression と同じ文法 (`key op value`、op は = != > >= < <=、
  `CONTAINS(key, value)`、括弧、AND / OR を同じ階層で混ぜると失敗)。値は引用符を外し、数の形なら Long / Double。実コネクタの
  不具合もそのまま: AND / OR の右側の条件はキーが演算子の最後の 1 文字 ("D" / "R") になるので、AND は成り立たず、OR は左側
  だけが効く。比べ方は langchain4j (型が違えば "Type mismatch: .." の STORE_OPERATIONS_FAILURE)。文法の誤りは
  "Error building metadata filter: .." の STORE_OPERATIONS_FAILURE (空の条件は "Expression cannot be null or empty")。

## Web Service Consumer (`wsc`、mule-wsc-connector 2.2.2)

実 Mule の記録は test/fixtures/apps/wsc-ops (206 件)。同じアプリに偽の SOAP サービス (`/soap/<11|12>/<mode>`、応答は resp.dwl) を置き、
送った要求のヘッダーと本文のバイト列 (GET /last) まで照合する。実物の SOAP エンジン (mule-soap-engine 2.4.0、CXF 4.1、wss4j 4) の
書き方に合わせた。

- config: `<wsc:connection wsdlLocation service port [address] [soapVersion]>`。属性は式でもよく、consume のたびに評価する
  (動的な config)。WSDL は最初の consume で読み、場所ごとに覚える (32 件まで。読めなかったものは覚えない)。読むのは
  lib/wsdl (mule-wsdl-parser 1.4.11 と同じ結果)。場所はアプリの資源、`file:`、`http(s):`、在るファイルの絶対パスと作業ディレクトリ
  からの相対パス。import は文書からの相対。
  - 場所が分からない: `WSC:INVALID_WSDL` ("Error fetching the resource [x]: Cannot resolve URL: [x]")。XML や WSDL の誤りも
    `WSC:INVALID_WSDL` ("Error processing WSDL file [<URL>]: .."、wsdl4j / Xerces の文言)。
  - `file:` や `http(s):` の文書を読めない: `WSC:CONNECTIVITY` ("..:org.mule.wsdl.parser.exception.WsdlGettingException: Error
    Getting the resource [<URL>]: <path> (No such file or directory)" / "Connection refused" / 404 なら URL)。import の文書を読めないときは、実物と
    同じく CXF の NullPointerException の文言。
  - rpc の WSDL (binding のどれかが style="rpc")、service / port が無い、宛先が無い: `WSC:CONNECTIVITY`
    ("Error trying to acquire a new connection:..")。SOAP の binding でない port は無いものとして扱う。
  - 操作が無い: `WSC:BAD_REQUEST` ("The provided operation [x] does not exist in the WSDL file [<URL>]")。
  - 封筒の版は config の soapVersion だけで決まる (port の binding は見ない)。宛先は address、無ければ port の soap:address。
- 要求:
  - 封筒は `<soap:Envelope xmlns:soap=".."><soap:Header>..</soap:Header><soap:Body>..</soap:Body></soap:Envelope>`
    (宣言なし。forceXMLProlog なら `<?xml version='1.0' encoding='<charset>'?>`)。
  - 本文 (`<wsc:body>`、書かなければ payload) は読んで書き直す。名前空間の宣言は書いたまま、文書の外のコメントは残し、
    処理命令と宣言は落とす。空の要素は `<x/>`。エスケープは Woodstox (文字データは `&` `<` と先頭か `]]` の後の `>`、属性は `&` `<` `"`)。
    読めない本文は `WSC:BAD_REQUEST` ("..the request body is not a valid XML")、空なら "Cannot build default body request..".
  - `<wsc:headers>` は根が `headers` の XML で、子要素を soap:Header に写す (WS-Security の後)。
  - HTTP のヘッダー: content-type、soapaction (WSDL の soapAction。属性が無ければ送らない)、transport headers を小文字の名前で
    commons-collections の CaseInsensitiveMap に入れた順 (後のものが上書き)。本文は Transfer-Encoding: chunked で送る。1.1 は `text/xml; charset=..`、1.2 は
    `application/soap+xml; action=..; charset=..` を jakarta.mail の書き方 (token でなければ引用符、76 文字で折り返し、60 文字を
    超える値は action*0 / action*1) で。charset は本文の DataType の charset。
  - WS-Security: `wsse:Security` (soap:mustUnderstand は 1.1 で "1"、1.2 で "true"、actor は soap:actor / soap:role)、UsernameToken
    (DIGEST は Base64(SHA-1(nonce + created + password)) で Nonce と Created を必ず付ける。TEXT の Created は addNonce に従い、
    addCreated だけでは付かない: 実 Mule の記録)、Timestamp (Created と Expires、ミリ秒)。
- 応答: payload は SoapOutputEnvelope `{body, headers, attachments}`、attributes は SoapAttributes
  `{additionalTransportData: {reasonPhrase, statusCode}, protocolHeaders}` (protocolHeaders は小文字の名前の CaseInsensitiveMap の順)。
  - body は Body の最初の要素から末尾の空白の手前までを書き直したもの (application/xml)。名前空間は要る所で宣言し直す。
    headers は Header の子要素ごとに `<?xml ..?>` と祖先の宣言すべて (接頭辞の順) を付けたもの。
  - 読む charset は応答の Content-Type、無ければ要求の charset (XML の宣言は見ない)。HTTP の状態コードは見ない。
  - 一方向の操作 (output の無い操作) は応答を見ない (body は空の `*/*`)。
- 失敗:
  - Fault は `WSC:SOAP_FAULT` (description は faultstring / Reason)。`error.errorMessage.payload` は SoapFaultException
    (faultCode と subCode は QName、reason、detail は宣言付きの XML の文字列、role、node)。
  - Content-Type が text/html なら空の文言の SOAP_FAULT。根や Header の前で XML が読めなければ Woodstox の文言の SOAP_FAULT
    ("Error reading XMLStreamReader: .."、faultCode は Client / Sender)。根が SOAP でなければ VersionMismatch。
  - Body の中で読めなければ `WSC:BAD_RESPONSE`、Body に要素が無ければ `WSC:EMPTY_RESPONSE`、Body が無い・同じ名前の Header は
    `MULE:UNKNOWN` ("Unexpected error while consuming web service: ..")。
  - 接続できない: `WSC:CANNOT_DISPATCH` ("Connection refused: host/ip:port")、時間切れ (既定 5 秒、
    default-http-transport-configuration の timeout): `WSC:TIMEOUT` ("The SOAP request timed out")。

## gRPC (`grpc`、mule-grpc-connector 1.0.4)

- クライアントの `<grpc:unary-call config-ref method="pkg.Service/Method">` (`<grpc:content>` と `<grpc:request-headers>`)。
  config は `<grpc:client-config>` の `<grpc:no-auth-connection host port>` に `<grpc:idl-definition><grpc:single-binary-protobuf
  protobufDescriptorFile=".."/>` (protoc の `--descriptor_set_out` で作った記述子) と `<grpc:connection-mode><grpc:plain-text/>`。
- 送る本文は content のバイト列のまま (ふつうは `output application/x-protobuf descriptorUrl=.. messageType=..` で書く)。
- 結果の payload は `*/*` の TypedValue。DW で読むと、記述子の出力の型の protobuf として読める (DW の protobuf 形式は
  docs/dw-formats.md)。listener の応答や次の unary-call の content にはそのまま渡せない (実 Mule と同じく失敗する)。
- 失敗は `GRPC:<status の名前>`。応答の読み方と、実 Mule が止まる応答の扱いは ADR 077。
- サーバーの `<grpc:unary-method config-ref methodName>` (`<grpc:response-unary>` と `<grpc:error-response statusCode description>`)。
  config は `<grpc:server-config [maxInboundMessageSize]>` の `<grpc:grpc-server-connection listenerConfig>` に記述子。listener は
  `<http:protocol-support><http:http2-support enable="true"/>` を書いたものだけ h2c を受ける。payload は要求のメッセージで、DW で読むと
  入力の型の protobuf。応答は response-unary の値 (無ければ payload) のバイト列。細かい規則は ADR 079。
- サーバーのストリーミング (server-streaming-method と send-stream-message / end-stream、client-streaming-method、
  bidirectional-streaming-method) は、メッセージが届くたびにフローを動かし、応答のメッセージもそのつど送る (h2c。ADR 079)。
  クライアントのストリーミングは gRPC として正しく流す (送るたびに送り、届くたびに渡す)。実 Mule のコネクタは溜めて 1 回で送るので、
  ここは実 Mule と違う (ユーザーの判断。ADR 080)。`<grpc:deadline>` に対応。server-streaming-subscriber-source は未対応。

## Salesforce Composite (`salesforce-composite`、mule-salesforce-composite-connector 3.1.4)

実 Mule の記録は test/fixtures/apps/salesforce-composite (99 件。同じアプリに偽の Salesforce を置き、token-connection で
つないで送った要求 (GET /last) まで照合) と salesforce-composite-org (12 件。本物の org に client-credentials でつなぐ)。

- 接続: `token-connection` (sessionId、instanceUrl。トークンを取りに行かない)、`oauth-client-credentials-connection`
  (トークンは Salesforce コネクタと同じ取り方)、`oauth-user-pass-connection` (同じ。未照合)。instanceUrl はそのまま使う。
  接続の属性は式でもよい (動的な config。操作のたびに評価する)。proxyHost と tls:context は扱わないので、書けば
  CONNECTIVITY で失敗する。
  API の版は 67.0 (実コネクタに書き込まれていて変えられない)。応答の時間切れは responseTimeout (既定 5 秒)。
- 要求: ヘッダーは `authorization: Bearer <token>` と `content-type: application/json` (GET でも)、本文は chunked で
  Jackson と同じ JSON (Map はフィールドの順、文字列は " \ と制御文字だけ逃がす、小数は Double の書き方)。
  - create-sobject-tree は `{"records": ..}`、execute-composite-batch は `{"batchRequests": ..}` (haltOnError は送れない)、
    execute-composite-graph は `{"graphs": ..}`、get-sobject-collections は POST の `{"ids": .., "fields": ..}`、
    delete-sobject-collections は DELETE の `?ids=a,b&allOrNone=..` と本文 `null`。
  - 日時の値は送れない (TRANSFORMATION "Java 8 date/time type `java.time.ZonedDateTime` not supported by default: ..")。
- pre-* (HTTP を使わない): 部分要求の HashMap `{richInput, method, url}` (Java 17 の HashMap の順)。pre-create / pre-update は
  `new HashMap(sObject)` から Id と fieldsToNull を除き、fieldsToNull の名前を null で足す。pre-update の method は
  HttpConstants$Method の PATCH。pre-query の parameters は ":名前" をそのまま置き換え、URL は URLEncoder の書き方。
  空の id / query / search は VALIDATION "Parameter 'x' is Empty."、pre-retrieve の Id / Fields / Type の誤りも VALIDATION。
- post-* (HTTP を使わない): statusCode が 400 以上なら `{errors: result}`。post-create / post-retrieve は result、
  post-update / post-delete / post-get-limits は部分応答そのもの、post-search は result.searchRecords。
  post-query / post-query-all は records と、nextRecordsUrl のページを直接 GET したもの (失敗した問い合わせは空)。
- 応答: tree / batch / graph の最上位は HashMap、ほかは LinkedHashMap と ArrayList。数は Integer / Long / BigInteger / Double。
  attributes は HashMap `{status-code, headers}`。
- 失敗 (SALESFORCE-COMPOSITE): 2xx でなければ UNKNOWN "Invalid status code: N, response body: <本文>"。本文に期限切れの文言
  ("Session expired or invalid" など 7 つ) があるか、401 の配列の最初の errorCode が INVALID_SESSION_ID なら CONNECTIVITY
  "Invalid session Id" (client-credentials は取り直して 2 回までやり直す)。401 のほかの配列は本文が空の UNKNOWN。
  JSON の誤りは TRANSFORMATION (Jackson の文言と位置)、型が合わなければ UNKNOWN (ClassCastException の文言)、空の本文は
  UNKNOWN "Empty stream came as response"、時間切れは "Timeout exceeded" (collections と composite request は CONNECTIVITY、
  ほかは UNKNOWN)、つながらなければ UNKNOWN "Connection refused: host/ip:port"。

## Salesforce Pub/Sub (`salesforce-pub-sub`、mule4-salesforce-pubsub-connector 1.4.2)

実 Mule の記録は test/fixtures/apps/salesforce-pubsub (25 件。d30 の org、Platform Event MulayPubSub__e と、SyncItem__c の CDC)。設計は ADR 088。

- 接続: `<salesforce-pub-sub:pubsub-config>` の `oauth-client-credentials-connection` (子に `oauth-client-credentials`)、
  `oauth-user-pass-connection`、`basic-connection`、`jwt-connection`、`config-with-oauth-connection`。認証は Salesforce コネクタと同じ。
  gRPC の宛先は接続の `host` / `port` (既定 api.pubsub.salesforce.com:7443)。`publishRequestTimeout` / `publishRequestTimeoutUnit` は
  publish の期限 (過ぎたら TIMEOUT)。
- `publish-event topic` (events は既定 `#[payload]` の Map の配列): 結果は HashMap の ArrayList
  (`correlationKey`、`eventBody`、`hasError`、`error`、`replayId`)。値は項目の Avro の型に合わせて変える。失敗の型と文言は実 Mule と同じ
  (必須の項目が無い: INVALID_INPUT、union に合わない値やスキーマに無い項目: MULE:UNKNOWN、gRPC の失敗: 状態の対応表)。
- `subscribe-channel-listener channelName eventBatchSize` と `<salesforce-pub-sub:replay-option>` の子 (`earliest`、`latest`、
  `custom-replay-id replayId`、`replay-id-from-object-store osName osKey`)。payload は EventDTO (`eventId`、`replayId`、`event`)、
  attributes は null。`event` の数はすべて Double (実 Mule と同じく Gson を通した形)。CDC の bitmap は項目名に展開する。
- できないこと: proxy、TLS の設定、`inactivityWatchdogSchedulerFrequency`、`saml-connection`、`unauthorize` (何もしない)。

## jmx (`jmx`、自作モジュール com.demo-group:mule-jmx-module 0.1.0)

MuleSoft の公式コネクタではなく、ログを HTTP から読むための自作モジュール (ソースは `/mnt/tmp/mule-jmx-module`)。
別のプロジェクト (エージェントの管理画面) の `/logs` 系が使う。実装は `conn/jmx`、ファイルを読む部品は `lib/logfile`、
最近のログのバッファは `rt/log` の ring。期待値は実 Mule の記録 (`test/fixtures/apps/jmx-logs`、`jmx-small`)。

- 結果はどれも JSON の文字列 (`application/json; charset=UTF-8`)。キーの並びと JSON の逃がし方は実モジュールの JsonUtil と同じ。
- `<jmx:config logBufferSize="5000" logDir=".."/>`。logDir が無ければ `mule.home` (アプリのプロパティ、無ければ環境変数 MULE_HOME) の `logs`、
  無ければ `/opt/mule/logs` (あれば)、無ければ `logs`。
- `get-recent-logs` (lines 100、level、pattern): バッファの最後の lines 件 (0 以下なら全部)。level はそれ以上 (小文字でもよい。知らない名前は全部)、
  pattern は message と logger に大文字小文字を区別せず含むもの。{bufferCapacity, bufferSize, count, entries[{timestamp, epochMillis, level, logger,
  message, thread}]}。バッファに入るのはアプリが出したログ (logger、エラーのログ。カテゴリのレベルの規則は rt/log のまま) で、mulay 自身のログ
  (`mulay.*`) は入れない。例外のスタック (`exception`) は持たない。
  - 実モジュールは appender に固定の名前を付けるため、バッファに入るのは**最初の `<jmx:config>` だけ**。2 つ目以降は bufferSize 0 のまま (同じに合わせた)。
  - thread は mulay では `[アプリ名].フロー名` (実 Mule は Mule のスレッド名)。
- `list-log-files`: {logDir, files[{name, size, lastModified}]}。通常のファイルだけを名前順に。ディレクトリが無ければ空。
- `tail-log-file` (fileName、lines 100): {file, lines, content[]}。後ろから読み、バイトを 1 文字ずつ (ISO-8859-1 として) JSON にするので、
  UTF-8 の日本語は文字化けして出る (実モジュールの癖。同じに合わせた)。\r は残す。末尾の改行は 1 つだけ読み飛ばす。lines が 0 以下なら空。
- `search-log-file` (fileName、pattern、lines 50): {file, pattern, matches, content[]}。UTF-8 として読み、大文字小文字を区別せず含む行の最後の lines 件。
  lines が負なら実モジュールと同じく範囲外で失敗する (`MULE:UNKNOWN` "fromIndex(2) > toIndex(1)")。
- ファイルが無い、通常のファイルでない: 失敗ではなく `{"error":"Log file not found: <パス>"}`。fileName と pattern が null なら `MULE:UNKNOWN`
  "Required parameter '..' was assigned with value '..' which resolved to null. Required parameters need to be assigned with non null values"。
- `fileName` が絶対パスか `..` を含むときは読まず `{"error":"Invalid log file name: .."}` (実モジュールは logDir の外も読む。docs/compat/deviations.md)。
- collect-metrics / collect-cpu / collect-memory / collect-gc / collect-threads: キーの構造は実モジュールの MetricsCollector と同じ JSON
  (jmx-metrics が値を型に直して実 Mule と照合)。値は mulay のプロセスと OS (/proc) のもの:
  os は uname・/proc/meminfo・/proc/loadavg、cpu は /proc/self/stat と /proc/stat の差分 (前に呼んだときから。初回は起動から)、
  memory の heap は匿名メモリ (RssAnon)、nonHeap はファイルに載ったメモリ (RssFile)、threads は /proc/self/status の Threads、runtime の pid と uptime。
  JVM にだけある memoryPools / gc / bufferPools / inputArguments は空、classLoading は 0。
- 扱わない: lines が数でないときの `MULE:EXPRESSION` の文言 (実 Mule は DataWeave の変換エラーの文言)、読めないファイル/壊れた UTF-8 の細かい文言。

## Anypoint MQ (`anypoint-mq`、anypoint-mq-connector 4.0.23)

実コネクタ (と、それが使う anypoint-mq-rest-client 5.1.500) と同じ REST をブローカーに送る (conn/anypoint_mq。URL と JSON と
ackToken は conn/amq_wire、期待値は tools/gen-amq-golden.java が実物から作る test/amq)。実 Mule の記録は本物のブローカー
(組織 T1、Sandbox、ap-northeast-1) に対する `test/fixtures/apps/anypoint-mq-ops` (操作、77 件) と `anypoint-mq-sub` (subscriber、31 件)。
認証情報 (各アプリの `src/main/resources/mq-secret.yaml`: mq.url、mq.clientId、mq.clientSecret) はリポジトリに入れない
(作り方はシナリオの note。無ければ `mule-oracle` はこのアプリを飛ばす)。

- 接続: `<anypoint-mq:config>` の `<anypoint-mq:connection url clientId clientSecret>`。url は `https://mq-<region>.anypoint.mulesoft.com/api/v1/organizations/<組織>/environments/<環境>`
  の形でなければ ANYPOINT-MQ:CONNECTIVITY "Invalid api url provided <url>" (実コネクタの検査と同じ)。最初に使うときに
  `GET <base>/serviceRegistry` で認証サーバーを得て、`POST <認証>/oauth2/token` (client_credentials。5 回まで、422 なら `/api/v2/oauth2/token`)
  でトークンを取る。取れなければ CONNECTIVITY (401 と 5xx は "Failed to connect with Anypoint MQ Service: [401] Unauthorized"、ほかは
  "An error occurred while executing the operation: AUTHORIZE AGAINST AUTH SERVER. Cause: Can not login into Authentication Server .."。
  トークンの口は 1 分ほどに 10 回までで、超えると 429)。トークンは設定ごとに持ち、ブローカーが 401 なら取り直して 1 度だけ送り直す。
  起動のときに各設定の接続を裏で用意しておく (トークンは 1 回だけ試し、失敗は覚えない)。
- 要求は HTTP/1.1 (失敗の文言にブローカーの理由句が入る) で、接続を使い回す。5xx・429・通信の失敗は、プロパティ
  `max.retries.failure.operation` (既定 5) 回まで、1 秒から倍々 (最大 30 秒、`object.store.client.back.off.initial.wait` /
  `multiplier` / `max.interval`) に [1, 2) の揺らぎを掛けて待ってから送り直す (実 Mule は -D のシステムプロパティ、mulay はアプリの
  プロパティ。`%%% jvm -D..` はどちらにも効く)。User-Agent は実コネクタと同じ。
- publish (`destination`、`<anypoint-mq:body>` (無ければ payload)、`<anypoint-mq:properties>`、`messageId` (無ければ UUID)、`messageGroupId`、
  `deliveryDelay` / `deliveryDelayUnit`、`sendContentType` (既定 true)): `PUT .../destinations/<名前>/messages/<id>` に
  `{"body", "headers", "properties"}` (Gson の書き方、headers と properties は HashMap の順)。本文は payload のバイト列を UTF-8 として読んだ
  文字列 (Binary は壊れる。実コネクタと同じ)。sendContentType なら properties に `contentType` (payload の DataType の mime をそのまま) と、
  mime に charset があれば `MULE_ENCODING`。ユーザーのプロパティはその後に足す (同じ名前なら上書き)。値は文字列・数 (そのまま)・真偽
  (文字列 "true")。null は MULE:UNKNOWN "Property value can not be null"、Object や Array は MULE:UNKNOWN "Property value accept only string
  or number or boolean as values"。結果: payload は本文 (`*/*` のストリーム)、attributes は AnypointMQMessagePublishAttributes {messageId}
  (ブローカーの答えた ID)。交換 (exchange) にも送れる。検査の順は接続 → messageGroupId (`^[a-zA-Z0-9\p{Punct}]{1,128}$`。
  ILLEGAL_MESSAGE_GROUP_ID) → 本文が null (ILLEGAL_BODY) → deliveryDelay が 0〜900000 ミリ秒の外 (ILLEGAL_DELAY)。413 は ILLEGAL_BODY。
- consume (`destination`、`acknowledgementMode` IMMEDIATE (既定) / MANUAL、`acknowledgementTimeout` (lockTtl)、`pollingTime` (既定 10000、0〜20000 ms
  でなければ CONSUMING)): `GET .../messages?pollingTime=..&lockTtl=..` (0 は送らない。pollingTime を送らなければブローカーは 10 秒待つ)。
  何も無ければ pollingTime > 0 なら ANYPOINT-MQ:TIMEOUT "Failed to retrieve a Message. Didn't receive any message during polling interval of
  '<ms>' milliseconds"、0 なら payload も attributes も null (payload の ^mimeType は `*/*`)。IMMEDIATE は受けてすぐ ACK (失敗は ACKING
  "Failed to perform the IMMEDIATE ACK of ..")。payload は本文 (UTF-8 のバイト列のストリーム)。mime は contentType のプロパティ (無ければ `*/*`。
  DW の知らない mime なら Binary)、outputMimeType / outputEncoding があればそれ。
  attributes は AnypointMQMessageAttributes: headers (ブローカーの headers を HashMap の順: lockId、created、messageId、ttl、deliveryCount、
  messageGroupId、deliveryDelay)、destination、messageId、ackToken (MANUAL のときだけ。ほかは null)、deliveryCount (Integer)、contentType、
  properties (HashMap の順。数は Long か Double、真偽は文字列) の並び (実 Mule の bean の並び)。
- ack / nack (`ackToken`): ackToken は `{"destination","messageId","lockId"}` (Gson、`=` は `\u003d`) の Base64。ACK は
  `DELETE .../messages/<id>` に `{"lockId"}`、NACK は `DELETE .../messages/<id>/locks/<lockId>` (すぐ再配信され、deliveryCount が増える)。
  void (payload と attributes はそのまま)。同じ ackToken の ACK は 2 度目も成功、ACK の後の NACK は 400 (NACKING "..LockId: .. provided
  is expired")。空白だけ・空は ACKING / NACKING "Invalid token: The 'ackToken' cannot be an empty String"、null は MULE:UNKNOWN "Required
  parameter 'ackToken' ..."、読めないものは "The provided ackToken '<t>' is invalid and could not be decoded: <java.util.Base64 か Gson の文言>"、
  中身の欠けたもの (null の欄) は実物と同じ NullPointerException の MULE:UNKNOWN。ブローカーの 500 は送り直した後に ACKING / NACKING。
- subscriber (ソース。`destination`、`acknowledgementMode` AUTO (既定) / MANUAL / IMMEDIATE、`acknowledgementTimeout`、`<anypoint-mq:subscriber-type>`
  の `<anypoint-mq:prefetch maxLocalMessages>` (既定) か `<anypoint-mq:polling fetchSize>` と `<scheduling-strategy><fixed-frequency>`、
  outputMimeType / outputEncoding): prefetch は裏で min(maxLocalMessages, 10) 件ずつ 20 秒の long poll で取り (lockTtl は
  acknowledgementTimeout、0 なら 120 秒)、polling は周期ごとに fetchSize 件を取る。AUTO はフローが成功 (on-error-continue で扱った失敗を含む)
  すれば ACK、失敗 (on-error-propagate) すれば NACK (キューの maxDeliveries を超えれば dead-letter queue へ)。IMMEDIATE は流す前に ACK
  (フローが失敗しても再配信されない)。MANUAL はフローが ack / nack し、どちらもしなければ acknowledgementTimeout の後に再配信。
  フローの correlationId は新しく作る (messageId ではない)。止めたプロセスの long poll はブローカーに 20 秒ほど残り、その間に届いた
  message を取ってロックすることがある (実 Mule も同じ)。
- 失敗の型 (ANYPOINT-MQ): PUBLISHING、CONSUMING、ACKING、NACKING、DESTINATION_NOT_FOUND (404。親はどれも ANY)、ILLEGAL_MESSAGE_GROUP_ID /
  ILLEGAL_BODY / ILLEGAL_DELAY (親は PUBLISHING)、TIMEOUT (親は CONSUMING)、CONNECTIVITY (親は MULE:CONNECTIVITY)。文言は
  "Failed to publish message to destination '<名前>': An error occurred while executing the operation: SEND ONE MESSAGE. Cause: 404 - Not Found
  (<ブローカーの本文>)." の形 (操作ごとに RECEIVE MESSAGES、ACK ONE MESSAGE、NOT-ACK ONE MESSAGE)。交換から consume すると 400 の CONSUMING。
- FIFO のキュー: messageGroupId ごとに送った順に受ける。同じ messageId は 5 分の間は重複として捨てられる (ブローカーの規則)。
- 時間 (2026-10-12、ap-northeast-1、同じアプリ anypoint-mq-ops の /perfpub・/perfcon、50 件、3 回): 実 Mule は publish 30.6〜33.2 ms/件、
  consume (IMMEDIATE) 53.4〜55.7 ms/件。mulay は publish 24.8〜29.1 ms/件、consume 44.6〜47.2 ms/件。起動してから最初の publish まで
  実 Mule は約 9.3 秒 (デプロイ 9.1 秒)、mulay は約 0.5 秒。subscriber (anypoint-mq-sub、AUTO、20 件を送って最後の 1 件がフローに届くまで)
  は実 Mule 0.88〜1.05 秒、mulay 0.58〜0.65 秒。
