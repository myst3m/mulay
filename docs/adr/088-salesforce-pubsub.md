# ADR 088: Salesforce Pub/Sub コネクタ (salesforce-pub-sub)

日付: 2026-10-22。状態: 決定。対象は mule4-salesforce-pubsub-connector 1.4.2 (`com.mulesoft.connectors`)。

## 背景

- Salesforce は、新しいイベント連携に Pub/Sub API (gRPC、`api.pubsub.salesforce.com:7443`、イベントの本体は Avro) を勧めている。
- 実 Mule の公式コネクタの内容:
  - 操作は `publish-event`。
  - source は `subscribe-channel-listener`。
  - replay の指定は `earliest` / `latest` / `custom-replay-id` / `replay-id-from-object-store`。
- XML の名前は、bytecode の注釈 (`@Alias`) とドキュメントから取った。
- 振る舞いは、逆コンパイルしたコードと実 Mule での記録から取った (fixture salesforce-pubsub)。

## 決定

### 接続

- 接続の要素 (`oauth-client-credentials-connection` など) は、Salesforce コネクタと同じ形である。
  - 認証は conn/sf_core の `auth-of` / `session` をそのまま使う (client credentials、ユーザーとパスワード、basic、JWT、認可コード)。
- gRPC の頭に付けるもの: `accesstoken`、`instanceurl`、`tenantid`。
  - tenantid は org の ID で、REST の `SELECT Id FROM Organization` で 1 度だけ読む。
  - 実 Mule は `x-sfdc-*` の名前で送るが、Pub/Sub API はどちらの名前も受ける。
- 接続の要素の `host` / `port` / `publishRequestTimeout(Unit)` を読む。
- status が UNAUTHENTICATED のときは、ログインし直して 1 度だけ送り直す。

### publish-event

- GetTopic で schema ID を、GetSchema で Avro のスキーマを得る。
  - どちらも topic と ID ごとにプロセスの中に覚える。
  - 実 Mule は publish のたびに問い合わせる。スキーマが変わったときは、mulay は再起動するまで古いスキーマを使う。
- events は `java.util.List<Map>` として読む。配列でなければ MULE:EXPRESSION "Cannot coerce .. to Array" になる。
- 1 件ごとの Map を、スキーマの record に入れる。手順は実 Mule (`generateProducerEvent`) と同じ。
  - 値が数なら、項目の型 (union なら null 以外の最初の型) に合わせて int / long / double / float に変える。小数を long に入れると切り捨てる。
  - 数以外は、そのまま入れる。
- エンコードの失敗 (実 Mule の記録):
  - 必須の項目が無い: SALESFORCE-PUB-SUB:INVALID_INPUT "null value for (non-nullable) long at <Record>.<field>"。
  - スキーマに無い項目に数を入れた: MULE:UNKNOWN (Avro の getField が null を返したときの NullPointerException の文言)。
  - union に合わない値: MULE:UNKNOWN "Not in union [..]: <値> (field=<名前>)"。
- 結果は `ArrayList<HashMap>` で、各要素の項目は次のとおり。HashMap の並びは jhash で決める。
  - `correlationKey`、`eventBody` (入力の Map)、`hasError`。
  - 成功したら `error` (null) と `replayId` (Long)。失敗したら `error` (`message` と `errorCode` の HashMap)。
- gRPC の失敗の型は、実 Mule の対応表 (`PubSubUtils`) で決める。
  - 説明は "io.grpc.StatusRuntimeException: <CODE>: <説明>" である (実 Mule は CompletionException の文言を出す)。

### subscribe-channel-listener

- push 型の source で、1 本の Subscribe (双方向の gRPC) を開いて読み続ける。
- 流量制御は実 Mule と同じにする。
  - 最初の FetchRequest で `eventBatchSize` 件 (最大 100) を求める。
  - flow を `eventBatchSize` 件処理するごとに、同じ FetchRequest を送り直す。
- イベントは 1 件ずつ順に flow に渡す (実 Mule は並行に流しうる)。
- payload は EventDTO (`eventId`、`replayId` (Long)、`event`) で、attributes は null である。
- `event` は、実 Mule の結果と同じ値を、Avro の値から直接作る (conn/sf_pubsub_avro の `gson`)。
  - 実 Mule は、Avro の GenericRecord を toString で JSON にし、それを Gson で LinkedTreeMap に読み直している。
    mulay は文字列を経由しない。結果は同じで、往復の分だけ速い。
  - 数はすべて Double (2^53 を超える long は丸まる)、record と map は LinkedTreeMap、配列は ArrayList、文字列は String、
    真偽値は Boolean の `^class` を持つ。値の無い項目も null として入る。bytes は latin1 の文字列、fixed は符号付きの数の配列。
  - CDC の ChangeEventHeader の `changedFields` / `diffFields` / `nulledFields` は、bitmap ("0x..") から項目名に展開する (実 Mule の `processBitmap` と同じ)。
- replay:
  - `latest` と `earliest` は、そのまま送る。
  - `custom-replay-id` は、先に replay ID が有効かを確かめる (CUSTOM で 1 件求める Subscribe を開き、INVALID_ARGUMENT なら無効)。
    無効なら source を始めず、その後も試し直さない ("The provided replay id is not valid. ReplayId: .., Channel: .." を 1 回だけログに出す)。
    アプリの他の flow は動く。実 Mule 4.11.3 で記録した (RetryPolicyExhaustedException で source が止まり、アプリは起動する)。
  - `replay-id-from-object-store` は、`osName` の店の `osKey` の値 (Integer、Long、文字列) を読む。無いか無効なら earliest で始める。店に書くのは flow の役目 (実 Mule と同じ)。
- stream が切れたとき (相手が閉じた、または gRPC の失敗) は、0.5 秒待ってから同じ replay の指定で開き直す。
  - 実 Mule も、source の再接続で同じ指定から始め直す (受けた最後の replay ID からは再開しない)。

## 実 Mule と違う点 (docs/compat/deviations.md)

- スキーマと topic の情報をプロセスの中に覚える (上の publish-event)。
- イベントを 1 件ずつ順に流す。
- 接続の検査 (`validate` が最初の Platform Event で GetTopic する) をしない。
- 未対応: proxy、TLS の設定、`inactivityWatchdogSchedulerFrequency`、`unauthorize` (何もしない)、saml-connection。

## 確かめ方

- fixture test/fixtures/apps/salesforce-pubsub (d30 の org。Platform Event MulayPubSub__e と、SyncItem__c (templates/org-sync/sfdx) の CDC。
  sfdx/ の PlatformEventChannelMember で CDC を有効にする)。CDC の作成・更新・削除で、ChangeEventHeader の項目、bitmap を展開した changedFields、
  Date の項目 (epoch ミリ秒の Double。`1.7980704E+12` と書かれる) まで実 Mule と同じ。
- メッセージの符号は test/pubsub (コネクタの jar の生成クラスで作った期待値)。
- Avro は mulay.lib.avro (ADR 087) を使う。
