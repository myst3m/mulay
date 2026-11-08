# ADR (設計判断の記録)

mulay の設計判断と、その理由を残す。2026-10-14 にソースのコメントを全部消し、残すべき理由をここへ移した
(コードにコメントは書かない。理由は ADR に書く)。

- 書式: `# 番号 — 決めたこと`、状態、## 決定、## 理由、## 場所 (ns/関数名。行番号は書かない)。
- 「Clay の制約を避ける書き方」(001、017、033、042、048、072) は、単純にすると不具合や遅さが戻る書き方の一覧。コードを書き換える前に読む。
- 実 Mule の挙動そのものはテスト (test/fixtures) と docs/connectors.md・docs/compat/deviations.md・docs/mule-runtime.md が正。

## mulay.lib

- [001](001-clay-constraints-lib.md) Clay の制約を避ける書き方 (mulay.lib)
- [002](002-bigint-representation.md) 任意精度の整数は clay.bigint の BigInt を使い、Java の BigInteger の意味に合わせる
- [003](003-dec-bigdecimal-semantics.md) 10 進数は Java の BigDecimal と同じ unscaled × 10^-scale で持ち、scale と丸めの規則も Java に合わせる
- [004](004-regex-backtracking-vm.md) 正規表現は java.util.regex.Pattern 互換の部分集合を、明示スタックの後戻り VM と手数の予算で照合する
- [005](005-utf8-unicode-tables.md) 文字列は UTF-8 のバイト列のまま扱い、壊れた並びは最大部分ごとに U+FFFD にし、Unicode の表は生成して持つ
- [006](006-xml-parser-scope-and-limits.md) XML は整形式を確かめる pull パーサの上に DOM と書き手を置き、外部の資源は引かず、展開と属性の数に上限を置く
- [007](007-yaml-core-schema.md) YAML は 1.2 の core schema だけを解釈し、数の綴りとキーの順・重複をそのまま残す
- [008](008-deflate-zip.md) DEFLATE・gzip・ZIP は純 Clay で書き、展開に上限を置き、書き出しは固定 Huffman と固定の時刻にする
- [009](009-crypto-without-openssl.md) 暗号の部品は OpenSSL を使わず、clay.crypto・clay.pkix と OS の乱数と純 Clay で組み、名前は OpenSSL の綴りで引く
- [010](010-seal-format.md) 埋め込む値は PBKDF2 で導いた鍵の AES-256-CBC で封じ、暗号化してから HMAC をかける
- [011](011-ssh-sftp-pure-clay.md) SSH と SFTP は純 Clay の同期のクライアントにし、方式を絞り、strict kex と known_hosts の照合を持ち、SFTP の読み書きは要求を重ねる
- [012](012-sqlite-lib-internals.md) 純 Clay の SQLite は SQLite 3.50.3 のソースの手順を写し、B-tree のページは読み解いた形で持ち、分け方は SQLite と違ってよい
- [013](013-time-java-time-semantics.md) 日時は java.time と同じ意味で自作し、タイムゾーンの規則は OS の zoneinfo から読む
- [014](014-java-map-order-and-everit.md) Java の Map の反復順と everit の違反の並びは、ハッシュと表の手順を写して再現する
- [015](015-reproduce-java-libraries.md) Mule が使う Java のライブラリの判定と文言は、版を決めてその手順を写し、生成した期待値で照合する
- [016](016-fs-res-path-safety.md) ファイルの作成は 1 回の open で有無を確かめ、資源のパスは ".." を拒み、シェルに渡すパスは単一引用符で 1 語にする

## DataWeave (dw 直下)

