# 作業中の TODO

残っているものだけを書く。済んだものは git の履歴と docs/ (mule-runtime.md、connectors.md、compat/deviations.md) にある。

## ランタイムと DataWeave

- [~] DataWeave のコンパイルエラーの文言を実 DW のパーサに合わせる (golden `syntax_errors/`、実 DW の 1 行目、`dwt -e`)。
      残り: parboiled の規則名がそのまま出るもの (`expected Namespace`、`Attribute<..>`、`AlphaNum`、`interpolationExpr`、
      `digit09`、`content`)、空白の位置を指すもの (`[1 2]`)。`tools/dwt-all.sh -e` の不一致は 87 (静的な型の文言を含む)。
- [ ] lib/regex の `search`・`match-full`・`looking-at` は、無いことを 0 要素の Vec(Match) で表す (CLAUDE.md の規則では Option に移す)。
      呼び元は jsonschema・mcp_schema・dw/eval など。2026-11-01 に docstring を消した時に気づいた。
- [ ] dw::test の残り (ADR 111): TestResult の location (dw::Runtime location が引数を通した値の場所を持てば直る。実 DW は名前の文字列の場所)。
- [ ] xmlschema! の残り (ADR 113): attributeGroup・group の参照、入れ子の choice・sequence の細部、substitutionGroup。
- [ ] Mule の中の DW のエラー文の残り (validation-ops で記録、2026-11-02): (1) フローの変数の null は、関数の引数の説明で
      `Null (null as Null {encoding: "UTF-8", mediaType: "application/java; charset=UTF-8"...)` と型の情報が付く (mulay は `Null (null)`)。
      (2) 文字列の補間の Append の失敗は場所が無く、抜粋を出さず `Trace:\n  at main (Unknown)` になる (dw-oracle でも同じ)。
      再現: `<validation:is-true expression="#[true]" message="#['a $(vars.nope) b']"/>`。
- [ ] mulay 側のシナリオ実行器 (`tools/scn-run`、未作成) — 今は `tools/mule-oracle/mule-oracle mulay` で足りている。
- [ ] Batch: batch:history、streaming の aggregator、ジョブの input phase の失敗。
- [ ] OpenTelemetry のトレースの残り (ADR 116): parallel-foreach・first-successful・round-robin・batch・async の中の route のスパンの名前を
      実 Mule で記録して足す。HTTP 以外のソース (VM、JMS、Anypoint MQ ..) と HTTP 以外のコネクタ (Database は記録済み) の操作が実 Mule で
      どんなスパン (種類、名前、属性、受け渡し) になるかを記録する。送る列があふれたときの WARN の文言。`levelOverrides`。
- [ ] XA。
- [ ] シナリオ sftp-listener の /names が時々 (`MULAY_DW_LAZY_ALL=1` の時に 2 回に 1 回ほど) 違う: 起動の時点で無いディレクトリ
      li/never を見張る listener (l0) が止まらず、後から置いた never/n.txt を読む。2026-10-26 の前のバイナリでも出るので
      時機の問題 (ディレクトリを作る時と listener の初めの poll の前後)。listener が止まる判定の時機を実 Mule と比べて直す。

## DW 側の残り

- 値のセレクタを数に当てたとき (`1.a`、`{a: 1}.a.a`、`payload.a.a`): 実 DW 4.11.3 は null を返し、mulay は
  "You called the function 'Value Selector' with these arguments" で失敗する (2026-11-03、脆弱性の点検の途中で見つけた)。
  ほかの型 (Boolean、日付、関数) も実 DW で記録して golden にしてから直す。
- 値のソースの位置: 形でたどれない値 (関数の引数、関数の結果、入力から作った値) の位置。すべてに付けるには値が作られた
  場所を持つ仕組みが要る (docs/compat/deviations.md)。
- 静的な型の推論: 型の注釈・ジェネリクス・オブジェクトの形は推論しない (docs/compat/deviations.md)。型引数の上限
  (`fun f<T <: String>(a: T)` は実 DW では String として検査する。mulay は Any)、引数の数の合うオーバーロードが無いときの
  `(arg0, arg1)` の書き方。
