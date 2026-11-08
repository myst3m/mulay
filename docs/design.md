# mulay 設計書

> mulet (Clojure, v0.3.1) を Clay 言語へ製品品質で移植する。
> 作成: 2026-09-28 (v0 計画)。根拠資料: `docs/clay-capabilities.md` (Clay 0.51.1 の能力調査)、mulet のコード調査。
>
> この文書は計画として書き始めたもの。現在の構成は §2・§3 に実在のファイルで書き、計画と違う実装になったところは
> 「実装:」として注記する。まだ無いものは (未実装) と記す。日付つきの「決定」は記録として残す。
> 2026-10-14 に実装と照合した (clay 0.86.5)。各部の詳細は `docs/mule-runtime.md`、`docs/dw-eval.md`、`docs/aot.md`。

## 0. 目的と非目的

**目的**
- Mule 4 アプリ (XML + DataWeave + properties) を、単一の小さなネイティブバイナリで高速起動・低メモリ実行する。
- **売り物になる品質**: 正しさの基準が明示され、テストで保証され、エラー時の挙動が予測でき、運用 (ログ・メトリクス・ヘルスチェック・graceful shutdown) に耐えること。

**非目的**
- `java!` の DataWeave 構文 (mulet と同じく未対応。理由を文書化する)。
- mulet の JIT、バイトコード VM、MUBC、Clojure コード生成、bench/disasm、corral/perf などの独自拡張。
- mulet の実装をなぞること。**mulet は仕様の参考資料**であり、mulet の既知の不具合と負債 (§10) は持ち込まない。

## 1. 正しさの基準 (オラクル)

判定の優先順位は次の順とする。

1. **実 Mule 4 ランタイム** (ローカルにある `~/srv/mule-enterprise-standalone-4.11.3`、`~/AnypointCodeBuilder/runtime/mule-enterprise-standalone-4.12.0`)。同じアプリ・同じ入力で出力を比べる差分テストを行う。
2. MuleSoft 公式ドキュメント (DataWeave 2.x リファレンス)。
3. (2026-10-23 まで) mulet の挙動。ただし 1・2 と矛盾しない範囲に限った。mulet は 2026-10-23 にアーカイブした (gitlab.com/myst3m/mulet)。今は 1・2 だけで判定する。

mulet 独自の拡張は採るか採らないかを個別に判断し、`docs/compat/deviations.md` に記録する。例: セレクタの大文字小文字を区別しない、`jwt::*` モジュール。

## 2. 全体アーキテクチャ

```
            ┌──────── CLI (run / validate / inspect / dw / build / version / help) ────────┐
入力        │                                                                              │
 dir/jar/xml ─► mule/load ─► lib/xml ─► mule/props (${} 解決) ─► mule/parse ─► Mule IR (mule/model)
                 │           (資源: src/main/resources か JAR の中身)          │  診断 (diags) があれば起動しない
                 └─► mule/lint (実 Mule が落とす書き方と読まない属性の警告。validate / run が出す)
                                                                               │
 #[..] と transform ─► dw/lex ─► dw/parse ─► AST ─► dw/resolve ─► 解決済み IR (dw/rir)
                                                       │  読み込み時に dw/eval が閉包の木にする
                                                       └► (mulay build のときだけ) dw/gen・gencode で Clay のソースにして
                                                          アプリ専用の実行ファイルへ (docs/aot.md)
                                                                               ▼
Runtime = app/run (ソース: http:listener・scheduler・ポーリング、起動と停止) + rt/engine (フロー実行・エラーモデル・
          スコープ・ルーター) + コネクタ (conn/registry の表) + DW の評価器
          + 横断機能 (rt/log、rt/ops の /__/health・/__/metrics、rt/meter と app/otel の OTLP メトリクス、
            rt/trace と app/otel の OTLP トレース、app/ammetric、SIGTERM での graceful shutdown)
```

