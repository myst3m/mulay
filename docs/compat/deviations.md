# Mule / DataWeave との既知の違い

実 Mule 4.11.3 (DW 2.11.2) との差のうち、意図したものと未対応のもの。
計測: `tools/dwt-all.sh -e`、`tools/mule-oracle/mule-oracle mulay`。

## 意図した違い

| 項目 | mulay | 実 Mule | 理由 |
|---|---|---|---|
| `java!` 呼び出し、Java のクラス (型の再利用 `import java!..` を含む) | 非対応 | 対応 | JVM を持たない |
| DataWeave の連鎖 (演算子の連なり、`.a`・`[0]`・`()`・`as T` の連鎖) の長さ | 入れ子と合わせて 400 段まで ("nested too deeply") | `+` と `.a` は 400 段を読み 1000 段で StackOverflowError、`application/dw` の入力の `as` は 600 段で StackOverflowError | 名前解決・評価が鎖の長さだけ再帰するので、入れ子と同じ上限に数える。前は数えず、2 万段でプロセスごと落ちた。ADR 017 |
| wasm (Müdrover) の DataWeave の深さの上限 | 1000 ("Stack Overflow. Max stack is 1000") | 3000 | wasm のスタックはブラウザの既定で約 1 MB で、数えた段がおよそ 1500 を超えるとどの書き方でもあふれて trap になった (map や reduce を挟む再帰は 500 段ほど)。ネイティブは 3000 のまま。ADR 017 |
| JAR で動かすときの `${app.home}` | JAR のパスから .jar を外したもの。その下は `http:load-static-resource` だけが JAR の中身から読む (ファイルとしては無い) | 展開したアプリのディレクトリ (ファイルがある) | JAR を展開しない (RTF の読み取り専用のルート FS、メモリ)。ADR 117 |
| `mulay dw test` の出力 | ファイルごとの木 (✓ ✗ ○)、Failures、合計の行 | Maven の plugin のイベントのログ (TestStarted など) | 読みやすさを優先する (ユーザーの判断、2026-11-02、ADR 111) |
| dw::test の TestResult の location | "Unknown location" | テストの名前の文字列の場所 | dw::Runtime location が引数を通した値の場所を持たない (ADR 111、docs/todo.md) |
| `application/java` の値 | DW の値のまま持つ。HTTP 応答では Java の直列化形式で書く | Java のオブジェクト | 同上 (外から見える書式は合わせてある) |
| `Mule::lookup` | 非対応 | 対応 | 評価器から flow を呼ぶ仕組みが未実装 |
| `dw` reader | データのリテラルだけ読む | 式も評価する | reader は評価器より下の層 |
| 文字列の位置 (`sizeOf`、`indexOf`、範囲の添字など) | コードポイント単位 (`"a😀b"[-1 to 0]` は `"b😀a"`) | UTF-16 単位 (サロゲート対が壊れて `"b??a"`) | 絵文字など BMP 外の文字でだけ差が出る |
| head-tail の構築子 `[h ~ t]`、`{k: v ~ t}` | "Head-tail constructors ([head ~ tail]) are not supported yet" で失敗 (パターンの `case [h ~ t]`、`case {k: v ~ t}` は対応) | 配列・オブジェクトを作る | 未対応を黙って別の形に読まず診断で示す (docs/adr/020) |
| 正規表現リテラルの検査 | 使うときに組み立てて検査する (評価しない枝の `/(/` は失敗しない) | パースのときに "Invalid Regex: .." で失敗 | docs/adr/020 |
| `output application/json---` (改行なしの `---`) | 内容の型を `application/json` と読む | "Unknown content type `application/json-`" で失敗 | docs/adr/020 |
| 入れ子の深さ | スクリプトの式は 400 段で "The expression is nested too deeply (the limit is 400 levels)"、JSON の読み込みは 2000 段で "Maximum nesting depth exceeded" | JVM のスタックが尽きると "null" で失敗 (dw-oracle で、括弧の入れ子は 185 段が通り 200 段で失敗、JSON は 2100 段が通り 2500 段で失敗) | C のスタックが溢れるとプロセスごと落ちる (docs/adr/017、033) |
| 正規表現の入れ子の深さ | 括弧と文字クラス `[` の入れ子が合わせて 1000 段を超えると "Pattern is nested too deeply (the limit is 1000 levels) near index .." で失敗 | JVM のスタックが尽きるまで (尽きれば StackOverflowError で失敗) | 外から来た文字列を `as Regex` にするアプリで、C のスタックが溢れるとプロセスごと落ちる。`a|a|..` の長い並びは段にならない (敵対的レビュー、2026-10-25) |
| SQL (SQLite・Derby の pure-Clay エンジン) の入れ子 | 括弧・CASE・関数呼び出しの入れ子が合わせて 250 段を超えると "Recursion limit"。式の木の高さが 1000 を超えると SQLite と同じ "Expression tree is too large (maximum depth 1000)" | SQLite 3.53 の構文解析は構文ごとに上限が違う (括弧 2493 段、関数 831 段、CASE 498 段で "Recursion limit") | 深い入れ子で C のスタックが溢れるとプロセスごと落ちる。要求の処理は小さめのスタックで動くことがある (敵対的レビュー、2026-10-25) |
| ロケール | en-US と CLDR (Java 17 の既定)。日時の名前 (月・曜日・午前午後・紀元・四半期) と週の定義は主な 68 の地域 (`lib/time/locales`)、それ以外は en-US。時間帯の名前 (z) は en-US だけ | `java.locale.providers=COMPAT,CLDR`、すべての地域 | 英語以外のロケールの数値書式、表に無い地域の日時の名前で差が出うる |
| `Double.toString` | Java 19 以降の最短表現 (2^53 以上 2^63 未満の整数だけは Java 17 と同じ。ADR 003) | Java 17 | 三角関数などの結果の最後の桁がまれに違う |
| `Float.toString` (DB の float4 / BINARY_FLOAT) | Java 19 以降の最短表現 | Java 17 (最短でないことがある。例 `1.17549435E-38`) | Double と同じ |
| output の deferred=true で、途中の要素の評価が失敗したとき読む側に届くもの | 失敗した所までのテキスト (`[\n  10,\n  5`) | それか空 (書き手が別のスレッドで、回によって違う) | 決まった結果にする (実 Mule でも起こる方) |
| deferred=true の出力をもう一度読んだときの文言 | `java.io.IOException - Pipe closed\njava.io.IOException: Pipe closed, while reading ..` | Pipe closed の後に PipedInputStream のスタックトレースが続く | JVM のスタックは作れない |
| deferred=true の入力の読み取り | 変換のときに読む (payload の parse の失敗は変換で出る)。本体が `payload map F` で payload が streaming=true の JSON の配列なら、読むときに要素を 1 つずつ読む | 読むときに読む | 入力の値を決めておけば Event を持ち越さずに済む |
| deferred=true の書き出し | 本体が `A map F` で出力が JSON なら 1 要素ずつ。それ以外 (CSV、XML、map でない本体) は最初に読むときに全体を評価して書く (失敗なら空) | 書き手が少しずつ書く | 外から見える違いは失敗したときの出力だけ |
| deferred=true の出力を file:write / sftp:write で書き、途中で評価が失敗したとき | 失敗した所までを書いて成功 | 失敗した所までか空のファイルを書いて成功 (回によって違う) | 上と同じ |
| 指数の大きい数を展開する演算 (加減算、floor / ceil / round、mod、pow、toPlainString) | 1 千万桁を超えるなら "BigInteger would overflow supported range" で失敗 (mod と除算は "Division by zero"。toPlainString は指数表記のまま。小数点の後の 0 が 1 千万桁を超える小さい数の toPlainString も指数表記のまま。指数を使わない書式 (`as String {format: "#,##0.00"}` など) で整数部が 1 千万桁を超えるときも同じ失敗) | BigInteger の範囲 (約 6.5 億桁) まで作る | 確保に失敗するとプロセスごと終わる。実 DW も 1 千万桁の加算は 300 秒で終わらない |
| repeat / leftPad / rightPad の結果の大きさ | 128MB を超えれば "Requested array size exceeds VM limit" で失敗 | Java の配列の上限 (約 2^31 文字) まで作る | 確保に失敗するとプロセスごと終わる |
| 入れ子の multipart | 100 段まで読み、それより深い部分の中身は Binary のまま | 3000 段でも読む | 段ごとに中身を複製するので、深い入れ子でメモリを段数 × 大きさだけ使う |
| multipart のパートが読めないとき | 中身を Binary (元のバイト列) のまま渡し、誤りにしない | 中身に触れた時に読みの誤り (`while reading `x` as Xml` など) で失敗する | DW の組み込み関数は引数の遅延の値を先に読み切る (`rt/whole-args`) ので、読めないパートを誤りにすると `sizeOf(payload.parts)` のような中身に触れない式まで失敗する |
| multipart のパートの Content-Type の追加指定 | `supportDtd`・`externalEntities`・`descriptorUrl` は読む設定にしない (ほかの `maxAttributeSize`・`separator` などは使う) | `supportDtd` は使わない (2026-11-08 に http-multipart で記録)。`externalEntities`・`descriptorUrl` は未確認 | 相手が送るパートの見出しで、外部参照やサーバーのファイルの読み込みを有効にさせない |
| 正規表現の照合の大きさ | 手数は 1 億 + 入力 1 バイトあたり 64 (find-all・split・replace は呼び出し全体で)、後戻りの記録は 100 万件まで。超えれば "regex step limit exceeded .." / "regex backtracking stack limit exceeded .." | 手数の上限は無い (`(a+)+b` は終わらない)。後戻りは再帰で、`(a\|b)*` の 1 万回ほどで StackOverflowError (エラーの文言は "null") | 攻撃者の入力で CPU とメモリを使い切らない |
| JSON Schema の検証 (APIkit の要求の検証) の `pattern`・`patternProperties` | 正規表現の手数は検証 1 回の全体で 1 億 + 照合する文字列 1 バイトあたり 64。超えたら "regex step limit exceeded .." で検証の失敗 (`not` の中でも) | 手数の上限は無い | 前は文字列ごとに 1 億手から数え直し、超えても「合わない」として続けたので、`^(a+)+$` と 1000 個の要素で 12 分かかった |
| 開発者に見せるエラーの表示 (ログの例外の枠、`mulay validate`、`mulay dw`) | Rust 風: `error[型]: 見出し`、`--> ファイル:行:桁`、ソースの行と印、`note:` (element・flow stack・DataWeave の元の文)、直し方の `help:`。ログの枠は `Element DSL` と「(set debug level logging ..)」の行を出さない | `****` の枠 (Message・Element・Element DSL・Error type・FlowStack) と、DW の文言そのまま | 何が・どこで・どう直すかを分かるようにする (ユーザーの決定、ADR 096)。`error.description`・エラーの型・DW の golden は実 Mule のまま。mule-oracle は mulay のログの例外を事実 (メッセージの 1 行目・要素・型・FlowStack) で比べる |
| tls:context の enabledProtocols / enabledCipherSuites | TLSv1.2 と TLSv1.3 だけ (TLSv1、TLSv1.1 は捨てる)。使えるものが残らなければ起動時に "tls:context enabledProtocols: none of '..' is supported .." などで失敗。スイートは clay.tls の 9 つ (ECDHE と AEAD) のうち enabledCipherSuites に書いたもの。それ以外 (CBC、RSA の鍵交換など) は捨てる | JDK と tls-default.conf の許すもの | clay の TLS が持つ範囲。設定の誤りで暗号を弱めたまま動かさない |
| 待たない仕事 (async、batch:job、A2A のストリームとプッシュ通知) が同時に 512 を超えたとき | 超えた分は呼び出し側 (要求のスレッド) で動かす (async は終わるまで次へ進まない) | スケジューラのスレッドの溜まりで待つ | 要求ごとにスレッドを作り続けると、作れなくなったところでプロセスごと落ちる |
| 通常のファイルでないもの (FIFO、/dev/zero などのデバイス、それらへの symlink) の中身 | file:list の要素の payload は空の Binary。file:read は FILE:ACCESS_DENIED "Could not read file '..': it is not a regular file"。readUrl は資源が無いのと同じ | 読むときに開くストリーム (FIFO は書き手を待って止まり、/dev/zero は終わらない) | mulay は中身を先に全部読むので、開くと止まるかメモリを使い切ってプロセスごと落ちる。属性 (regularFile など) は実 Mule と同じ |
| file:rename / sftp:rename の to が `.`、`..`、空 | 消す前に FILE:ILLEGAL_PATH (sftp は SFTP:ILLEGAL_PATH) "'to' parameter of rename operation should not be '.' or '..' but '..' was received" | overwrite="true" なら to の先 (元のディレクトリかその親) を消しにかかり、作業ディレクトリの中身まで消えてから MULE:UNKNOWN (2026-10-25、file 1.5.6 で確かめた) | to をリクエストから取るフローで、外から作業ディレクトリを消せる (fixture file-rename-dots、sftp-rename-dots) |
| コネクタの XSD にあって mulay が読まない属性が XML にあるとき | 起動時に `warning: <file>:<line>: <要素>: attribute .. is not supported and is ignored` を出して続ける (docs/connectors.md) | 何も出さない (属性はコネクタが使う) |
| 運用の端点 `/__/health`、`/__/ready`、`/__/metrics`、RTF の `/mule/healthcheck/applications/<名前>/ready` (`mulay.admin.port`、`mulay.health.app`) | あり (`mulay.admin.port` を指定したときだけ専用のポートで答える。docs/mule-runtime.md §8) | 無い (RTF の Pod では Mule が :7777 で ready を答える) | RTF のランタイムとして載せるため。RTF の ready の応答は Mule エージェントと同じ (起動中の状態は CREATED だけ) |
| OpenTelemetry のメトリクスのフローごとの数 (`received.events`、`dispatched.*`、`execution.errors`、`fatal.errors`) | フローごとの点 (`mule.artifact.id` と `mule.flow.name`) | 4.12.0 と 4.12.2: `mule.artifact.id` だけの点が 1 つで、値はアプリのどれか 1 つのフローの値 (各フローが同じ属性で記録し、1 つだけ残る。otel-metrics では received.events が 0) | 公式ドキュメント (otel-support) は `mule.flow.name` 付きと書く。不具合の値は真似しない |
| OpenTelemetry のメトリクスを送れなかったときの詳しい文言 (接続の失敗など) | clay の文言 (`connect 127.0.0.1:4317: Connection refused`) | OkHttp の文言 (`Failed to connect to /127.0.0.1:4317`) | 送る HTTP のクライアントが違う。前後の文言と段は SDK と同じ |
| OpenTelemetry のメトリクスで送らないもの | OTel の SDK 自身の計測 (`otel.sdk.*`、実 Mule は別の要求で送る)、`jvm.gc.duration`、`jvm.class.*`、`jvm.memory.used_after_last_gc`、Anypoint のメタデータ、`alert-fuseboard`、`telemetry.sdk.version` | 送る | GC もクラスのロードも無い。SDK を持たない。版は cli 層にしか無い |
| OpenTelemetry の JVM のメトリクス (`jvmMetrics.enabled=true`) の値 | mulay のプロセスの値に付け替える: `jvm.cpu.count` (affinity と cgroup の上限)、`jvm.cpu.time`、`jvm.cpu.recent_utilization` (前に送ってからの CPU 時間 / (経過時間 × CPU の数))、`jvm.memory.used` と `committed` (プールは 2 つ: `anonymous` (heap、RssAnon) と `file-backed` (non_heap、RssFile)。committed は used と同じ)、`jvm.memory.limit` (heap だけ、cgroup の memory.max。上限が無ければ出さない)、`jvm.thread.count` (/proc/self/task の状態: R は runnable、他は waiting。main のスレッドだけ daemon=false)。scope の version は書かない。アプリの resource と同じ 1 つの要求で送る | JVM の MXBean の値 (G1 などのプール、Java のスレッドの状態)。scope の version は計装ライブラリの版 (`2.26.1-alpha`)。アプリとは別の要求 | JVM を持たない。ダッシュボードが同じ名前で CPU、メモリ、スレッドを見られるように |
| OpenTelemetry のメトリクスの設定で読まないもの | `meter-exporter.conf` (`configurationFilePath`)、`tls.*Base64`、`tls.strategy`、`backoff.*` (既定の値で試し直す)、`aggregationTemporality` (いつも累積) | 読む (4.12.0 は `aggregationTemporality` を読むが使わない: DELTA_PREFERRED でも累積で送った) | 必要になってから |
| OpenTelemetry のメトリクスの `telemetry.sdk.*` | `name=mulay`、`language=clay` | `opentelemetry`、`java`、SDK の版 | 送り手が違う |
| OpenTelemetry のメトリクスの `type` の大文字小文字 | 区別しない (`http` でもよい) | Java の enum の名前 (`HTTP`、`GRPC`) | 書き間違いで黙って送らないより親切 |
| OpenTelemetry のトレースのレベル DEBUG | MONITORING と同じスパン | Java SDK の内部の段 (`mule:parameters-resolution`、引数ごとの `mule:value-resolution`、`mule:get-connection`、`mule:operation-execution`) を足す | 実 Mule の実装の内側の段で、mulay に当たるものが無い |
| OpenTelemetry のトレースの `thread.start.name` / `thread.end.name` / `thread.start.id` の値 | `[<アプリ>].<フロー>` (ログの場所と同じ) と OS のスレッド (pthread_self) | Mule のスレッドの名前 (`[MuleRuntime].uber.07: [app].flow.CPU_LITE @..`) と Java のスレッドの ID | スレッドの作りが違う。属性の有無は同じ |
| OpenTelemetry のトレースで route のスパンを出すもの | choice、foreach、scatter-gather、until-successful (実 Mule で記録した名前) | parallel-foreach、first-successful、round-robin、batch にもあるはず | 名前を記録していない。記録してから足す (docs/todo.md) |
| OpenTelemetry のトレースの送る列があふれたとき | 黙って捨てる (数は数える) | WARN `Export queue overflow: ..` と OTEL_EXPORT_QUEUE_FULL の警報 | 文言を記録していない |
| OpenTelemetry のトレースの設定で読まないもの | `tracer-exporter.conf`、`levelOverrides`、`tls.*Base64`、`backoff.*` (既定の値で試し直す)、`batch.backPressure.strategy` (いつも DROP)、`includeAnypointMetadata` | 読む | 必要になってから |
| OpenTelemetry のトレースの `telemetry.sdk.*` | `name=mulay`、`language=clay` | `opentelemetry`、`java`、SDK の版 | 送り手が違う |
| Anypoint Monitoring の `_metric.log` (`mulay.am.metricFile`) で書くもの | `app_inbound_metric` だけ | `system_metric` (JVM)、`app_stats`、`_metering_metric.log`、`_v2_metric.log` なども書く | Insights の要求数と応答時間に要るのはこれだけ。JVM の値は mulay に当たらない |
| `app_inbound_metric` の `commons.cluster_id` | 書かない | RTF の id | Pod の環境変数に無い。無くても Anypoint は受け付ける (2026-10-14 に max-core で確かめた) |
| `app_inbound_metric` で数えない要求 | a2a・MCP・OAuth の口 | (それらのコネクタのソースは HTTP リスナーではない) | 汎用の HTTP リスナーの経路だけで数える |
| `app_inbound_metric` の `endpoint` の RAML による正規化、`anypoint.platform.config.analytics.agent.preserved_endpoint_tokens` | しない (区切りの規則だけ) | APIkit のアプリでは RAML の形に合わせる。指定した語は X にしない | 必要になってから |
| `app_inbound_metric` の `time` | 時計の分の境目で区切った窓の始まり | エージェントの起動からの 60 秒ごとに区切り、その時の分 (要求の 1 分後の値になることがある) | 窓が時計に揃う方が読みやすい |
| 止めるときの最後のメトリクスの送信 | 1 回だけ試す | SDK の試し直しに従う | 受け口が無いと止めるのが数秒遅れる |
| JAR から起動したときのアプリの資源の大きさ | 展開した合計が 1 GB を超えると読み込みの diag (1 エントリは 256 MB まで) | ディスクに展開するので上限なし | 起動のときに資源をメモリに展開するため (ADR 048、056) |
| MySQL の生成したキーの数 | affected rows が 1,000,000 を超えるかキーが 64 ビットを超えると SQLException (HY000) | Connector/J はサーバーの返す数だけキーを作る | 嘘の数を返すサーバーや中間者がメモリを使い切らせないため (ADR 068) |
| MySQL のサーバーから読むパケットの大きさ | 継いだ大きさが maxAllowedPacket (無ければ 64 MiB) を超えると PacketTooBigException (S1000) | 物理パケット (16 MiB まで) 1 つずつを maxAllowedPacket かサーバーの max_allowed_packet と比べる。継いだ大きさには上限が無い | 偽のサーバーや中間者がメモリを使い切らせないため。サーバーの max_allowed_packet を 64 MiB より大きくして大きな行を読むアプリは maxAllowedPacket を URL に書く (ADR 068) |
| ProtoBuf の記述子で、value か key の無い map の項目、`fields` の無い `google.protobuf.Struct`、`values` の無い `google.protobuf.ListValue` (protoc では作れない) | 読み書きで "Message t.A.MEntry has no field `value`." などで失敗 | 読むと NullPointerException。書くと Map は NullPointerException、Struct と ListValue は記述子を見ずに標準の形 (fields は 1 番) で書く | 前は添字 -1 で `nth` してプロセスごと落ちた。型の参照が解けない記述子は実 DW と同じく読み込みで `Descriptors$DescriptorValidationException - t.A.b: ".t.B" is not defined.` で失敗する |