- 再帰の段数 (2026-10-17 に測った。golden は test/fixtures/dw/recursion_test): 実 DW は、名前付きの関数とラムダの呼び出しを
  main を含めて 256 段まで許し、超えると `Stack Overflow. Max stack is 256` (組み込み関数の呼び出しは数えない。map のラムダから
  再帰すると 1 段に 2 つ数える)。末尾呼び出しを回すのは自分自身の呼び出しだけで、相互再帰は回さない (if・match の枝、do の結果に
  あれば回し、本体がそのまま呼び出しなら回さない)。mulay は式の入れ子を 3000 まで数え、相手を問わず末尾呼び出しを回すので、
  実 DW が 256 段で止める次のものを通す: 末尾でない 255 段以上、相互再帰、`default` や `or` の中の再帰、map のラムダからの 128 段以上、
  match の枝の中の末尾でない再帰の 254 段 (実 DW は match の枝でも 1 段に 2 つ数えるらしい)。
  本体がそのまま自分の呼び出しのとき止まらなかったのは直した (失敗の文言は Max stack is 3000)。段数を数えるには、call-def で
  段を数え、閉包の入口の深さの検査 (eval に 40 か所、gencode の deep) を式の深さだけに絞る必要がある。
- 初期化の前の変数を読むクロージャと、map / update の遅延評価 (docs/compat/deviations.md の「既知の差」)。
- 実 DW では a2a の ResponseAttributes の headers に `- "date"` を使うと空のオブジェクトになる (mulay は date だけを落とす。
  wsc の protocolHeaders では実 DW も date だけを落とす)。2026-10-16 に a2a-basic で気づいた。headers の Java の型を調べて合わせる。
- application/dw reader: `"1" as Number` を数に変換しない (2026-10-04 のセキュリティレビューで気づいた)。
- `payload.^mediaType`: 生のバイト列の TV で reader が mediaType を付けない形式 (protobuf) は TV の mime そのもの (引数付き。実 Mule と同じ)
  だが、JSON などは reader の付ける引数無しの mime (`application/json`)。実 Mule の JSON の payload の値は記録していない (2026-10-18)。
- `write(x, "application/x-protobuf", {..})` の型: 実 Mule 4.11.3 では String (test/fixtures/apps/grpc-client で `typeOf` が String、
  `as String {base: "64"}` はバイト列をそのまま出した)。同じ jar の dw-oracle (DW 2.11.2) では Binary で、mulay も Binary。
  記録したバイトは 0x80 未満だけなので、実 Mule の String が上のバイトを失うかは分からない。0x80 以上のバイトで実 Mule を
  記録して合わせる (2026-10-18)。

## コネクタの未対応 (詳細は docs/connectors.md の「できないこと」)

- [ ] gRPC: server-streaming-subscriber-source (アプリの起動時に動く購読。終わると onConnectionException)。TLS (connection-mode の
      tls) と OAuth / Google の接続も未対応。
- [ ] HTTP: request の認証 (NTLM、OAuth の他の grant)、multipart の組み立て、
      listener の `basic-security-filter` / ストリーミング応答。
- [ ] ObjectStore: config-ref (DB などに置く店)。
- [ ] File: lock (ストリームの消費を追う必要がある)、ファイルの属性 (所有者・権限) の操作、symlink の追い方、
      list の payload の遅延読み込み、listener の並行実行。
- [ ] SFTP: listener、鍵の認証 (identityFile)、proxy。
- [ ] APIkit 1.13 の OpenAPI 3.1 の検証 (ADR 112) で未確認のもの: oneOf で 2 つ以上が合う時の文言、if/then/else、dependentRequired、
      form (x-www-form-urlencoded) の本文。
- [ ] `mulay validate` は APIkit の仕様を読まない (RAML の !include や OpenAPI の外の $ref が読めないことは、run の起動で初めて分かる)。
- [ ] APIkit: console、strict validation、Exchange の依存 (`resource::...`) の API 仕様、RAML の discriminator / example の検証 /
      入れ子の uses / annotation、XML のスキーマ検証、flowMappings。
- [ ] Salesforce: saml-connection、config-with-oauth-connection、set-password / reset-password / change-own-password、
      proxy / TLS の設定、object listener の triggersQuery、replay の FROM_LAST_REPLAY_ID を Object Store に持つ、
      basic-connection と oauth-user-pass-connection の実 Mule との照合。