- 計画にあった `.muir` (中間形式の読み書き)、`compile`、`schema`、`repl` のサブコマンドは (未実装)。
  独立した validator の段も無く、検査は mule/load・mule/parse の診断と mule/lint が受け持つ (`mulay validate` は
  読み込みとすべての DataWeave のコンパイルまでを行う)。`link` の段も無い (式は parse の時点でコンパイル済み)。

設計の核は次の 3 つの決定。

1. **式の評価器は 1 つ**にする。解決済み IR を木のまま歩く評価器で、変数参照は slot 番号に変換しておく。mulet には評価器が 4 つあり、同じ IR でも評価器ごとに意味が食い違っていた。この問題を根本から無くす。性能は閉包コンパイル (IR → Clay の closure の木) で後から上げる。その場合も入口は 1 つに保つ。
   実装: 閉包コンパイルは済み (dw/eval の compile-prog。dw/engine が読み込み時に 1 回行う)。`mulay build` の事前コンパイル
   (dw/gen、dw/gencode) も同じ ev/CProg を組み立て、生成しない節は dw/eval の閉包に任せる (docs/aot.md)。
2. **ペイロードは TypedValue** (値 + MediaType + encoding) で表す。reader は遅延させる (必要になるまで parse しない)。writer は境界 (HTTP 応答、ファイル書き出し、`write()`) で実行する。mulet の「transform の直後に文字列化する」モデルは採らない。
3. **失敗は値で返す**。Clay には例外が無く、`Values(T Err)` で返す。Mule のエラーモデル (エラー型の親子関係、continue/propagate) はそのまま戻り値の流れとして書ける。

## 3. リポジトリ構成 (パッケージ = 層)

計画 (v0) では rt/ に scopes・source・metrics・trace・health・shutdown を、mule/ に validate・muir・schema/ を置く予定だった。
実際には下のとおり (2026-10-14 の実在のファイル。lib/、conn/、db/ は代表とまとまりで書く)。