- [017](017-dw-clay-constraint-idioms.md) Clay の制約を避ける書き方 (src/mulay/dw 直下)
- [018](018-dw-context-lexer-and-precedence-climbing.md) DW のパーサは手書きの再帰下降と precedence climbing にし、字句はパーサが文脈を渡して 1 トークンずつ読む
- [019](019-dw-ast-keeps-spelling-and-byte-spans.md) DW の AST は綴りとバイト位置を持ち、名前の解決と数値への変換は後段に任せる
- [020](020-dw-parser-intended-deviations.md) DW のパーサで実 DW と意図して変えた点: head-tail 構築子は診断、正規表現は検査しない、`json---` は json
- [021](021-dw-parse-error-recovery.md) DW のパーサは誤りから回復して読み続け、診断の連鎖は位置で抑える
- [022](022-dw-number-nint-ndec.md) DW の Number は 64 ビット整数 (NInt) と BigDecimal 相当 (NDec) の 2 通りで持ち、正規形を 1 つに決める
- [023](023-dw-numfmt-ports-java-decimalformat.md) 数値の書式は Java 17 の DecimalFormat を移植し、ロケールの記号は CLDR の表を埋め込む
- [024](024-dw-implicit-lambda-by-shape.md) 暗黙のラムダと遅延引数は、型ではなく式の形と組み込み関数の引数型で決める
- [025](025-dw-resolve-slots-and-hidden-origin.md) resolve は slot の番号を再利用せず、値の位置は location の隠れた引数で渡す
- [026](026-dw-user-modules-share-one-position-space.md) 利用者の DW モジュールは本体の後ろの位置から始まるように解析し、位置 1 つでどのソースかを決める
- [027](027-dw-deferred-map-staging.md) output の deferred=true で本体が `A map F` なら、A と F に分けたプログラムで 1 要素ずつ作る
- [028](028-dw-builtin-table-shape.md) 組み込み関数の表: (モジュール, 名前) ごとに 1 つ、型は番号で照合し、モジュールの定数も引数 0 の組み込みにする
- [029](029-dw-key-attrs-carried-in-meta.md) キー選択の結果は、キーの属性と名前空間をメタデータ `@attrs` / `@ns` で包んで運ぶ
- [030](030-dw-aot-observably-same-as-closures.md) 事前コンパイルの生成コードは、閉包のコンパイルと評価の順・失敗・深さまで同じにする
- [031](031-dw-generated-sources-not-hand-edited.md) fnarity.clay と stdlib_locs.clay は実 DW の .dwl から生成し、手で編集しない
- [032](032-dw-error-frames-built-while-unwinding.md) 失敗の位置と枠 (try の error.stack) は、失敗が抜けるときに DwErr に積んで作る

## DataWeave の形式と標準ライブラリ (dw/fmt・dw/lib)

- [033](033-clay-constraints-dw-fmt-lib.md) Clay の制約を避ける書き方 (dw/fmt・dw/lib)
- [034](034-format-dispatch-in-registry.md) データ形式の reader / writer の振り分けは fmt/registry の 1 か所に置く
- [035](035-dw-defined-builtins-call-operators.md) DW で書かれた標準関数はネイティブで書き、定義と同じ順で同じ演算子を呼ぶ
- [036](036-lazy-args-and-hidden-location.md) 遅延引数と「関数を返す」標準関数は、resolve が作る形を組み込みの側で受ける
- [037](037-reproduce-java-iteration-and-sort-order.md) 実 DW の結果に出る Java / Scala の内部の順序を、同じ計算で再現する
- [038](038-java-named-facilities-mapped-to-own-tables.md) Java の名前で引く機能 (文字コード、MessageDigest / Mac) は、名前を写して mulay と clay の実装で計算する
- [039](039-process-wide-state-and-os-sources.md) Mule との接点は大域の atom に持ち、環境変数と乱数は OS から直接取る
- [040](040-dates-periods-build-iso-and-reparse.md) Dates / Periods の組み立て関数は ISO の文字列を組んで読み直す
- [041](041-distinct-and-group-by-lookup.md) distinctBy と groupBy は、番号を先に決めてから組み立てる

## コネクタ (conn)

- [042](042-clay-constraints-conn.md) Clay の制約を避ける書き方 (conn)
- [043](043-http-routed-sources-in-stages.md) HTTP の経路で動くソース (A2A・MCP) は、要求を段に分け、フローは本体から渡された口で流す
- [044](044-connection-warmup-at-startup.md) Salesforce と Anypoint MQ の接続は起動のときに裏で用意し、最初の操作はそれを待つ
- [045](045-java-library-formats-per-connector.md) 実コネクタが使う Java のライブラリの読み書きを、コネクタごとに写す
- [046](046-objectstore-vm-persistence.md) ObjectStore と VM の永続は変わるたびにファイル全体を書き直し、店の期限は触れたときに確かめる
- [047](047-untrusted-paths-and-names.md) 外から来たパスと名前で、意図しないファイルや要求の構造に届かせない

## ランタイム (rt・mule・app・cli)