- [ ] Database: SQL Server など他のドライバ、XA、MySQL の証明書の検証・RSA の鍵交換・LOAD DATA LOCAL。
- [ ] Database (SQLite): 接続どうしの書き込みのロックが無い。トランザクションの中で書いている間に別の接続も書けてしまい、
      後のコミットが先の書き込みを消す (lost update)。実 Mule (sqlite-jdbc 3.50.3) は 2 つ目の書き手が busy timeout (既定 3 秒) だけ待って
      "[SQLITE_BUSY] The database file is locked (database is locked)" (DB:QUERY_EXECUTION)。queryTimeout はその呼び出しの間の
      busy timeout になり (1 秒、2 秒、300 ms は切り上げて 1 秒)、終わると元に戻る (2026-10-17 に測った。ファイルの DB に 2 つの設定)。
- [ ] Database (SQLite) の性能: lib/sqlexec に検索の計画が無く、INTEGER PRIMARY KEY (rowid) の範囲や index の範囲でも表を
      全部なめる。100 万行の表で `SELECT .. WHERE id <= 100` が 650 ms (libsqlite3 の FFI だった 10/11 より前は 0.55 ms)。
      perf では行ごとの列名の探索 (sqlexec/lookup の str/lower-case) が 25%。全行を読む select も 0.70 秒から 1.27 秒に遅くなった
      (`tools/mule-bench/soak` の /small と /sum、2026-10-26)。rowid と index の範囲を seek に直し、列名は解決の時に添字にする。
- [ ] Database (SQLite): 再帰の CTE が 1,000 万段で "recursion limit" になる (lib/sqlexec)。実 SQLite に上限は無い (1 億行を数えられた)。
- [ ] Database (PostgreSQL): execute-script の 1 行に `;` で区切った複数の文 (`UPDATE ..; INSERT ..`)。pgjdbc は文を分けて送り、
      失敗の Batch entry の番号を分けた文で数え、番号が組の数を超えると文面は `<unknown>` になる (2026-10-17 に測った:
      2 行目の 2 つ目の文の失敗は "Batch entry 2 <unknown> was aborted: .. Position: 14"、Position は先頭の空白を含めて数える)。
      mulay は 1 つの文として送り "cannot insert multiple commands into a prepared statement" になる。成功のときの件数の配列は未確認。
      Oracle (19c 以前は対象外、2026-09-30 決定): REDIRECT、TCPS、ネットワーク暗号化 (NNE)、ROWID の bean の中身の確認、
      配列や OBJECT 型のパラメータ。
- [ ] VM: redelivery-policy。
- [ ] Salesforce Composite: oauth-jwt-connection、oauth-saml-connection、config-with-oauth-connection、proxy と tls:context、gzip の応答。
- [ ] WSC: WS-Security の署名・暗号・検証・復号、MTOM と添付、http-transport-configuration (requesterConfig)、入力の要らない操作の本文の自動生成。
- [ ] Vectors: ほかの埋め込みの接続 (OpenAI、Azure OpenAI、Hugging Face、Mistral、Nomic、Einstein、Vertex AI)、ほかの保存先 (pgvector、Chroma、Qdrant、Milvus、OpenSearch、Elasticsearch、Pinecone、MongoDB Atlas、AI Search、AlloyDB、Weaviate)、multiformat (Tika) の読み取り、query-all、embedding-generate-from-document / media。
- [ ] Validation: validation:config の i18n (文言の差し替え)。is-number の COMPAT の記号 (NaN と fr の桁区切り以外)、IDN の nameprep の全体 (docs/compat/deviations.md)。
- [ ] A2A: `task-repository-object-store` の子要素の形。
- [ ] Anypoint MQ: subscriber の circuitBreaker、クロスリージョンのフェイルオーバー、接続の tlsContext / proxy / TCP の設定、
      フローへの並行な配信、subscriber を始めるときの失敗 (認証、存在しないキュー) の実 Mule との照合。
- [ ] MCP: クライアントの authentication / tlsContext、file-image-data、outputSchemaDefinition、
      SSE のサーバーの requestTimeout、クライアントのエラー型 (UNAUTHORIZED / REQUEST_TIMEOUT / INVALID_URI / SCHEMA_VALIDATION_FAILED) の条件、
      `mulay validate` での mcp の検査。