```
mulay/
  clay.pkg        パッケージ名と src の場所だけ (clay の版はここでは固定していない)
  src/mulay/
    lib/        汎用部品。Clay の stdlib に持ち上げられる品質で書く (mulay の他の層に依存しない)
      dec.clay bigint.clay numparse.clay ieee.clay   任意精度 10 進数・整数、数の読み取り、IEEE 754
      time/          日付・時刻・期間・タイムゾーン (tz.clay は TZif)・書式・ロケールの名前
      regex.clay     Java 正規表現の互換部分集合
      xml.clay yaml.clay csv.clay jsonschema.clay wsdl.clay
      uni.clay unitab.clay   UTF-8、コードポイント、大文字小文字の表
      zip.clay inflate.clay  JAR 展開
      crypto.clay hash.clay x509.clay keystore.clay secure.clay seal.clay random.clay   暗号・鍵・secure-properties
      ssh*.clay sftp.clay    SSH と SFTP のクライアント
      sql*.clay              純 Clay の SQLite (sqlparse、sqlexec、sqlbtree、sqlfile ほか。docs/sqlite.md)
      otlp.clay procstat.clay osinfo.clay signals.clay logfile.clay fs.clay glob.clay res.clay ほか
    dw/
      val.clay       DW の値モデル (§4)
      lex.clay / parse.clay (Pratt) / ast.clay / astdump.clay
      resolve.clay / rir.clay (解決済み IR) / eval.clay (閉包コンパイル) / engine.clay (入口)
      rt.clay sel.clay coerce*.clay num.clay numfmt.clay sty.clay tsel.clay javaobj.clay fnarity.clay loc.clay src.clay ほか
      gen.clay / gencode.clay / genreg.clay   事前コンパイル (mulay build。docs/aot.md)
      fmt/           reader と writer: json xml csv yaml multipart ndjson text dw (dwread) props eventstream scalar、
                     registry (形式の表)
      lib/           標準ライブラリ。モジュール単位 (core と core_*、strings arrays objects types dates periods numbers
                     binaries url math coercions diff timer tree values mime multipart crypto runtime system mule
                     validation dtd)
    mule/
      model.clay     Mule IR (プロセッサ・ルーター・ソース・コンフィグ)
      load.clay      読み込みの入口 (プロジェクトのディレクトリ、JAR、単体の XML。複数ファイルの統合、import)
      parse.clay     XML から IR へ。レジストリのキーは (名前空間 URI, ローカル名)
      props.clay     properties / global-property / secure-properties / ${} 解決
      lint.clay      実 Mule が落とす書き方と、読まない属性の警告 (validate と run が出す)
      ignored.clay   実コネクタの XSD にあって mulay が読まない属性の表 (tools/ignored-attrs.py gen が生成)
      dump.clay      inspect / validate の表示
      (計画の validate.clay、muir.clay、schema/ は (未実装)。コネクタのスキーマは埋め込んでいない)
    rt/
      event.clay     Event と TypedValue
      engine.clay    プロセッサの実行とフローの呼び出し。スコープとルーター (choice、foreach、parallel-foreach、
                     scatter-gather、try、until-successful、async、first-successful、round-robin、idempotent-message-validator、ee:cache) と batch:job もここ。
                     cache スコープは (未実装)
      error.clay     エラー型の階層とエラーハンドラ
      conn.clay      コネクタのインターフェース (§6.3)
      cron.clay      scheduler の cron 式
      log.clay       ログ
      ops.clay       運用の状態 (STARTING / READY / DRAINING) と /__/health・/__/ready・/__/metrics の本文
      meter.clay     Mule のメトリクスの数え (OTLP で送るとき)
      trace.clay     トレースのスパンを開いて閉じ、送る列に積む (OTLP で送るとき。ADR 116)
      stream.clay deferred.clay persist.clay javaser.clay   行のストリーム、deferred 出力、永続の店、Java の直列化
    app/
      run.clay       アプリの起動: http:listener・scheduler・ポーリングするソース、運用の端点、graceful shutdown
      otel.clay      OTLP のメトリクスとトレースの送信 (mule.openTelemetry.meter.exporter.*、tracer.exporter.*)
      ammetric.clay  Anypoint Monitoring の app_inbound_metric (_metric.log)
    conn/        コネクタの実装。registry.clay が表を持つ: http (tls.clay)、os、file、vm、db、sftp、apikit (apispec、raml)、
                 salesforce (sf_*)、a2a、mcp (サーバー) と mcp_client、anypoint_mq (amq_wire)、validation、wsc、jmx、
                 inference、vectors。ftp と grpc は (未実装)。OAuth はコネクタではなく http:request の認証 (http.clay)
    db/          SQL 共通層 (sql.clay、sqltext.clay) とドライバ: pg、sqlite (純 Clay)、mysql (mywire)、oracle (orawire、oraproto、oranum ほか)
    cli/         main.clay (入り口)、boot.clay (サブコマンドと起動)、aot.clay (事前コンパイルの stub。ADR 082)、opts.clay、help.clay、dwt.clay (DW の golden ランナー)。repl と Web UI は (未実装)
  test/
    <area>/                 deftest の area (dec、dwparse、eval、rt、mparse、db、sqlite ほか約 50)。各 area に src/mulay への symlink
    fixtures/dw/<分類>/*.dwt DW の golden (1 ファイル 1 ケース、期待値は実 Mule の DW)。mulet のテスト・公式ドキュメント・mulay 独自から作る
    fixtures/apps/<name>/   Mule アプリ + scenario.scn (要求と、実 Mule で記録した応答)
    fixtures/dw-corpus*/ dwparse/ otel/ am/   パーサの照合用コーパス、OTLP と Anypoint Monitoring の実 Mule の記録
  tools/
    test.sh new-test-area.sh dwt-all.sh dwt-aot.sh   単体テスト、area の作成、DW の golden (通常と事前コンパイル)
    gate.sh   確認一式 (ビルド、golden、単体、全アプリの照合の通常と遅延、MUnit。--wasm、--bench)。CPU 4 つに固定する
    dw-oracle/ mule-oracle/ sqlite-oracle/   実 DW・実 Mule・SQLite で期待値を作る・照合する
    docs-fixtures/ extract-dw-corpus.py   公式ドキュメントから golden とコーパスを書き出す
    gen-*.{java,py} ignored-attrs.py   表と golden の生成器
  deploy/        Dockerfile (RTF 用を含む)、rtf/ の entrypoint と probe、k8s/ の例
  templates/     アプリのテンプレ (agent-harness、stat-models。test/fixtures/apps から symlink で照合に入る)
  docs/
```