## 未対応 (v1 の範囲外)

- コネクタ: FTP、JMS、email、sockets、websockets、java モジュール。扱うコネクタの未対応は docs/connectors.md の「できないこと」。
- secure-properties: AES 以外のアルゴリズム (Blowfish、DES など。OpenSSL 3 の legacy 暗号)、RSA、値の中の `${secure::..}` の入れ子
  (docs/connectors.md の secure-properties)。
- cron の `L` `W` `#`。
- XML SDK のモジュール (mule-plugin の `<module>`)。古い仕組みなので扱わない (ユーザーの判断、2026-11-02)。
  一度入れたものは 9922f0b9 で外した (元は 6d712825・bb83ae87、ADR 114)。

## コネクタの違い

| 項目 | mulay | 実 Mule |
|---|---|---|
| Salesforce の config-with-oauth-connection の PKCE | プロパティ `mulay.salesforce.pkce=true` で code_challenge (S256) と code_verifier を送る (既定は送らない) | 送らない (コネクタ 12.0.4 まで)。PKCE を求める組織では認可が 400 で断られる |
| Salesforce の config-with-oauth-connection のトークン | プロセスのメモリに持つ (再起動したら認可し直す) | Object Store に持つ |
| Salesforce の認可の口の resourceOwnerId (`/authorize?resourceOwnerId=x`) | state に入れて運び、コールバックで受けた state の持ち主のトークンにする (実 Mule の state の書き方とは照合していない) | 実コネクタの書き方 |
| gRPC のクライアントが枠の壊れた本文を受けたとき | `GRPC:INTERNAL` "Received a truncated gRPC message" (ADR 077) | 応答を返さずに止まる |
| gRPC のクライアントがメッセージ無しの成功を受けたとき | `GRPC:INTERNAL` "No value received for unary call" | 応答を返さずに止まる |
| gRPC のクライアントが grpc-status の無い 200 以外の HTTP 応答を受けたとき | gRPC の HTTP の状態コードの対応表のエラー (503 は `GRPC:UNAVAILABLE` "HTTP status code 503") | 応答を返さずに止まる |
| gRPC のクライアントのストリーミング (ユーザーの判断) | client-streaming と双方向は送るたびに相手に送り、応答はメッセージが届くたびに渡す (listener もすぐ)。Iterable は間が空いても待ち、失敗は GRPC:<CODE>。双方向の attributes の requestId は requestId、messageSent は本当に送れたか。Deadline は grpc-timeout ヘッダと DEADLINE_EXCEEDED (ADR 080) | endClientStreaming まで溜めて 1 回で送り、応答も全部届いてから渡す。listener は 500 ms に 1 フレーム。Iterable は pollTimeout の 2 回分で NoSuchElementException の 500、失敗は MULE:UNKNOWN。requestId の欄に routingId、messageSent はいつも true |
| file:list の要素の payload | 読み込み時に全ファイルを読み、mime で parse する (parse できなければ Binary) | 触ったときに読む |
| file:listener | 1 件ずつ順に流す | 並行に流しうる |
| APIkit の apikit:console の画面 (`/console/`、`index.html`) | 自前の小さな HTML (title は同じ「APIkit Console」、`api/` の仕様をそのまま見せる)。状態コード・content-type・`expires: -1` は同じ | API Console (MuleSoft の JS の資源 `package/build/*.js` と AMF のモデル `?amf`) の画面 |
| apikit:console の `?amf` と `package/build/*` | APIKIT:NOT_FOUND | AMF のモデル (gzip の JSON-LD) と API Console の資源を返す |
| apikit:console の `/api/` (`?raml` 付きも) | 根の仕様のファイルをそのまま返す (content-type は同じ application/raml+yaml) | AMF が解決して書き直した仕様 (OAS は JSON、RAML は include を展開した物) |
| apikit:console が返すファイル (`/api/<ファイル>`) | 根の仕様と、RAML の include・uses で読むファイル。OAS の外部の `$ref` 先は返さない (mulay の OAS は外部の $ref を読まないため) | 根と参照先のファイル |
| http:polling-source と db:listener の watermark | プロセスの中だけに持つ (再起動すると最初から読む) | ObjectStore に永続し、再起動しても残る |
| http:polling-source と db:listener の流し方 | 1 件ずつ順に流す。同じ id の項目を並行に流さない検査 (ALREADY_IN_PROCESS) は要らない | 並行に流しうる |
| http:polling-source の式の誤り | ポーリングのたびに失敗としてログに出る (ADR 084) | source の開始の時点で失敗する |
| file:read の lock="true" | 何もしない (中身はすぐ読む) | 中身 (ストリーム) を読み切るまでファイルを lock する。読み切る前に同じファイルをもう一度 lock して読むと MULE:UNKNOWN "Unexpected error reading file '..': Could not lock file '..' because it's already owned by another process" |
| attributes.creationTime (File) | 更新時刻 | Java 17 の Linux と同じく更新時刻 |
| SQLite (`jdbc:sqlite:`) の実装 | 純 Clay の SQLite (lib/sqlparse・sqlexec・sqlbtree、db/sqlite)。SQL の範囲は docs/sqlite.md。範囲外の文 (RIGHT・FULL JOIN、upsert、RETURNING、VIEW、TRIGGER、ウィンドウ関数、ALTER TABLE など) は "unsupported: .." の SQLITE_ERROR | sqlite-jdbc に同梱の SQLite 3.50.3 |
| SQLite のファイルの DB | 開くときに全部読み、変えた文の後 (bulk は全部の組の後) に全部書く。rollback journal とファイルのロックは無い (他のプロセスと同じファイルを使わない) | rollback journal とロック |
| SQLite の ORDER BY の無い問い合わせ、集約の後の ORDER BY で値が同じ行の順 | rowid の順か、「列 = 値」で使った索引の順。同じ値の行は入れた順 | SQLite のプランナが選んだ索引 (covering index) の順や、sorter の都合の順 (SQL では決まっていない) |
| Salesforce の失敗した項目の exception | message だけ (stackTrace は空の Array) | Java の例外 (スタックトレース付き) |
| Salesforce の結果の POJO (describe、get-user-info、Bulk のジョブ情報) のキーの並び | 固定 | 実行ごとに変わる (Java のリフレクションの順) |
| Salesforce の操作の headers (SOAP ヘッダ) の持ち越し | 操作ごとに作る (headers の無い呼び出しには付けない) | プールした接続に残り、headers を渡さない内部の呼び出し (describe など) にも前の操作のヘッダが付く (ADR 089) |
| Salesforce の Bulk v1 の操作の headers の持ち越し | 操作ごとに送り、後の操作には付けない。POST でも 1 度だけ送る | BulkConnection の中の Map に残り、使い回す接続での後の POST (create-job、close-job、abort-job、create-batch など) にも付く。POST では同じヘッダを 2 度送る (ADR 090。chunkSize の大きすぎる PK chunking の後、ヘッダの無い create-job が ClientInputError で断られるのを実 Mule で確かめた) |
| Salesforce のメタデータ API の操作の headers のログ | 1 回の操作で 1 度出す | SOAP の呼び出しのたびに出す (deploy・retrieve は状態を見に行く回数だけ繰り返す) (ADR 090) |
| Salesforce の search の searchRecords の要素 | レコードの Map | 未確認 (実 Mule の記録に一致する結果が無い) |
| DB の select の結果を一部だけ読む | DW で読むと全部読んで接続を返す | 読んだところまで (payload[0] だけなら要求の終わりまで接続を持つ) |
| foreach / batch:job で読んだ select の結果を後で読み直す | 失敗する (読んだ行は持たない) | 読み直せる (repeatable なストリーム) |
| 行のストリーム (select、streaming=true の JSON 配列) を入力にした batch:job の BatchJobInstance.recordCount | 0 (ブロックごとに取り出して流すので、始めた時点では数えない) | 先に全部をキューに読み込んで数えた数 |
| データ形式 (JSON など) の payload を foreach / batch で分けた要素のうち、文字列とバイト列の要素の ^mimeType | Java の値 (application/java、batch の記録は */*) | 元の形式の mime (値は parse 済み) |
| Anypoint MQ の subscriber がフローに流す並び | 1 件ずつ順に (フローの maxConcurrency が 1 のときと同じ) | フローの maxConcurrency まで並行に流す |
| Anypoint MQ の subscriber (prefetch) の手元の message のロック | 流す直前に、取ってから lockTtl の 8 割が過ぎていれば延ばす | 0.5 秒ごとに、8 割が過ぎたものを延ばす |
| Anypoint MQ の接続の用意 | 起動のときに裏で接続 (サービスレジストリとトークン。トークンは 1 回だけ試す)。操作はそれが終わるまで待つ | デプロイのときに接続を確かめる (照合していない) |
| Anypoint MQ の送り直しの設定 (`max.retries.failure.operation`、`object.store.client.back.off.*`) | アプリのプロパティ (`mulay run <app> k=v`、`%%% jvm -Dk=v`) | JVM のシステムプロパティ |
| Anypoint MQ のサービスレジストリが答えないとき | CONNECTIVITY で失敗 | 予備のリージョンのサービスレジストリを試す |
| pooling-profile の無い DB の設定 | 接続の数に上限なし | maxPoolSize 5、無期限に待つ (上限と読み切らない select が重なると止まる) |
| 未対応のソース | 起動を止める | (コネクタがあれば動く) |
| http:request (streamResponse="true") の responseTimeout | 応答の頭が届くまでの時間だけ数える。本文は届く限り待つ | 要求の全体 (本文を読み切るまで) に掛かる (未確認) |
| http:request の proxy (http の宛先) | proxy へは絶対 URI の要求行 (`GET http://host:port/path`) で送る (標準の HTTP proxy の作法) | 実 Mule は proxy へ相対の要求行 (`GET /path`) に Host: 宛先 を付けて送る (test/fixtures/apps/http-proxy で確認) | 実 Mule の送り方は、絶対 URI を求める一般の proxy では宛先が分からない。mulay は標準に従う。proxy 側が受けた要求の見え方だけが違う |
| SFTP (SSH) の方式 | 鍵交換は curve25519-sha256 と diffie-hellman-group14-sha256 / group16-sha512、ホスト鍵は ssh-ed25519・ecdsa-sha2-nistp256・rsa-sha2-256/512 (RSA は 1024 ビット以上)、暗号は chacha20-poly1305・AES-GCM・AES-CTR と HMAC-SHA2。これだけを出すサーバー (ecdh-sha2-nistp*、group-exchange や SHA-1 の DH、ecdsa の nistp384/521、ssh-rsa (SHA-1) の署名だけの古いサーバー、CBC や hmac-sha1 だけのもの) とはつながらない (CONNECTIVITY) | Apache MINA sshd の方式 (上のものを含む) | 純 Clay の SSH (lib/ssh)。ECDH の P-256 と SHA-1 の RSA の検証は clay に無い |
| SFTP の接続の失敗の文言 (CONNECTIVITY) | lib/ssh の理由 (例 "no common key exchange algorithm") | MINA sshd の例外の文言 |
| PostgreSQL の確かめるモードで sslrootcert が無いとき | OS の CA で確かめる | ~/.postgresql/root.crt (無ければ失敗) |
| PostgreSQL の sslcert / sslkey (利用者の証明書)、NonValidatingFactory 以外の sslfactory | 接続の失敗 | 使う |
| PostgreSQL の sslmode=allow | prefer と同じ (TLS を先に試す) | 平文を先に試す |
| MySQL の sslMode=VERIFY_IDENTITY の名前の照合 | subjectAltName (DNS 名と IP) だけと比べる。SAN の無い証明書は CN が名前でも失敗 | SAN が無ければ CN と比べる | clay.tls (pkix) の照合は RFC 6125 に従い CN を見ない |
| MySQL の確かめるモードで trustCertificateKeyStoreUrl が無いとき | OS の CA (clay.tls の既定、SSL_CERT_FILE) で確かめる | JVM の信頼する証明書 (javax.net.ssl.trustStore か cacerts) |
| MySQL の trustCertificateKeyStoreUrl | file: の URL だけ (ほかは "Cannot open .. [mulay reads trustCertificateKeyStoreUrl only from file: URLs]") | Java の URL で読めるもの (http: など) |
| http:listener-connection の host | IPv4 の数字、0.0.0.0、localhost (127.0.0.1) だけ。ほかの名前は起動の失敗。同じポートで host の違う listener-config も起動の失敗 (ポートごとに 1 回しか待たない) | 名前を引いて bind する。同じポートでも host が違えば別に待てる |
| http:listener が受けた壊れた要求: Host の無い HTTP/1.1、Host が 2 つ、Transfer-Encoding の付いた HTTP/1.0、chunk の大きさの後ろの空白 (`3 `)、行を LF だけで終える頭やチャンクの行 | 400 (本文なし) | 受けて流す (200) | clay.http のサーバが RFC 9112 §3.2・§6.1・§7.1 に従って断る (clay 0.79.0、LF だけの行は 0.79.1。ADR 091)。request smuggling の穴をふさぐため |
| http:listener が HTTP/1.0 の要求に返す状態行 | `HTTP/1.1 200` (本文は chunked にせず close で区切り、`Connection: keep-alive` が無ければ閉じる) | `HTTP/1.0 200` (要求の版をそのまま返す) | clay.http のサーバが RFC 9110 §6.2 (自分が従う最も高い版で答える) に従う。clay に確かめた (2026-10-17) |
| http:listener の応答の Date ヘッダー | いつも付ける (フローが Date を決めればそれを使う) | 付けない | clay.http のサーバが RFC 9110 §6.6.1 に従って全部の応答に付ける (clay 0.87.0)。外す設定は作らないと決まった (2026-10-16)。シナリオは受けたヘッダーを書き出すところで `date` を落として比べる |
| http:listener が受けた、パスでない対象 (`GET a/7`) | 400 | 404 "No listener for endpoint: /7" | 同上 |
| http:listener が `java.net.URI` として読めない対象を断る 400 | Content-Length を付ける。absolute-form の authority に IPv6 の角括弧があれば調べない | Content-Length を付けずに接続を閉じて区切る。IPv6 の形も調べる | 前者は clay.http のサーバが付ける。後者は mulay の listener が IPv4 だけを待つので省いた (ADR 074) |
| http:listener が受けた absolute-form の要求 (`GET http://h/p`) の Host ヘッダー | 対象の authority (`h`) | 送られた Host のまま | clay.http のサーバが RFC 9112 §3.2.2 に従って置き換える (clay 0.79.0、ADR 091)。requestUri などは実 Mule と同じく scheme と authority を外した形 |
| http:listener が受けた absolute-form でパスの無い要求 (`GET http://h`、`GET http://h?x=1`) | `/` (`/?x=1`) として扱う | 応答せずに接続を閉じる | |
| http:listener が受けた absolute-form で userinfo の付いた要求 (`GET http://u@h/p`) | 400 | userinfo ごと外して扱う | clay.http のサーバが authority を host の文字に限る (ADR 091) |
| http:request が受けた、Transfer-Encoding と Content-Length が両方ある応答、Transfer-Encoding が `chunked` 単独でない応答 (`identity`、`gzip, chunked`) | HTTP:CONNECTIVITY "..failed: the response has both Transfer-Encoding and Content-Length." など (clay の文言) | 読む (Transfer-Encoding を優先する。`gzip, chunked` は本文が壊れる) | clay.http のクライアントが RFC 9112 §6.3 に従いエラーにする (clay 0.79.0、ADR 091)。接続を使い回すので、枠のずれが次の要求の応答に混ざるのを防ぐ |
| http:request が受けた、行を LF だけで終える応答の頭 | HTTP:CONNECTIVITY "..failed: a line of the response head ends with LF alone." (一部の行だけなら "..: a field line of the response has a control byte in it.") | 読む | clay.http のクライアントが CR のない LF を枠の誤りとして断る (clay 0.79.1、ADR 091) |
| http:request が受けた 1xx (100 Continue、103 Early Hints) の応答 | 読み飛ばして、その後の最終の応答を返す | 103 を最終の応答として返す。100 の後の応答は NullPointerException の文言の HTTP:CONNECTIVITY | clay.http が RFC 9110 §15.2 に従って読み飛ばす (ADR 091) |
| http:request の digest-authentication で、401 の挑戦に qop が無いとき (RFC 2069 の形) | response = MD5(HA1:nonce:HA2) | 別の値 (算出の仕方を再現できなかった。qop があるときは一致する) |
| Salesforce の sObject のフィールド名が XML の名前でないとき (データから来た "Name>x</urn1:Name>.." など) | 送らずに SALESFORCE:INVALID_INPUT "Invalid field name: '..'" | 未確認 (SOAP の本文にそのまま書くはず) |
| A2A の task-listener の attributes のキーの並び | 固定 (実 Mule の記録の 1 つ) | 実行ごとに変わる |
| http:listener が流して受ける大きな本文 (512 KB を超えるか長さの無いもの) の要求で、経路が無いか method が合わないとき | 本文を読まずに 404 / 405 (文言は同じ)。HTTP/1.1 は答えた後で接続を閉じる (HTTP/2 はその流れだけ) | 本文を受けてから答える (と思われる。接続は続く) | 経路の無い口に送られた大きな本文をディスクに溜めない (ADR 118) |
| http:listener が大きな本文をディスクに溜める間に、ディスクの空きが少なくなったとき | 空きが mulay.http.spoolMinFree (既定はファイルシステムの 10% と 1 GiB の小さいほう) を下回れば 503 で閉じ、溜めた分を消す | ディスクが尽きるまで書く | だれでも大きな本文を並行に送ってディスクを埋め、他の書き込み (Object Store、ログ) まで止められないように (ADR 118) |
| MCP サーバーが受けた、Origin ヘッダーのある要求 | Origin のホストが loopback でなく mulay.mcp.allowedOrigins にも無ければ 403 (JSON-RPC の -32600 "Origin not allowed: ..") | Origin を見ずに答える (SSE の応答には Access-Control-Allow-Origin: * も付ける) | MCP の仕様 (2025-06-18 の Transports) はサーバーに Origin の検証を求める。手元の MCP サーバーを、ブラウザで開いた悪いページが DNS rebinding で呼べないように。Access-Control-Allow-Origin: * は実 Mule と同じく残す (通った Origin にしか届かない) (ADR 118) |
| MCP サーバーのセッションの期限 (streamable-http) | sessionIdleTimeout (既定 5 分) より長く要求が無ければ消す (その後は 404 "Session not found")。全部で 10000 を超えたら最も長く使われていないものから消す (旧式の SSE のつながっているものは除く) | 消さない (sessionIdleTimeout 2 秒で 10 分待っても続く。sessionsObjectStore が無ければ数の上限も無い) | 認証の無い initialize のたびにセッションが増え、メモリを使い切らないように。期限は設定の文書 ("Timeout for idle sessions") のとおり (ADR 118) |
| A2A のプッシュ通知の送り先 | 名前を引いた結果に内側のアドレス (loopback、リンクローカル、プライベート、0.0.0.0、::、マルチキャスト) があれば送らない (WARN)。調べたアドレスにつなぐ。リダイレクトは追わない。`mulay.a2a.allowPrivatePushUrls=true` で内側にも送る | どこにでも送る | 認証の無い message/send や tasks/pushNotificationConfig/set で、だれでも送り先を決められる。サーバーの内側 (クラウドのメタデータ 169.254.169.254、手元の管理の口) に、サーバーの名で POST させない (SSRF) (ADR 118) |
| A2A のタスクの記録 | プロセスのメモリ (再起動で消える。最後の書き換えから 1 日で消え、10000 タスクを超えると終わったものの古い順に、足りなければ終わっていないものも消す) | Object Store (persistent、1 日で消える。数の上限は無い) | 認証の無い message/send でタスクが増え続け、メモリを使い切らないように (ADR 118) |
| A2A の tasks/cancel (Message しか返していないタスク、記録なしのサーバー) | 500 INTERNAL_ERROR / 404 task not found! | 答えない (要求が時間切れになる) |
| A2A のプッシュ通知の付いた message/send で応答の ID が合わないとき | 失敗の答えを通知の URL に送る | 何も送らない |
| Batch の記録の並行 | maxConcurrency が 2 以上か、入力が行のストリーム (select、streaming=true の JSON 配列) なら、ブロックを maxConcurrency 本 (1 以下なら 1 本) のスレッドで並行に流す。それ以外 (maxConcurrency を書かないか 1) は 1 件ずつ順に流す。schedulingStrategy は見ない | ブロックを並行に流す |
| BatchStepResult の exceptionSummary | 常に空 | Java の例外の種類ごとの数 |
| Batch の失敗した記録のログ | 既定のエラーハンドラの形 (DefaultExceptionListener) | batch モジュールの形 |
| stored-procedure の引数の種類のキャッシュ (db:config ごと、SQL の文面で 50 件) が一杯のとき | 新しい文面は覚えない | caffeine が使われ方の頻度で入れ替える |
| Validation の is-email / Validation::isEmail の国際化ドメイン (`a@例え.jp`) | IDN.toASCII の nameprep を簡略にする (小文字にし、見えない文字を除き、ASCII でない空白と制御文字を拒む。NFKC の正規化、未割り当ての文字と双方向文字の検査はしない) | java.net.IDN (nameprep の全体) |
| Validation の is-number の FLOAT の値 | double のまま持つ (float32 に丸めない) | Float。下限・上限の比べ方と文言の数が、float32 に丸まる桁でだけ違いうる |
| Validation の is-number の数の記号 | CLDR の表に COMPAT の違いのうち NaN (U+FFFD) と fr の桁区切り (U+00A0) だけを重ねる | `java.locale.providers=COMPAT` の記号 (ほかの地域の違いは未確認) |
| Validation の IP の一覧 (is-allowed-ip / is-not-denied-ip) のホスト名の項目 | 引かない (当たらない) | InetAddress.getByName で DNS を引く |
| Validation の IP の一覧の不正な項目 (`a/`、`1.2.3.4/x`、`/40` など) | 当たらない | 実モジュールの不具合で MissingFormatArgumentException などになる (未確認) |
| Vectors の transform-chunk-text の文の切り分け | 規則で近似する (. ! ? の後が空白で次が大文字・数字・括弧・引用符、直前が略語や 1 文字の頭文字でなければ文の終わり。lib/textsplit) | OpenNLP の学習済みモデル (opennlp-en-ud-ewt-sentence)。"3 p.m. on" や "Jan. 5." のような所で切り方が違いうる |
| Vectors の transform-chunk-text の文字の数え方 | 文字単位 (String.length と同じく UTF-16 で数えるが、最後の文字の単位の分け方は code point) | UTF-16 の単位 (絵文字が半分に分かれうる) |
| Vectors の store-remove に ids と condition を両方書く | 受け付けて ids で消す | ビルドで断る ("the following parameters cannot be set at the same time: [condition, ids]") |
| WSC の SOAP 1.2 の要求の Content-Type の折り返し | 折り返しの改行 (CRLF) を空白 2 つにして 1 行で送る | jakarta.mail が `; \r\n\t` で折り返した値を送る (受け手の Mule の listener は改行を空白 2 つにして見せる) | clay.http はヘッダーの値に改行を許さない |
| WSC の結果の body が XML の文書でない (Body の子要素が 2 つ以上) | DW で触ると Binary として見える (`#[payload.body]` でそのまま返すのは同じ) | 触ると "Illegal to have multiple roots .. while reading `body` as Xml" で失敗 | Java の中の TypedValue を読まずに持つ仕組みが無いので、先に読む (file:list と同じ) |
| Salesforce Composite の post-query / post-query-all | 操作のときに nextRecordsUrl のページを全部読む (失敗は操作のエラー) | 結果を読むときにページを取りに行く (失敗はそのときに出る) | ページの取得を後回しにする仕組み (遅延の iterable) を持たない |
| Salesforce Composite の client-credentials のトークン | 最初の操作のときに取る | アプリの起動のときに取る (OAuth の dancer の start) | Salesforce コネクタと同じ取り方を使う |
| Salesforce Pub/Sub の topic とスキーマ | GetTopic と GetSchema の結果をプロセスの中に覚える (ADR 088) | publish のたびに問い合わせる | publish ごとに 2 往復を省く。スキーマを変えたら再起動が要る |
| Salesforce Pub/Sub の subscribe-channel-listener | 届いたイベントを 1 件ずつ順に flow に渡す | 並行に流しうる | 同期の順序を保つ |
| Salesforce Pub/Sub の接続の検査 | しない | 接続のときに最初の Platform Event で GetTopic を呼ぶ | 失敗は最初の操作や購読のときに出る |
| Validation の Validation:: の関数 | アプリが Validation モジュールを持たなくても使える (mulay dw でも) | モジュールを依存に持つアプリだけ |
| DataWeave の利用者のモジュール (`import f from my::mod`) に構文エラーやコンパイルエラー (初期化の前の参照 `var now = now()` など) があるとき | アプリの読み込みで失敗する。文言は構文エラーなら `Module my::mod: <モジュールのエラー>`、それ以外はモジュールの抜粋と位置 (`my::mod (line: 3, column: 13)`) を付けた最初のエラー | 配備は成功し、その式を評価したときに MULE:EXPRESSION (`Script '..' has errors: <モジュールのエラー> at 2 : 14`。コンパイルエラーなら続けて `Unable to resolve reference of: <import した名前>`) | mulay はスクリプトを読み込み時に全部コンパイルする。誤りは早く知らせる |

## 既知の差 (直す予定)

- on-error の type のコネクタの名前空間の無い種類 (`HTTP:NOPE` など) を、実 Mule は `Could not find error` で拒むが、mulay は通す (コネクタのエラーの種類の表が無いため。ADR 100)。

- **DataWeave の初期化の前の変数を読むクロージャと遅延評価 (2026-10-12)**: 実 DW は do の var と fun、最上位の var を
  宣言の順に初期化し、まだ値の無い変数を読むと外側の同じ名前に進み、無ければ "There is no variable named 'b'" で失敗する。
  mulay は同じフレームの中で書いた順に決まる参照 (前の var の初期化の中、その中の match の case・オブジェクト・do) を
  解決のときに同じ規則で決め (resolve.clay の lookup-ref)、最上位の var は実行時に調べる。違いが残るのは:
  - クロージャ (ラムダ、値として使う do の fun) は作ったときに外の変数の値を写す。実 DW は呼んだときに読む。
    `do { var f = () -> b var b = 1 --- f() }` は実 DW で 1、mulay で null。`do { fun g() = b var a = g() var b = 1 --- a }` と
    `do { var f = () -> b var a = f() var b = 1 --- a }` は実 DW で "There is no variable named 'b'"、mulay で null。
  - 実 DW は map などに渡した関数と update の case を、値を読むときに評価する。`do { var a = [1] map (x) -> b var b = 1 --- a }`
    は実 DW で [1]、mulay で [null]。`{a: 1} update { case .a -> b }` の後ろの var b も同じ (update の case から後ろの fun を
    呼ぶのは実 DW と同じく動く)。

- **小数の末尾の 0**: 実 DW は小数のリテラルや入力の数 (1.50、1.0) の scale を値に残し、表示 (出力、as String) で削る。
  mulay は読むときに削る。違いが出るのは負の scale の数との乗算だけ (`1e30 * 1.50` は実 DW で 1.50E+30、mulay で 1.5E+30)。

- **DataWeave のコンパイル時の型エラー**: 実 DW は型を推論して、合わない引数を実行前に `Expecting Type: .. but got: ..` や
  `Unable to call: ..` で拒む。mulay は形から分かる範囲だけを推論して同じく拒む (resolve.clay の「静的な型」):
  - リテラル、if の和、default、do の var、最上位の var、最上位と do の中の fun の戻り値 (引数は Any として本体から)、
    配列の添字と範囲、組み込み関数の戻り値 (カタログのシグネチャから生成)、`case x matches` の束縛 (実 DW と同じく
    `Array<Array<String>>`)。組み込み関数の各引数の型の成分が、どのオーバーロードにも当てはまらなければ拒む。
  - and / or / not の被演算子、前置の呼び出しの関数型の引数 (ラムダの引数の数、関数でないリテラル)。
  - 組み込み関数の引数の数 (カタログのオーバーロードの数の幅のどれにも入らなければ、宣言の順で最初のオーバーロードを
    出して拒む。引数の型は推論した範囲で出す)。
  - オブジェクトのリテラルの形 (`{| a: 1 |}`、`{|a: 1, b: 2|}`)。キーが式・条件付き・属性付きなら `Object`。
  - それ以外は Any として扱い、実 DW より厳しくはならない。型の注釈、ジェネリクス (`fun g<T>(x: T): T`)、
    利用者の関数の引数の型の検査、オブジェクトの形の型 (`{| a: 1 |}` の表示を除く) は推論しないので、実 DW が拒む
    スクリプトを動かしてしまうことがある。日付のリテラルとラムダは、オブジェクトの値の型として `Any` と出す (実 DW は `Date`、`(x) -> ?`)。
- **値のソースの位置**: 実 DW の値は作られた場所 (リテラルの位置、入力の名前) を持ち、writer の失敗
  (`Cannot coerce Object to String` の抜粋と `Trace:`、text/plain の `Reason: .. while writing TextPlain at ..`)、
  Java への変換の失敗の抜粋、`locationString(x)`、`location(f)` に使う。mulay の値は位置を持たない。
  - `location(x)` / `locationString(x)` は、resolve が引数の式から値を作った式を形でたどる (var・do の var の
    初期化、fun の本体、リテラルの中のキーと添字、組み込み関数は .dwl の native)。関数の引数のように実行時に
    決まる値はたどれず、実 DW と違って "Unknown location" になる。
  - writer と Java への変換の失敗 (`Cannot coerce Object to String`、`Unable to convert `Array` to ..`) は、失敗の
    文言の型の最初の値を出力の値から探し、その経路を本体のリテラル (キー、添字、if の枝、do の本体) でたどって
    抜粋と Trace を付ける。関数の結果や入力から作った値はたどれず、位置の部分が無い。text/plain の writer の
    `while writing TextPlain at ..` は、本体が入力をたどるだけのとき入力の名前 (Mule の変数は変数名) を入れる。
  - 入力の読み取りの失敗は、最初の使用が組み込み関数の呼び出しの引数ならその位置の Trace を付ける (実 Mule は
    使うときに読む)。
- **props() の Java 固有のキー**: mulay は JVM ではないので、props() は OS と利用者の由来のキー (file.*、line.separator、
  path.separator、java.io.tmpdir、os.*、user.*) だけを持つ。値の出どころは Java と同じ (os.version は uname、
  user.home / user.name は passwd、java.io.tmpdir は TMPDIR を見ずに /tmp)。キーの順は Java の Properties の
  反復順 (JVM の全プロパティで決まる) を再現しない。
- **利用者の DW モジュール** (`import ... from mymod::Utils`、Mule アプリの資源の mymod/Utils.dwl、
  dw::Runtime::run / eval の fs の "/Utils.dwl"): var と fun は修飾名で本体と同じプログラムに入れる。モジュールの
  型 (type) は修飾せずに登録するので、本体や別のモジュールの同じ名前の型とぶつかる。import の失敗の位置は宣言全体
  (実 DW はモジュールの名前だけ)。
- **関数の呼び出しの型の失敗の文言**: `You called the function '++' with these arguments:` の後、実 DW は引数の値
  (`String ("X")`) と `But it expects one of these combinations:` の一覧を出し、演算子なら演算子の位置だけを指す。
  mulay は引数の型だけで、位置は式全体 (golden は 1 行目で比べる。core-modules の /alias)。
- **try の失敗の stack**: 実 DW と同じく名前付きの関数の枠 (末尾呼び出しを含む) と、native の組み込み関数の
  枠 (`fail (dw::Runtime:50:49)`) を出す。DW で書かれた組み込み関数 (native でないもの) の中の枠は出ない。
  末尾再帰が 64 段を超えて失敗すると、途中の枠が欠ける (1 段ごとに記録しないため)。組み込み関数に渡したラムダの
  中の失敗は、実 DW は "Unknown location" と `main (anonymous:0:0)` にするが、mulay は位置を出す。
- **出力の encoding の文字集合**: UTF-8 / UTF-16 / UTF-32 / ISO-8859-1 / US-ASCII / windows-1252 以外
  (Shift_JIS など) は表せない文字の置換 (`?`) をしない。
- **メモリ**: 大きな JSON (8.6MB) の読み込みで最大 RSS が入力の約 23 倍 (203MB) になる。
- **XSD 検査 (mvn package) の失敗**: 実 Mule は mvn package の XSD 検査で、スキーマに合わない XML を落とす。
  mulay は XSD を持たず、そのまま読む。`mulay validate` が警告 (stderr の `warning:`、終了コードは 0) を出すのは
  次の書き方だけ。
  - `http:request` の子要素の順 (スキーマは body、headers、uri-params、query-params、response-validator)。
- **A2A の tasks/resubscribe のイベントの記録**: 送り直すイベントはプロセスのメモリに最大 1000 タスク分持ち、古いものから捨てる。
  実コネクタは上限なく持つかもしれない (確かめていない)。捨てたタスクへのつなぎ直しは、今のタスクだけを送って閉じない。
- **MCP の tools/list の並び**: 実 Mule は複数の tool の並びが起動のたびに変わる (フローの起動順)。mulay はフローの書いた順。
- **MCP の parametersSchema**: type、enum、minimum、maximum、minLength、maxLength、pattern、minItems、maxItems、items、properties、
  required、additionalProperties:false だけ検査する。oneOf、allOf、$ref、format など他のキーワードは通す。
  type が配列 (`["string","null"]`) のときの文言は確かめていない。
- **MCP の resource / prompt のフローの失敗の data**: 実 Mule は例外の型の名前 (raise-error では `DefaultMuleException`) を data に書く。
  mulay はどの失敗でも `DefaultMuleException: <説明>` にする。
- **MCP の resources/list と prompts/list の並び**: tools/list と同じく、実 Mule は起動のたびに変わる。mulay はフローの書いた順。
- **MCP の default-response-headers と reject-with-headers の並び**: 複数あると、実 Mule の JSON モードでの並びは起動のたびに変わる
  (SSE モードは書いた順の逆で安定していた)。mulay は JSON モードで書いた順、SSE モードで逆順。
- **MCP のセッションの置き場**: 実 Mule は sessionsObjectStore に {id、protocolVersion、transport} を入れる。mulay はメモリだけで、
  指定された Object Store は使わない (再起動でセッションは消える)。
- **MCP クライアントが on-new-session-listener に拒否 (403) されたとき**: 実 Mule のクライアントは操作を続けられ、ping は成功し list-tools は
  空、call-tool は "Unknown tool" になる (拒否されたはずのサーバーのセッションができているように見える。理由は分からない)。
  mulay は初期化の応答が 2xx でないので `MCP:SERVER_ERROR` ("Client failed to initialize by explicit API call") にする。
- **旧式の SSE で initialized の通知の前に来た要求**: 実 Mule のサーバーは、initialize の後、notifications/initialized が来る前の要求 (tools/call など) に
  答えず、POST も返らない。MCP の Java SDK の McpServerSession が、要求の処理の前に exchangeSink (notifications/initialized で初めて値が入る) を待つため
  (実 Mule で確認。同じサーバーへの別のセッションの操作は普通に動く)。mulay は initialize の後なら普通に処理する (initialize の前は 500)。
- **MCP の attributes の mediaType**: Java のオブジェクトの attributes には ^mediaType (`*/*`) などのメタデータが付く
  (実 Mule は MCP で確認。他のコネクタの attributes でも同じと見て付けた)。
- **jmx のログファイルの fileName**: 実モジュール (自作の mule-jmx-module 0.1.0) は `dir.resolve(fileName)` で読むので、`/etc/passwd` や `../x` のような
  logDir の外のファイルも読める (パストラバーサル)。mulay は絶対パスと `..` を含む名前を読まず `{"error":"Invalid log file name: .."}` にする
  (design.md §8)。`sub/app.log` のような下のディレクトリは読む。
- **jmx の最近のログ**: 実モジュールは Mule のランタイムの全ログ (起動のログなど) と Java の例外のスタックを入れる。mulay はアプリが出したログだけで、
  例外のスタック (`exception`) は持たない。thread は `[アプリ名].フロー名`。
- **jmx の JVM メトリクス**: collect-metrics / cpu / memory / gc / threads は、実モジュールと同じキーの構造で mulay のプロセスの値 (/proc) を返す。ヒープ = 匿名メモリ、非ヒープ = ファイルに載ったメモリ、GC・メモリプール・バッファプール・JVM の引数は空、classLoading は 0、threads.states は RUNNABLE だけ、vmName / vmVendor / vmVersion は "mulay"。
- **Cache の既定の鍵**: keyGenerationExpression の無い戦略は payload の SHA-256 を鍵にする。実 Mule は Java の直列化したバイト列を
  ハッシュするが、mulay は payload の書いたバイト列 (ev/bytes) をハッシュする。違いが外から見えるのは、既定の鍵の戦略に objectStore を指し、
  その店のキーを os:retrieve-all-keys で読んだときだけ。
- **Cache の永続する店**: 戦略の店が永続する (persistent) とき、mulay は payload だけをファイルに書き、attributes は書かない
  (再起動の後に当たると attributes は空)。実 Mule は CoreEvent を直列化して入れる。
- **Cache の synchronized**: mulay は常に鍵ごとに排他する (同じ鍵の 2 つ目は 1 つ目が終わるまで待ち、その結果を使う)。`synchronized="false"` は読まない。