- [ ] MCP (実 Mule の不具合らしい挙動。MuleSoft への報告を検討): SSE の拒否で rejectWithMessage と reject-with-headers が届かない、
      拒否ヘッダの null 値が長い IllegalArgumentException の 500 になる、initialized 前の要求が答えもエラーもなく保留される。
- [ ] secure-properties: AES 以外のアルゴリズム、値の中の `${secure::..}` の入れ子。

## XSD との照合で分かった未対応 (2026-10-08。詳細は docs/connectors.md の「実コネクタの XSD との照合」)

優先度は未定。実アプリで使われやすく、結果が変わるものを先に挙げる。

- [ ] Database: parameterTypes、useColumnNumbers、autoGeneratedKeysColumnIndexes、transactionIsolation、
      db:listener の transactionalAction、他のドライバの接続 (mssql / derby / data-source)。
- [ ] HTTP: `basic-security-filter`、polling-source の属性の形 (pollingRequestHeaders など)、
      接続の maxConnections / connectionIdleTimeout / usePersistentConnections / streamResponse。
- [ ] SFTP: list の matcher、lock、writeStrategy、identityFile。
- [ ] File: lock、listener の watermarkMode、list の subset。
- [ ] A2A: クライアントの push-notification-config の 4 操作、get-card の useExtendedCard。
- [ ] Salesforce: 全操作の readTimeout、triggersQuery、replay の autoReplay など、パスワードの 3 操作。
- [ ] MCP: reconnectionDelay、sessionsObjectStore。
- [ ] APIkit: `console`。
- [ ] 読まない要素 (`<db:parameter-types>` など) の警告。

## SQLite と外部ライブラリ

- [ ] SQLite のファイルの DB を clay.io の File (pread / pwrite、fsync、バイト範囲のロック。clay 0.85.0 で入った) と
      rollback journal で書く (今は全部読み、全部書く。docs/sqlite.md)。
- リンクするのは libc と libm (glibc) だけ (2026-10-13)。libm は wasm には無い (clay の ADR 057)。wasm 版を作るときに clay に依頼する。

## Clay への依頼 (返事を待っているもの)

- (2026-11-01) `str`・`print`・`println` に Option を渡しても型の誤りにならず、`#clay.core/Some{:v ..}` と書かれる。
  clay 0.109.0 で C の `char*` が `Option(Str)` になった時、mulay の fs の誤りの文 (strerror) が黙ってこの形に変わった
  (テストを強めて見つけ、match で開けて直した)。最小の再現を送り、clay は 0.110.0 で再現して穴として扱う。mulay では C の答えは
  必ず match で開ける。
- (2026-11-01) clay のロードマップ (clay の docs/development/plans/030-roadmap.md) に、mulay が上げた困りごとが 3 つとも入った。
  段 1 は 1.0 (最短 0.113 前後)。段 2 (1.x) の順は次のとおり。
  1. str・print・println に Option を渡すと `#clay.core/Some{..}` と書く穴 (上の件)。
  4. 写しの警告を既定にする。写すつもりの所は `(copy x)` と書けば黙る。入ったら、mulay の 4 か所 (ADR 001 に理由を書いて
     残したもの: regex の先読み・後読み 2、time.fmt の幅を指定した項目、sqlbtree の内側の節での削除) に `(copy x)` を書く。
  6. 空のリテラルと fn の引数の型の推論。入ったら、`(let [z: Vec(T) []] z)` (150 か所) や型を書いた fn リテラルを減らせる。

- (2026-10-12) 大きな Str を手放しても OS に返らない (malloc_trim でも返らない) ことを依頼 (中)。JAR から起動すると、資源だけを
  取り出して JAR を手放しても、RSS が JAR の大きさだけ残る (max-core の JAR で 149 MB、ディレクトリからなら 83 MB)。
- (2026-10-19) コネクタを本体と別に配る仕組みは、Rust の crate のようなソースのパッケージにする (ユーザーと clay の判断。.so の
  動的ロードはセキュリティの危険が大きいのでやめた)。clay 0.94 の `git:` 依存で実現した (ADR 081。段 1〜6 は 2026-10-20 に済み。
  外のコネクタは操作・source・エラーの親・parse の表・listener に足す経路を持てる。見本は templates/connector、確かめは
  tools/pkg-check.sh)。配布物の `mulay build` は ADR 082。rt に残っていたコネクタの知識 (HTTP の例外のクラス名、
  `DB:QUERY_EXECUTION` の既定) も移した。残り: `mule/ignored` は本体だけ。