**依存の向き**: `lib` ← `dw` ← `mule` ← `rt` ← `conn` ← `app` ← `cli`。`db` は `lib` だけに依存し、`conn` (conn/db) が使う。
逆向きの依存は禁止する。rt はコネクタを直接知らず、`rt/conn` のインターフェースと conn/registry が作る表だけを見る。

## 4. DataWeave の値モデル

```clojure
(defvariant Val
  (VNull)
  (VBool b: Bool)
  (VNum n: Num)                          ; Num = Int の高速パス | Dec (任意精度) | Float
  (VStr s: Str)
  (VArr xs: Vec(Val))                    ; 大きな配列や遅延列は VSeq
  (VSeq src: Lazy)                       ; ストリームと遅延列 (repeatable)
  (VObj es: Vec(Entry))                  ; 順序を保ち、重複キーを許す。Entry = key(QName) + attrs + value
  (VDate …) (VDateTime …) (VLocalDateTime …) (VTime …) (VLocalTime …) (VTimeZone …) (VPeriod …)
  (VBin b: Bytes)
  (VRange from: Int to: Int)
  (VRegex r: Regex)
  (VFn f: Closure)                       ; ユーザー定義関数と組み込み関数
  (VType t: DwType)
  (VMeta v: Val schema: Vec(Entry)))     ; `<~ {…}` と `.^` で扱うメタデータ
```

- **数値**: DW の Number は 10 進数の意味論を持つ。整数は Int で持つ。Clay の Int は溢れると wrap するので、溢れを検知したら Dec に昇格させる。`/` は Dec で計算する (DW と同じく、割り切れなければ既定の精度で丸める)。Float を使うのは `as Number {class: "java.lang.Double"}` のように明示された場合だけにする。
- **オブジェクト**: `Vec(Entry)` にし、キーの索引は必要になった時点で作る (小さいオブジェクトは線形探索)。Clay の Map は順序も重複キーも保たないので使わない。
- **所有権**: Clay の値は参照カウントで、共有中の値を書き換えると複製される。DW は不変値だけを扱うので、評価器は値を**借用で渡し、新しい値を組み立てる**書き方に統一する。大きなオブジェクトを 1 か所だけ変える操作 (`update`、`mergeWith`) は、所有権が移る経路でその場更新になる。
実装 (dw/val.clay) との違い: Int に収まる整数は `VInt`、それ以外の数は `VNum` に分けた。`VSeq` (遅延列) は (未実装) で、
DB の結果などの行のストリームは rt/stream が持つ。`VKey` (キーの値) と `VNsV` (Namespace の値) を足した。`VBin` は Str、
`VRegex` はソースとフラグで持つ。

- **TypedValue**: `{value: Val-or-Raw, media: MediaType, charset}`。Raw (未 parse のバイト列) は、最初に選択操作を受けた時点で parse して結果を保持する。これが Mule の「遅延パース」と同じ振る舞いになる。

## 5. DataWeave 処理系