- [048](048-clay-constraints-rt-mule-app-cli.md) Clay の制約を避ける書き方 (rt・mule・app・cli)
- [049](049-connector-op-naming-contract.md) コネクタの要素は汎用の形で持ち、名前付けの規則を mule/parse と rt/conn の契約にする
- [050](050-expressions-compiled-at-load-lazy-inputs.md) 式はロード時にコンパイルし、参照する入力を字句で調べて必要なものだけ読む
- [051](051-connector-interface-sources-transactions.md) コネクタは関数の record で表し、ソースの周期とトランザクションの確定は rt と app が持つ
- [052](052-typed-value-states.md) TypedValue は state で値とバイト列の持ち方を分け、ストリームは ID で持つ
- [053](053-row-stream-lifetime.md) 行のストリームは登録表に ID で置き、寿命を要求 (相関 ID) の enter / leave で決める
- [054](054-deferred-output-and-streamed-map.md) deferred=true の出力と streaming=true の入力の map は、`A map F` を 1 要素ずつ書く
- [055](055-error-type-parent-table.md) エラー型の親子関係は、実物の jar の enum と実行時の parentErrorType から表に書く
- [056](056-app-loading-and-bundle.md) アプリはディレクトリ・JAR・単体の XML から同じ形 (Loaded) に読み、埋め込みは長さ付きの文字列の束にする
- [057](057-persist-file-format.md) 再起動をまたぐ値は店ごとに 1 ファイルへ全部書き直し、一時ファイルは毎回別の名前を O_EXCL で作る
- [058](058-http-listener-routes-and-startup.md) http:listener はポートごとの経路表で振り分け、全ポートが開いてから READY にする
- [059](059-inspect-masks-secret-values.md) mulay inspect / validate は、名前が秘密らしいプロパティと属性の値を **** と表示する
- [060](060-cli-arguments.md) CLI は <app> を省けばカレントディレクトリとし、埋め込んだ実行ファイルはプロパティとログレベルだけを受ける
- [061](061-string-parameters-skip-output-inference.md) String の引数は出力形式を推論せず、DW の String をそのまま Java の String として使う

## DB (db)