- (2026-10-26) 空いたプールのページを、それを作ったキャリアのヒープしか使えない。要求が別のキャリアに載ると RSS がキャリアの数だけ
  増え、新しいページのフォールトで遅くなる (csv2json 2.0 s → 3.3〜4.7 s)。MADV_HUGEPAGE つきの populate が断片化した時に直接
  コンパクションで止まる (xml2json の 5%)。clay 0.101.0 (ADR 134) で直り、mulay で効くことを確かめた (下の性能の表)。
  残り: 1 枚ずつ返したページの下で huge page が割れ、gen が時々 0.1 秒遅くなる (clay が判断する)。

## 性能

どの段も実 Mule より速いこと。最新の値 (2026-10-17、mulay 38987f3、clay 8aa412f9。req/s):

clay 8aa412f9 は 0.88.0 に ADR 104 の直し (数える欄を持つ record を C の値にするのは 2 つまで) を足したもので、同じ日に 0.89.0 として
リリースされた。0.87.0 と 0.88.0 では、DwErr などを値で写すたびに待ちが出て DW の評価が約 2 倍遅く、nested (366) が実 Mule (416) を
下回る (clay と切り分けた。0.86.5 → 0.87.0 で遅くなった)。0.89.0 (mulay 3d1a7aa) で測り直しても同じか少し速い
(mulay: compute 1,451、nested 749、transform 13,663。AOT: compute 2,286、nested 1,762)。

条件: `test/fixtures/mulet-samples/bench` (target/bench)。サーバ・実 Mule の JVM 全スレッドをコア 0-1、`wrk -t2 -c8` をコア 2-3、io の上流は
mulay の小さなアプリ (target/bench/up) をコア 4-5、各フロー 5 秒温めて 10 秒測る (target/bench の `target.sh`、`pass.sh`)。
実 Mule は `-XX:ActiveProcessorCount=2 -Xmx2048m`、全フローを一巡温めた後。mule-oracle は実行ごとに wrapper.conf を書き直すので、
JVM の引数は target/bench/bench/scenario.scn の `%%% jvm` に書く。実行は `MULE_ORACLE_RUNTIME=<絶対パス>/target/mule-bench-runtime
tools/mule-oracle/mule-oracle run target/bench/bench` で、Tanuki のラッパーではなく JVM の pid に `taskset -a -cp 0-1` をかける
(ラッパーに掛けると固定できず 3 倍速く出る)。機械の揺れの対照に、10/5 に作った AOT のバイナリ target/bench/bench-aot を同じ時に
測る (今回は 10/5 の 95〜98%)。

| フロー | Mule 4.11.3 | mulay | mulay build (AOT) | mulay / Mule |
|---|---|---|---|---|
| echo | 24,965 | 78,155 | 103,278 | 3.1x |
| routing | 21,391 | 83,196 | 85,910 | 3.9x |
| transform | 7,687 | 12,636 | 17,347 | 1.6x |
| pipeline | 4,026 | 10,216 | 12,739 | 2.5x |
| compute | 858 | 1,430 | 2,150 | 1.7x |
| nested | 416 | 719 | 1,722 | 1.7x |
| io-simple | 12,325 | 50,063 | 51,832 | 4.1x |
| io-pipeline | 9,109 | 25,610 | 29,496 | 2.8x |
| io-subflow | 11,862 | 42,742 | 44,789 | 3.6x |

RSS (負荷の後): Mule 918MB (JVM)、mulay 32MB、mulay build 36MB。同じバイナリのパス間のばらつきは 5〜10% ほど。

DW の式ごとの速さ (`tools/dw-bench/run.sh`、2026-10-26、入力は 10 万件・11 MB の JSON。実 DW は 4.11.3 同梱の 2.11.2 を
同じプロセスで温めた後の中央値、mulay は 5〜7 回の中央値。読み取り・評価・書き出しを含む):