- **字句解析 + Pratt パーサ**を手書きする。EBNF は mulet の `resources/grammar/dataweave.ebnf` を仕様として参照する。加えて mulet の未対応部分も実装する: 任意の 2 引数関数の中置呼び出し、`mod()` 形式、`dw::x::f()` の完全修飾、ジェネリクス `<T>`、`.#`。
- **エラー位置**: すべてのノードに span を持たせ、Mule と同じ形式 (行、列、ソースの抜粋、キャレット) で報告する。
- **resolve 段**
  - 名前を解決し、import を正しく反映する (import していないモジュールの関数は呼べない。Core は暗黙に import される)。
  - クロージャの捕獲を解析し、変数を slot 番号に置き換える。
  - 中置の `$` を暗黙にラムダ化する (mulet と同じ除外リストを使う)。
- **組み込み関数の多重定義**: DW は型でオーバーロードする (例: `sizeOf(Array | Object | String | Binary)`)。関数表は `name → [(引数の型パターン, 実装)]` とし、実行時の値の型で選ぶ。
- **型システム**: `is`、`as`、match の型パターン、関数の型注釈は、実行時の型検査を行う (mulet は検査していなかった)。
- **format プロパティ**: JSON、XML、CSV を中心に、公式の reader/writer プロパティを網羅する。対応状況は `docs/dw-formats.md` で管理する。

## 6. Mule ランタイム

### 6.1 Event とエラー
- `Event { payload: TypedValue, attributes: TypedValue, vars: Vars, error: Option(MuleError), correlationId, ctx }`
- `Vars` は `Vec((Str, TypedValue))` にするか、Clay の Map(Str TypedValue) にする (計測して選ぶ)。
- **MuleError**: `{type: ErrorType(namespace, identifier, parent), description, detailedDescription, cause, errorMessage, childErrors}`。
- **エラー型の階層**は Mule 公式の表を持つ: `ANY` ← `MULE:*`、`HTTP:NOT_FOUND` → `HTTP:RESPONSE_VALIDATION`→… など。照合は親子関係をたどって行い、カンマ区切りの複数型と `when` 式にも対応する。
- プロセッサは `Values(Event MuleError)` を返す。try、on-error-continue、on-error-propagate は、この戻り値の流れとして書ける。
- 実装 (rt/event.clay、rt/error.clay): `Vars` は `Vec(Var)`、error は 0 か 1 個の `Vec(err/MErr)`。Event は corr、flow、tx
  (トランザクションの ID)、frame と callers (FlowStack) も持つ。実行関数は `Values(Event Vec(MErr))` を返し、エラーのときも
  その時点の Event を返す。

### 6.2 並行モデル
- 1 リクエストを 1 つの green スレッド (`clay.async/go`) で処理する。I/O は park する。
- **scatter-gather と parallel-foreach**: go + チャネル + deadline で書く。maxConcurrency はセマフォ (バッファ付きチャネル) で制御する。
- **async**: go で起動する (投げっぱなし)。maxConcurrency を守る。
- **scheduler**: fixed-frequency と cron (Quartz 形式、タイムゾーン対応) を持つ。disallowConcurrentExecution を守る。
- **CPU 並列**: Clay の `pmap` / `future` は OS スレッドを使う。par-safety の制約があるので、DW の評価は green スレッド側で行い、OS スレッドはフローの並列度を上げる用途に限る。スレッド数は構成で決める。

実装は上の計画と違い、mulay のコードは green スレッドではなく OS スレッド (`future`、`-DCLAY_PARALLEL`) で並行にする:
- app/run: http:listener のポートごと、scheduler ごと、ポーリングするソースごとに future。scheduler は 1 回の実行が終わってから
  次の時刻を決めるので重ならない。
- rt/engine: scatter-gather のルートと parallel-foreach の要素は future で同時に動かし、maxConcurrency は同時に動かす worker の数、
  timeout を過ぎたものは MULE:TIMEOUT。async は rt/ops の spawn-bg で別スレッドに出し、maxConcurrency はセマフォで守る。
- DW の評価器は大域の可変状態を持たないので、Event を別スレッドへ渡してよい (docs/adr/048)。

### 6.3 コネクタのインターフェース
Clay には protocol が無い。コネクタは**関数を持つ record** として表す。