- [062](062-db-cells-follow-jdbc-types.md) DB の値と失敗は、JDBC ドライバが返す Java の型と例外の区別で持つ
- [063](063-sql-text-rules-and-parse-cache.md) SQL の本文は mule-db-client の規則で読み、読んだ結果と構文解析の結果を本文ごとに控える
- [064](064-sqlite-state-in-one-atom.md) 純 Clay の SQLite は接続と DB を 1 つの atom に置き、文は swap! の中で実行する
- [065](065-pg-batch-sync-segments.md) PostgreSQL の bulk と execute-script は pgjdbc と同じ Sync の区切りごとに 1 回の往復で送る
- [066](066-pg-follows-pgjdbc.md) PostgreSQL のドライバはセッション・値・キー・失敗を pgjdbc 42.7 に合わせる
- [067](067-wire-codecs-are-pure.md) DB のプロトコルの値の読み書きはソケットに触らない ns に分け、読み取りは (値 次の位置) と負の位置で失敗を運ぶ
- [068](068-mysql-connector-j-defaults.md) MySQL のドライバは mysql-connector-j 9.2 の既定の設定と同じに振る舞う
- [069](069-oracle-thin-protocol.md) Oracle は 23ai 以降だけを相手にする純 Clay の thin で、手順は python-oracledb 26、値と文言は ojdbc11 23.8 に合わせる
- [070](070-oracle-execution-semantics.md) Oracle の実行: 指定したキーの列は ROWID で読み直し、LOB の列のある select は全部読み、型の揃わない bulk は組ごとに実行する
- [071](071-generated-driver-tables.md) ドライバの文言と型の表は JDBC ドライバの jar から生成し、手で編集しない
- [072](072-clay-constraints-db.md) Clay の制約を避ける書き方 (src/mulay/db)
- [073](073-otel-grpc-export.md) OpenTelemetry のメトリクスの gRPC の送り出しは、実 Mule 4.12.0 (OTel Java SDK 1.60.1) の OkHttp の送り手に合わせる
- [074](074-listener-request-target.md) http:listener は要求の対象を実 Mule 4.11.3 の Netty の HTTP サービスと同じく扱う (壊れた対象は java.net.URI の文言で 400、404 / 405 の文言は受け取ったままのパスを escapeHtml4)
- [075](075-dw-default-catches.md) DataWeave の default は、型変換の失敗と null を渡した関数の型違いだけを受ける
- [076](076-db-query-timeout.md) DB の queryTimeout は、実行の間だけ動く見張りがドライバの中断を送る (PostgreSQL は CancelRequest、MySQL は KILL QUERY、Oracle は同じ接続への interrupt の marker と緊急データ。SQLite は未対応)
- [077](077-grpc-client.md) gRPC のクライアント (grpc:unary-call) は h2c で送り、結果は TypedValue に包んだ protobuf にする (実 Mule が止まる応答は gRPC の仕様で決める)
- [078](078-logger-json-fallback.md) logger の message の式は推論した形式で書き、その形式で書けなければ JSON で書く
- [079](079-grpc-server.md) gRPC のサーバー (unary-method) は http:listener の h2c の上で受ける (要求の枠の文言は grpc-java、失敗は trailer の grpc-status)
- [080](080-grpc-client-streaming.md) gRPC のクライアントのストリーミングは gRPC として正しく流す (open-call で送るたびに送り、届くたびに渡す。実 Mule のコネクタの溜める作りは真似しない。Deadline)
- [081](081-connector-source-packages.md) コネクタは本体と別のソースの package として配り、入り口のファイルが使うコネクタを並べる (.so の動的ロードはしない。コネクタと配布物は mulay の同じ commit を git: で固定する)
- [082](082-aot-stub-in-entry-package.md) mulay build は、入り口の package にある stub (事前コンパイルの登録表と埋め込みを返す) を差し替えてビルドする (本体は生成物を require しない。表は起動時に dw/engine へ渡す)
- [083](083-object-store-in-rt.md) ObjectStore の店は rt (rt/ostore) に置き、os コネクタは操作の層にする (idempotent-message-validator と Cache が同じ店を使うため)
- [084](084-connector-evaluated-source-expressions.md) source の式をコネクタが自分で評価する (raw-sources。http:polling-source の item / watermark のように Mule の束縛に無い名前を使うため。mule/parse は文字のまま残す)
- [085](085-polling-source-watermark.md) ポーリングの source (http:polling-source、db:listener) の watermark と id は rt/poll で、実 Mule の PollingSourceWrapper と同じ手順で扱う (http は watermark を文字列で比べる)
- [086](086-munit-runner.md) MUnit のテストを `mulay test` で回す (suite ごとに読み込み直し、source は動かさない。matcher は関数を持たないデータで、判定と Hamcrest の文言は conn/munit。正解は実 MUnit 3.7.4)
- [087](087-avro-binary.md) Avro のバイナリ符号化は lib/avro に置く (スキーマは節点の表、AVal は完全名を持ち union の枝は Java の resolveUnion と同じ規則で選ぶ。失敗の文言は Avro Java 1.11.5 のもの。正解は tools/gen-avro-golden.java)
- [088](088-salesforce-pubsub.md) Salesforce Pub/Sub コネクタ (publish-event と subscribe-channel-listener。gRPC は clay の h2、Avro は lib/avro、event は実 Mule の Gson を通した形と同じ値を直接作る。replay と流量制御は実 Mule と同じ)
- [089](089-salesforce-soap-headers.md) Salesforce コネクタの操作の headers は SOAP ヘッダにする (値は「ヘッダ名 → Map」。捨てる・失敗する規則は実コネクタの SalesforceUtils と同じ。queryMore にも付ける)
- [090](090-salesforce-bulk-metadata-headers.md) Salesforce コネクタの Bulk / メタデータ API の操作の headers (Bulk v1 は toString した HTTP ヘッダ、v2 は最初の POST にだけ付けて既定を置き換える。メタデータは実コネクタと同じく送らずにログだけ。Bulk v1 の失敗の型は BulkApiV1ErrorMappingType の表)
- [091](091-xml-spans.md) XML の要素と属性のバイト位置は lib/xml の XLines の XSpan に置く (XmlOpts の spans のときだけ取る。元のファイルの UTF-8 のバイト位置で、BOM と CRLF の正規化を戻す。実体の置換テキストから出た要素は -1)
- [092](092-app-model-json.md) アプリのモデルの JSON (mule/amodel と mulay inspect --json。XML の木と位置から組み、パスは parse と同じ規則で数え、種類はモデルから取る。support と effect は conn/registry の component-info。choice には必ず otherwise を置く)
- [093](093-host-port.md) OS に触る所 (ファイル・ディレクトリ・環境変数) を lib/host に集める (native は clay の関数、wasm は mount! で渡されたメモリのファイル表。名前は clay.core と重ならないように file-read など)
- [094](094-note-runner.md) ライブ・ノートの例の実行 (mulay.note.run と mulay note。コネクタは再生専用、記録が尽きたら halt で止めて held。トレースは engine の hook、値は ID で表に置く)
- [095](095-wasm-entry.md) wasm の入口 (mulay.wasm.main の load・run・get_value・components) と、wasm で組めない C の呼び出しを target-when で分ける所 (lib/host・lib/fs・lib/osinfo・DW の asin など)
- [096](096-rust-style-diagnostics.md) 開発者に見せるエラーを Rust 風にする (lib/diag で表示、dw/explain で DW の文言を読み替えて help を付ける。error.description・エラーの型・DW の golden は Mule の文言のまま)
- [097](097-entries-and-api-model.md) AppModel の入口の一覧と API 仕様のモデル (lib/youtline で仕様の位置)
- [098](098-app-to-app-bridge.md) livenote でアプリ間の http:request をつなぐ (host の関数 mulay_http と export call、conn/http_req に組み立てを分ける)
- [099](099-db-emulator.md) livenote の DB のエミュレータ (db/emu: 自前の SQLite のエンジン、方言の読み替え、各ドライバと同じ形の結果とエラー) と、記録との組み合わせ
- [100](100-config-ref-and-enum-checks.md) 存在しない config-ref と XSD の列挙の外の値 (logger の level、timeUnit) を、実 Mule と同じ文で読み込みのエラーにする
- [101](101-app-log4j2.md) アプリの log4j2.xml (Root/Logger の level、子のカテゴリへの継承) に従ってログを出す。無ければ実 Mule の既定のまま
- [102](102-contract-checks.md) 約束の突き合わせと仕様の example (livenote の段階 5)
- [103](103-with-cleanup.md) 取ったものは with-cleanup で返す (処理が途中で失敗しても)
- [104](104-request-body-spool.md) listener の大きな要求の本文は流して受け、512 KB を超えた分はファイルに逃がす
- [105](105-dw-lazy-sequences.md) DW の配列は遅延した並び (VSeq) でも持ち、使う所が明示して扱う
- [106](106-dw-prepared-calls.md) 同じ関数を何度も呼ぶ組み込み関数は、呼び手を 1 回準備する
- [107](107-dw-output-spool.md) DW の出力は spool に書き (64 KB ずつ、512 KB を超えたらファイル)、読み直せる流れ (PIPE) にする。書く前に値を入れ子まで読まない (JSON と NDJSON、UTF-8)
- [108](108-dw-function-values-cross-scripts.md) DW の関数の値が評価の外へ出る時は、ホストの関数 (実 Mule の WeaveFunctionWrapper: 引数は rhs: Array 1 つ) にする
- [109](109-mulay-dw-module-path.md) `mulay dw` は --path・スクリプトのディレクトリ・Mule プロジェクトの src/main/resources からモジュールを読む
- [110](110-dw-type-reuse-json-schema.md) `import .. from jsonschema!a::b::C` は JSON Schema を DataWeave の型の宣言に訳して、ふつうのモジュールとして読む
- [111](111-dw-test-builtin-modules.md) dw::test (Tests・Asserts) は mulay が持つ DataWeave のモジュールとして書き、等しさの差分だけ Clay の組み込みにする
- [112](112-apikit-version-oas31-validator.md) APIkit は pom の mule-apikit-module の版に従う: 1.13 以上の OpenAPI 3.1 は別の検証器 (json-sKema の文言)
- [113](113-dw-type-reuse-xml-schema.md) `import .. from xmlschema!a::b::C` は XSD を、実 DW が作るのと同じ DataWeave の型の宣言に訳して読む
- [115](115-clay-cycle-warnings.md) Clay の循環の警告: mulay の 12 件はすべて clay の誤検知で、clay が直した (delay と、置き場より後に作る値の判定)。mulay では黙らせない
- [116](116-otel-traces.md) OpenTelemetry のトレース: 文脈はイベント (SpanCtx) が持ち、スパンは engine の決まった場所で作る。形は実 Mule 4.11.3 の記録に合わせる
- [117](117-load-static-resource.md) `http:load-static-resource` と `${app.home}`: app.home の下はアプリの資源から読む (JAR のままでも)。パスと Content-Type とエラーは実 Mule 4.11.3 の StaticResourceLoader と記録に合わせる
- [118](118-server-surface-hardening.md) 外から叩ける口の守り (公開前の点検): 内部の状態のファイルは 0600/0700、MCP のセッションと A2A のタスクに期限と上限、MCP は Origin を調べ、A2A のプッシュ通知は内側のアドレスに送らず、listener は経路の無い要求の本文を読まない