| 件 | 実 DW | mulay | mulay build (AOT) |
|---|---|---|---|
| range-arith (`sizeOf((1 to 30000000) map ($ + 1))`) | 1,223 ms | 1,184 ms | 815 ms |
| obj-map | 317 ms | 190 ms | 211 ms |
| filter-select | 124 ms | 102 ms | 123 ms |
| concat | 230 ms | 125 ms | 120 ms |
| reduce | 183 ms | 103 ms | 123 ms |
| json-roundtrip | 215 ms | 139 ms | 164 ms |
| group-order | 233,007 ms | 267 ms | 399 ms |

AOT の列は数の読み取りの速い道より前の値。実 DW の group-order (groupBy の中で orderBy) は 1 回 233 秒かかる (出力は mulay と同じ)。
閉包の range-arith は、準備した呼び手と整数の算術の前は 2,903 ms (実 DW に負けていた)。range-arith の閉包はまだ実 DW と互角。

大きなファイルとデータの変換 (`tools/mule-bench/run.sh`、mulay は 2026-10-30・b7029eff・clay 0.105.0、実 Mule は 2026-10-27 (xml2json は 10-30)。入力は 100 万行で、CSV 45 MB・
JSON 114 MB・XML 142 MB、コピーは 1 GB。サーバーもクライアントも CPU 0-3 に固定し (ベンチは 4 コアまで)、ケースごとにサーバーを
立て直す。温め 2 回の後 3 回の中央値。cycles はサーバーの cgroup だけを perf stat で数えた値 (JVM の JIT と GC のスレッドを含む)。
出力は 6 件とも実 Mule とバイト単位で同じ (xml2json は 10-30 にも確かめた)):

| 件 | 実 Mule | mulay | ピーク RSS: Mule / mulay |
|---|---|---|---|
| copy (file:read → file:write) | 2,896 ms, 7.8 Gcyc | 323 ms, 1.6 Gcyc | 821 / 31 MB |
| csv2json | 5,553 ms, 27.3 Gcyc | 1,808 ms, 8.8 Gcyc | 840 / 45 MB |
| json2xml | 6,032 ms, 28.2 Gcyc | 2,306 ms, 11.3 Gcyc | 849 / 46 MB |
| xml2json | 3,881 ms, 18.1 Gcyc | 2,556 ms, 12.5 Gcyc | 913 / 46 MB |
| json-filter | 4,522 ms, 22.2 Gcyc | 1,184 ms, 5.8 Gcyc | 849 / 45 MB |
| json-agg | 7,088 ms, 36.8 Gcyc | 2,446 ms, 12.0 Gcyc | 1,166 / 1,046 MB |

- 実 Mule の RSS は JVM の全体 (待機時 840 MB 前後、-Xmx2048m)。mulay の待機時は 28 MB。
- 変換のメモリ: DW の出力を spool に流し (ADR 107)、CSV・JSON・XML の payload を並びで読み、配列のオブジェクトへの展開と XML の根を
  遅延したオブジェクトにした (ADR 105 第 4〜6 段)。2026-10-26 の前は csv2json 1,712 MB、json2xml 1,568 MB、xml2json 2,691 MB だった。
- xml2json: clay 0.101.0 では実 Mule より 2 割遅かった (4,974 ms、23.3 Gcyc、70.8 Ginsn)。XML の読み手の時間の多くが clay の record の
  手間で (大きな record の assoc の連なりで欄を取り出せず作り直す、record の解放が汎用の rec_drop を通る)、clay 0.102.0 で直った。
  mulay 側の 2 つ (UTF-8 の検査で ASCII を飛ばす、1 単位の確かめの振り分け) と合わせて 3,513 ms・17.0 Gcyc・50.1 Ginsn。
  142 MB を読むだけなら 1,920 ms が 970 ms。その後、XML の読み手が出来事を作らずに値を直接組む形にして (ADR 105 第 7 段)、
  3,468 ms・16.3 Gcyc・47.6 Ginsn が 2,556 ms・12.5 Gcyc・38.8 Ginsn。数の読み取りの速い道 (18 桁まで) で csv2json も 5% 縮んだ。
- json-agg のピーク RSS (1,037 MB) は実 Mule の全体 (1,190 MB、JVM の土台 840 MB を含む) より少ないが、値の表現は太い
  (114 MB の JSON を全部読むと 855 MB、1 項目あたり約 142 バイト。名前 (Key) を項目ごとに作る分が約 30 バイトで、使い回すと 671 MB)。