```clojure
(defrecord Connector
  [name: Str
   ns-uri: Str                              ; XML の名前空間
   schema: ConnSchema                       ; config、connection、operation、source の属性定義 (埋め込み)
   connect: Fn(Config Values(Conn Err))
   disconnect: Fn(Conn Unit)
   validate-conn: Fn(Conn Values(Bool Err))
   ops: Map(Str OpImpl)                     ; OpImpl: (conn, 解決済みパラメータ, event) -> Values(TypedValue+attrs Err)
   sources: Map(Str SourceImpl)])
```

実装 (rt/conn.clay) はこれより小さい: `Connector {name uri run sources push poll tx-end init}`。操作は `run` 1 つが
OpCall (操作名、パラメータ、式を評価する関数) を受けて OpResult を返す。config と接続はコネクタの中で扱い、
schema・connect・disconnect の欄は無い。

- コネクタの登録は静的な表 (conn/registry.clay) で行う。実行時にリフレクションは使わない。
- **パラメータの式はパース時に DW IR へ変換**しておく。mulet は `#[...]` を実行のたびに parse していた。
- **接続プール**はコネクタ共通の汎用プールにする (最小数、最大数、idle timeout、validation)。
  実装: 共通のプールは (未実装)。プールはコネクタごとに持つ (conn/db、conn/sftp ほか)。

### 6.4 HTTP
- listener には `clay.http/run-server` (HTTP/1.1 と HTTP/2、TLS) を使い、path パターン、allowedMethods、response/error-response builder、ストリーミング応答を実装する。
- request には `clay.http/request` を使い、TLS、proxy、basic/OAuth2 認証、followRedirects、responseTimeout、コネクションプールを実装する。
- **Clay 側に足りないもの** (mTLS、ストリーミングの request/response body、Cookie、WebSocket) は、Clay 本体へ機能要望として出す (§9)。

### 6.5 DB
- `db/sql.clay` を共通層とする: 値 (`Cell`、JDBC の getObject が返す Java の型の区別)、結果 (`Outcome`)、失敗 (`DbErr`、
  SQLState と例外の class)。Mule の意味 (SQL の読み方、操作ごとの結果の形、エラーの型) は `conn/db.clay` と `db/sqltext.clay`。
  接続は設定ごとのプールから借りて返す。
- ドライバ
  - **PostgreSQL**: 純 Clay。`clay.postgres` を拡張して、拡張クエリプロトコルと型付きの行を扱う。
  - **SQLite**: FFI (libsqlite3)。
    実装: 2026-10-11 の決定で純 Clay に替えた (db/sqlite と lib/sql*。docs/sqlite.md)。FFI 版は削除済み。
  - **MySQL**: 純 Clay のプロトコル実装 (P2)。実装済み (db/mysql、db/mywire)。
  - **Oracle**: 純 Clay の thin プロトコル (TNS / TTC)。**決定 (2026-09-30)**: OCI (Instant Client) は使わず、最初から
    thin で書く (依存なしで配布するため)。M3 に前倒しし、共通層 → PostgreSQL / SQLite → Oracle の順に進める。
    実 Mule との照合には既存の Oracle DB を使う。
    実装 (2026-09-30): `db/orawire` (パケットと TTC の値)、`db/oraproto` (メッセージ)、`db/oranum` (NUMBER)、
    `db/oracle` (接続、O5LOGON、実行、fetch、LOB の読み取り)。暗号は clay.crypto と clay.pkix (`lib/crypto`。2026-10-13 まで libcrypto の FFI)。
    対象は 23ai 以降 (FAST_AUTH と応答の終わりの印)。19c 以前の手順 (PROTOCOL / DATA_TYPES を別に送る) と
    TCPS、ネットワーク暗号化、名前付きの時間帯は未対応。
- H2 は使えない。テストには SQLite を使い、H2 を前提にした mulet のテストは SQLite へ移す。