耐久テスト (`tools/mule-bench/soak/soak.sh`、12 巡、巡の間に 12 秒待つ。1 巡は g1・sum・gen・fe を 1 回ずつと small を 50 回):

| | g1 (1 巡目 → 12 巡目) | 巡の直後の RSS | 12 秒待った後の RSS |
|---|---|---|---|
| clay 0.100.0 (CPU 0-7) | 0.40 → 0.38 秒 | 2.1〜2.9 GB | 637〜651 MB |
| clay 0.101.0 (CPU 0-3) | 0.42 → 0.40 秒 | 599〜641 MB | 197〜201 MB |

0.101.0 では gen (100 万要素を作って合計) が 12 巡中 5 巡で 0.67〜0.77 秒になる (他は 0.57〜0.61 秒)。1 枚ずつ OS に返した空きページの下で
huge page が割れ、取り直したメモリの一部が 4 KB ページになるため (clay と切り分けた。CLAY_POOL_KEEP=512 か、1 枚ずつ返すのをやめると
消える)。clay が判断する。
sum・fe・small は mulay の SQLite の後退 (上の Database (SQLite) の性能) で 0.71.0 のころの値と比べられない。

- echo・routing・io-* は 10/5 の mulay (90,683・94,820・60,493) の 8〜9 割。DW の出力を実 Mule と同じく chunked で返すように
  なったこと (書き込みが要求ごとに 1 回から 2 回強に増えた)、Date を付けることなどの mulay 側の変化で、clay の件ではない。

- 残り: ラムダの呼び出しごとに引数の Vec とフレームを作る (compute と nested の大半は関数呼び出し: 引数の Vec、フレームの確保と
  解放、call-def・bind-args)。
- メモリ: 大きな JSON (8.6MB) の読み込みで最大 RSS が入力の約 23 倍 (203MB)。

## MUnit (`mulay test`、ADR 086)

- [ ] munit-tools:spy (before-call / after-call)、mock-when の then-call。
- [ ] enable-flow-sources の scheduler とコネクタの source (HTTP の listener だけ起動する)。
- [ ] parameterizations、munit-tools の store / retrieve / queue / dequeue、munit:dynamic-port (要素の形)。
- [ ] surefire 形式の報告 (target/surefire-reports) とカバレッジ。suite の読み込みの失敗を、実 MUnit と同じく suite の名前のテストの ERROR として出すこと。

## DataWeave の関数の値

- [ ] map・filter・reduce などの右辺が名前だけ (`[1, 2] map g`) の時: 実 DW は右辺がラムダのリテラルでなければ `($, $$) -> 右辺` にする
  ので、`g` を呼ばずに関数の並びを作り、JSON に書けず "Cannot coerce Function to String" になる (filter は静的な型の誤り)。mulay の
  `resolve/maybe-fn?` は名前・呼び出し・do・if・match を包まずに関数として呼ぶ (2026-11-01 に dw-oracle で確かめた)。直す前に、呼び出し
  (ラムダを返す関数)・if・do・match の右辺の実 DW の扱いを dw-oracle で記録する。
- [ ] 組み込み関数の誤りの「But it expects one of these combinations」の並びが実 DW と違う: `+` に実 DW に無い (Period, Period) がある、
  sizeOf に (Number) が無い、isEmpty は (Array) (Object) (String) のはずが重なって 7 つ出る (2026-11-01、dw-function-values を作る時に
  関数を渡して見つけた)。
- [ ] 関数を返した暗黙のラムダの結果の誤り: filter は実 Mule では場所の無い "Cannot coerce Function (<関数の表示>) to Boolean"
  (mulay は "(Function)" と書き、場所を付ける)、mapObject は場所が右辺 (mulay は演算子の左から)、orderBy は "You cannot compare a value of
  type :Function" の Trace が main だけ (mulay は dw::Core::orderBy の段と標準ライブラリの抜粋を出す)。


## Avro

- [ ] DW の形式 `application/avro` (schemaUrl を取る reader / writer) は未実装。mulay.lib.avro (ADR 087) の上に作れる。

## Salesforce