## 7. CLI と互換性

- **コマンド名**は `mulay`。計画では mulet と同じサブコマンドとオプションを持つ (`run`、`compile`、`validate`、`inspect`、`schema`、`repl`、`build`/`bundle`)。
  実装 (cli/main.clay、cli/help.clay): `run`、`validate`、`inspect`、`dw` (DataWeave を 1 回評価)、`build`、`version`、`help`。
  `compile`、`schema`、`repl`、`bundle` は (未実装)。`build` は mulet の build/bundle と違い、DataWeave を事前コンパイルしアプリを
  埋め込んだ専用の実行ファイルを作る (docs/aot.md)。
- **.muir** (未実装): mulay 独自の形式 (version 2.x、EDN) で読み書きする。mulet 1.1 の .muir は読まない (source から再コンパイルしても数 ms で済むため)。
- **Web UI** (未実装): mulet の React UI (`ui/`) の API 互換 (`/api/*`) を提供し、ビルド済みの資産をバイナリに埋め込む (P2)。

## 8. 品質保証

| 層 | 手段 |
|---|---|
| lib | 単体テスト (deftest、ASan/LSan)。regex、dec、time、xml はプロパティテストと fuzz (パーサがクラッシュしないこと) |
| DW | golden コーパス: (1) mulet のテストから自動抽出、(2) 実 Mule でこれを再評価して期待値を確定、(3) 公式ドキュメントの例。合格率を CI の閾値にする |
| Mule | アプリのシナリオテスト: `test/fixtures/apps/*` を mulay と実 Mule の両方で起動し、HTTP 要求に対する応答を比べる |
| 非機能 | 起動時間、RSS、スループット (wrk)。Mule 4.11 の baseline と比べる (当初は mulet の `docs/benchmarks` とも比べた。mulet はアーカイブ済み)。リークは ASan で 0 にする |
| 運用 | graceful shutdown、ログ (レベル、カテゴリ、JSON 出力)、`/__/health`、`/__/metrics` (Prometheus)、OTLP のメトリクス (実 Mule 4.12 の `mule.openTelemetry.meter.exporter.*`)、OTLP のトレース。実装済み: graceful shutdown (app/run、SIGTERM / SIGINT)、ログのレベルとカテゴリ (rt/log)、`/__/health`・`/__/ready`・`/__/metrics` (rt/ops、app/run。mulay.admin.port のポートだけで答える)、OTLP のメトリクス (app/otel)、OTLP のトレース (rt/trace、app/otel、ADR 116)。(未実装): JSON のログ出力 |
| セキュリティ | 500 応答から内部情報を削る、TLS の検証を既定で有効にする、SFTP のホスト鍵を検証する、secure-properties、パス走査の防止 |

作業の規律 (CLAUDE.md に書く): TDD、1 タスク 1 コミット、層を越える依存の禁止、「新しい IR ノードを足したら、読む・表示する・実行する段まで一緒に足す」
(計画では parse → resolve → eval → validate → muir。validate と muir の段は無いので、実際に触る場所は CLAUDE.md に書く)。

## 9. Clay 本体への依存と要望

mulay の中で書くもの (`mulay.lib.*`、stdlib に移せる品質で書く): dec、time、regex、xml、yaml、zip、unicode。

Clay 側に頼むもの (clay セッションと調整する)
1. mTLS (クライアント証明書の検証)。runtime の OpenSSL の設定に足す。
2. HTTP のストリーミング body (大きな payload のため)。
3. `clay.sql` の共通層の API を合意し、PostgreSQL の拡張クエリを実装する。
4. Int の加算・乗算で溢れを検知する組み込み (`add-overflow?` 相当)。数値の昇格に使う。
5. 見つけたコンパイラの不具合 (再現する最小コード付きで報告する)。

**版の固定**: Clay は API をよく改名する。`clay.pkg` で使う版を固定し、上げるときは明示的な作業として行う。
(未実装: `clay.pkg` は name と root だけで版を書いていない。版を上げるのは今もコミット単位の明示的な作業として行っている)

## 10. mulet から持ち込まない負債 (明示)

- 評価器が複数あり、評価器ごとに意味が違う。
- identityHashCode をキーにしたキャッシュ。
- ペイロードを即座に文字列化する。XML を再パースしない。
- 関数の名前空間が 1 つしかなく、import が効かない。
- セレクタが大文字小文字を区別しない (採るとしても、互換オプションとして明示する)。
- `and` / `or` が短絡評価されない。
- エラー型の照合が前方一致で行われ、`errorType.identifier` に namespace まで含まれる。
- propagate するときに元のメッセージが失われる。
- cron と timeZone が無視される。logger にレベルが無い。
- プロセッサの表をローカル名だけで引く。スキーマの解決が実行環境に依存する。
- ファイル・FTP・DB 用の、使われていない IR ノード。
- SFTP でホスト鍵を検証しない。

## 11. マイルストーン

**決定 (2026-09-28)**: 正しさの基準は実 Mule 4。v1 の範囲は P0 (M0〜M2 + 製品化)。汎用部品は mulay/lib に stdlib 品質で置く。
v1 = M0 + M1 + M2 + 運用最小限 (log、health、graceful shutdown) + 配布。M3 以降は v1.x / v2。


| M | 内容 | 完了条件 | 現状 (2026-10-14) |
|---|---|---|---|
| M0 基盤 | lib/{dec, time, regex, uni, xml, csv}、JSON の順序保持 reader/writer、Val | lib の単体テストが通る。ASan でリーク 0 | 済み |
| M1 DataWeave | パーサ、resolve、eval、Core/Strings/Arrays/Objects/Types、`mulay repl -i` | 抽出した golden の 80% 以上。実 Mule との差分は分類済み | 一部: golden は 3319/3319 (コミット d9a37ed の記録)、差分は docs/compat/deviations.md。`mulay repl` は (未実装) で、1 回の評価は `mulay dw` |
| M2 Mule コア | XML → IR、props、validator、engine、エラーモデル、P0 のスコープとルーター、HTTP の listener と request | `samples/hello-world`、`http-test`、`products-api` が実 Mule と同じ応答を返す | 済み: 3 本は test/fixtures/apps/ にあり、シナリオは全アプリで 92/92 (コミット 527ceb4 の記録)。validator は読み込みの診断と mule/lint。cache スコープは (未実装) |
| M3 P1 | DB (PostgreSQL、SQLite、Oracle thin)、File、OS、VM、scheduler (cron)、APIKit と OAS、DW の残りのモジュール、health、metrics、log、shutdown | `db-test-postgres`、`file-test`、`vm-test`、`objectstore-test` が通る。golden の 95% 以上 | 済み: アプリは db-pg (計画の db-test-postgres)、db-sqlite、db-oracle、file-test、vm-test、objectstore-test。APIKit は RAML も (conn/raml) |
| M4 P2 | SFTP、FTP、OAuth、Salesforce、Batch、MySQL、trace、Web UI の API、bundle、ホットリロード | 対応するサンプルと Exchange の例 18 本 | 一部: SFTP、Salesforce、Batch、MySQL は済み。OAuth は http:request の認証 (http-oauth)。bundle に当たるのは `mulay build`。FTP、trace、Web UI の API、ホットリロードは (未実装)。Exchange の例 18 本は未確認 |
| M5 P3 | MCP、A2A、gRPC、TUI の REPL | | 一部: MCP (サーバーとクライアント)、A2A は済み。gRPC と TUI の REPL は (未実装) |
| GA | ドキュメント、配布 (.deb、単一バイナリ)、ベンチマーク結果の公開 | | 一部: 単一バイナリ (`mulay build`) とコンテナ (deploy/ の Dockerfile、RTF 用) はある。.deb はリポジトリに無い。ベンチマーク結果の公開は未確認 |
