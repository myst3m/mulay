# Mule ランタイムの設計

```
Mule XML ─(lib/xml)→ DOM ─(mule/parse。${..} は mule/props で解決、#[..] は DW にコンパイル)→ App (Mule IR、読み込みの診断 diags)
   ─(rt/engine)→ フロー実行  ← Sources (http listener, scheduler) が Event を作って流す
```

読み込み全体は mule/load がまとめる。`mulay validate` は読み込みの診断に加えて mule/lint の警告 (実 Mule が落とす書き方) を出す。
独立した検査の段 (mule/validate.clay) は未実装。

## 1. Mule IR (`mule/model.clay`)

- **パラメータ値 `PVal`**
  - `PLit(s)`: 文字列のまま
  - `PExpr(text, c: eng/Compiled, src: ExprSrc)`: `#[...]` の中身をロード時に DW としてコンパイルしたもの。
    ヘッダの無い式は `%dw 2.0\n---\n<式>` に包む (**output 指示子は付けない**。出力形式は実行時に推論する、§2.1)。
    `ExprSrc` はエラー文言のための出どころ (式の本文、スクリプト、式の開始位置、Trace の関数名) と、
    式が参照する入力の名前 (`uses`、字句で調べる。output の推論と payload の遅延 parse に使う)。
  - `${prop}` はロード時に解決するので、IR には残らない。**実行時に DW を parse することはない** (mulet の負債 D を解消)。
- **`Loc`** は file・line に加えて、実 Mule の component location (`flow/processors/1/route/0/processors/0`、
  `.../errorHandler/0/processors/0`) と要素を書き戻した XML (Element DSL) を持つ。既定のエラーログに出す。
- **プロセッサ `Proc`** は defvariant。mulet の `:ir/type` をそのまま移さず、実際に使われるものだけを持つ:
  - `set-payload`、`set-variable`、`remove-variable`、`logger` (message は文字列と式の部品に分ける)、`ee:transform` (message の payload / attributes と variables)、`flow-ref` (target、targetValue)、`raise-error`、`parse-template`
  - `choice`、`foreach`、`parallel-foreach`、`scatter-gather`、`try`、`until-successful`、`async`、`first-successful`、`round-robin`
  - `ee:cache` (`PrCache`)、`ee:invalidate-key`、`ee:invalidate-cache`、戦略は大域の `ee:object-store-caching-strategy` (Config のまま engine が名前で引く)
  - `idempotent-message-validator` (`PrIdempotent`。idExpression・valueExpression・objectStore・要素の中の `os:private-object-store`)
  - コネクタの操作 `PrConnectorOp {connector, op, config-ref, params: Vec(Param), children: Vec(xml/XNode) (汎用 XML 部分木), exprs, chains, target, target-value, loc}`
- **Source**: `http:listener` (`SrcHttpListener`)、`scheduler` (fixed-frequency / cron、`SrcScheduler`)、汎用のコネクタ Source (`SrcConnector`)。
- **App**: `{name, flows (sub-flow は Flow の sub が true), configs, global-handlers (大域のエラーハンドラ), default-handler, properties, prop-origins, diags, res, ...}`

## 2. Event と TypedValue (`rt/event.clay`)

```
TV    {val, mime, props, raw, state, stream}   ; TypedValue。state: RAW (未 parse) / VAL (値のみ) / BOTH / FAILED / CURSOR / DEFER / PIPE
Event {payload: TV, attributes: TV, vars: Vec(Var {name, tv}), error: Vec(MErr) (0 か 1 個), corr, flow, tx, frame, callers}
```

- **HTTP のボディ**は RAW で受け取る (Content-Type から mime を決める)。DW が最初に `payload` を読むときに `dw/fmt/registry` で parse し、その結果を持った Event を以後使う (遅延パース)。
- **transform の出力**は、output 指示子の形式でその場で書き出して RAW にし、値もあわせて持つ (BOTH)。
  - その場で書き出すのは、書き出しのエラー (例: Object を text/plain で書く) を Mule と同じくその transform で起こすため。
  - 次の DW は、書いた形式を読み直した値と等価なものを使う。JSON は往復で値が変わらないので値をそのまま使う。XML などは RAW を読み直す。
- **`application/java` の出力**は値のまま持つ (書き出さない)。
- **境界** (HTTP 応答、ファイル書き出し) では RAW を使う。RAW が無ければ: String と Binary はそのまま、
  null は空、それ以外は application/java なら **Java の直列化** (`rt/javaser`、実 Mule が送るバイト列と同じ。
  Object → LinkedHashMap、Array → ArrayList、整数 → Integer/Long、小数 → Double)、他の mime ならその形式で書き出す。

### 2.1 mime (DataType) と Content-Type

TV の `mime` (`(:mime tv)`) は Mule の DataType の media type を**パラメータ込み**で持ち、HTTP 応答の Content-Type はそれをそのまま使う。

| 値の出どころ | mime | Content-Type |
|---|---|---|
| mimeType の無い `set-payload value="文字列"` | `*/*` | 付けない |
| `mimeType="text/plain"` の文字列 (encoding なし) | `text/plain` (RAW) | `text/plain` |
| 同上で `encoding="ISO-8859-1"` | `text/plain; charset=ISO-8859-1` (そのバイト列) | 同じ |
| 式 + `mimeType` | `<mimeType>; charset=UTF-8` | 同じ |
| output 指示子のある DW | `<mime>; charset=UTF-8; <prop>="<値>"...` (`indent="false"` など) | 同じ |
| output の無い式で Java の値 | `application/java; charset=UTF-8` | 同じ (本文は Java の直列化) |
| HTTP 要求の本文 | 要求の Content-Type (charset が無ければ `; charset=UTF-8` を補う)、無ければ `*/*`。HTTP/2 で受けた要求は Content-Type に関係なく `*/*` (実 Mule 4.11.3、`http2-payload`) | — |
| 404 / 405 | — | `text/plain` (charset なし) |
| 捕まらなかったエラー | — | `text/plain; charset=UTF-8`、本文は error.description |

**output の無い式の出力形式の推論** (実 Mule の DW と同じ): 式が参照する入力の mime を集める。`payload` は
その mime (`*/*` と Java は application/java)、`vars.名前` はその変数自身の mime (JSON の payload から作った変数は
application/json、文字列リテラルや Java の値は application/java)、それ以外の入力 (attributes、error ...) と `p(..)` の
呼び出しは application/java (`core-infer-mix`。`p('x') ++ payload.id` は JSON の payload だと失敗する。
`#[output application/java --- ...]` で直る)。
1 種類ならその形式で書き出し (JSON の payload に `'x=' ++ payload.a` は JSON の文字列 `"x=.."`)、
2 種類以上なら `Unable to infer a output media type as more than one is being used: application/java,application/json ...`
で失敗する。本文が `payload` や `vars.x` そのものなら、その TypedValue を書き直さずに返す (logger に JSON の本文がそのまま出る)。
条件式・状態コード・flow-ref の名前など値だけが要る所 (`eval-val`) では推論しない。
推論は式の文字列ごとに最初の 1 回だけ (実 Mule はコンパイル結果を式の文字列で使い回す)。XML の payload で
`#[payload.^mimeType]` を評価した後は、別のフローで JSON の payload に同じ `#[payload.^mimeType]` を使っても
XML で書き出して失敗する (`core-infer`)。推論に失敗したときは覚えない。
位置の無い書き出しの失敗は `..., while writing CSV.\nTrace:\n  at main (Unknown)` の形になる。

mime の無いリテラルの文字列 (`set-payload value="x"`、`set-variable value="x"`) は Java の String で、DW で読むと
`^class` (java.lang.String)、`^encoding`、`^mediaType`、`^raw`、`^contentLength` が付く。`^mediaType` は payload が `*/*`、
変数が `*/*; charset=UTF-8` (`core-infer-mix` の class-of-literals)。

DW に渡す payload と変数には `mimeType` のメタデータを付ける (`payload.^mimeType`。実 Mule が DataType から付けるもの)。

## 3. エラー (`rt/error.clay`)

- `MErr {ns, id, description, detailed, payload, attrs (errorMessage), cause, also, elem, dsl, stack, logged, kids (childErrors)}`
- **ErrorType の親子関係**は Mule の定義表として持つ。コネクタの型は、そのコネクタの extension model から取る。例: `HTTP:NOT_FOUND` → `HTTP:CLIENT_SECURITY`? → `MULE:ANY`。**推測で作らず、実 Mule の extension model JSON から生成する** (tools/gen-error-types)。
- 照合は親をたどって行う。`type="A, B"` の複数指定と `when` 式にも対応する。
- `error.errorType.identifier` は `TEST` (`APP:TEST` の後半)、`namespace` は `APP`。
- **on-error-propagate** は元のエラーをそのまま再送出する (mulet はメッセージが失われていた)。
- **on-error-continue** は、ハンドラの結果の Event でフローを正常に終える。
- **DW のエラー**は `MULE:EXPRESSION` にする。description は実 Mule の形:
  `"<msg>\n\n<行>| <その行>\n<キャレット>\nTrace:\n  at <関数> (line: L, column: C)" evaluating expression: "<式>".`
  行・列は式の中で数える (transform はスクリプト全体)。関数は `anonymous::main`、logger の message と
  choice の when だけ `main`。span の無いエラー、reader / writer のエラー、Java への変換の失敗
  (`Unable to convert 'abc' with class 'java.lang.String' to class 'Integer', while writing Java at queryParams.s.`)
  は `"<msg>" evaluating expression: "<式>".` だけ。
- `raise-error` の description が無ければ `An error occurred.`。
- エラーは起きた要素 (`flow/processors/0 @ app:file.xml:12`) と Element DSL を持つ。既定のハンドラ
  (`DefaultExceptionListener`) と logException のハンドラは実 Mule の枠 (Message / Element / Element DSL /
  Error type / FlowStack) で ERROR を出す。
- until-successful を使い果たすと `MULE:RETRY_EXHAUSTED` (親は `MULE:CONNECTIVITY`。MuleErrors の enum では ANY の
  直下だが、実行時の型の表ではこう)。description は最後のエラーのもの、元の型 (`APP:ALWAYS`) のハンドラにも一致する
  (MErr の `:also`)。試行のたびに Event (変数を含む) は入る前に戻す。
- idempotent-message-validator (core-idempotent):
  - idExpression (既定 `#[correlationId]`) の値を文字列にし、店に無ければ valueExpression (既定 `#[correlationId]`) の値を入れて通す。
  - あれば `MULE:DUPLICATE_MESSAGE` (親は `MULE:VALIDATION`)。description と detailed はどちらも `unknown description`。
  - 入れるのは「無ければ入れる」の 1 回の操作 (rt/ostore の `put-new!`) なので、同時に来た同じ id は片方だけが通る。実 Mule も、contains の後の store が「既にある」で失敗すれば重複にする。
  - id が null か空白だけなら `MULE:UNKNOWN` の `key cannot be null or blank` (店の失敗の文言)。
  - objectStore を指せば、id がそのままその店のキーになる (os:retrieve で読める)。
  - 指さなければ validator ごとの私的な店。永続しない、TTL 5 分、掃除は 6 分ごと (IdempotentMessageValidator の createMessageIdStore)。
  - objectStore と `os:private-object-store` を両方書くと起動の誤り (`Ambiguous definition of object store, both reference and private were configured`)。
- Cache スコープ `ee:cache` (core-cache):
  - 戦略を指さなければ、スコープごとの私的な店で、鍵は payload の SHA-256 (同じ payload でも、別のスコープの結果は使わない)。
  - 戦略 (`ee:object-store-caching-strategy`) は名前で共有する。鍵は keyGenerationExpression。店は objectStore で指した店か、
    要素の中の `os:private-object-store`、どちらも無ければ entryTTL・maxEntries・expirationInterval (ミリ秒。既定 300000・4000・30000) の私的な店。
  - 当たれば中の処理は動かない。返すのは覚えた message (payload・mime・attributes) と、今の event の変数 (中で足した変数は戻らない)。
  - 外れれば中の処理を動かし、成功したときだけ、payload と attributes を実体にして (ストリームやカーソルを読み切って) 覚える。失敗は覚えない。
  - 鍵を作る前に payload を実体にし、その event で中の処理を動かす (HTTP の本文を鍵のために読んでも、中で読める)。
  - filterExpression が false なら、店を見ずに中の処理を動かす。
  - 同じ鍵の処理は排他する (synchronized の既定)。`ee:invalidate-key` は鍵 (keyGenerationExpression) の 1 件を、`ee:invalidate-cache` は戦略の店を全部消す。
  - 起動の誤り: keyGenerator-ref・responseGenerator-ref (Java の部品)、イベントのコピーの戦略、objectStore と `os:private-object-store` の両方。
  - 当たったときの速さ (2026-10-20、mulay 3cd9290。サーバーをコア 0-1、`wrk -t2 -c8` をコア 2-3、10 秒): 文字列を返す `/c2` は
    mulay 115,155 件/秒、実 Mule 22,683 件/秒 (5.1 倍)。http:request の応答 (JSON と attributes) を返す `/c11` は 67,138 と 15,668 (4.3 倍)。
- first-successful がすべて失敗したら最後のルートのエラー。scatter-gather の失敗は `MULE:COMPOSITE_ROUTING` で、
  description は `Error(s) were found for route(s):\n\tRoute 1: <例外クラス>: <description>`、
  `error.errorMessage.payload` は `{results: {"0": Message}, failures: {"1": Error}}`。
- foreach はエラーで止まるとその時点の Event (要素の payload、counter) のまま伝える。回せないもの (String、Binary)
  は `"Expecting Array or Object but got String." evaluating expression: "payload".`。
- choice の when: null は false、String は大小文字を問わず true/false、それ以外は Java の Boolean への変換の失敗。
- http:request の応答の検証: 既定は 0..399 が成功、`<http:success-status-code-validator values="200..499"/>` で変える。
- http:request の認証 (`<http:request-connection>` の `<http:authentication>`):
  - `http:basic-authentication` (username / password は式も可): preemptive (既定) は最初から `Authorization: Basic`。
    `preemptive="false"` は 401 の `WWW-Authenticate: Basic` を見てから送り直す。
  - `http:digest-authentication`: 実 Mule と同じく、最初に realm / nonce が "null" の仮の Authorization を送り、401 の
    Digest の挑戦 (qop=auth) に答える (cnonce は "null"、nc は 00000001、uri はパスだけ)。
  - `http:headers` に Authorization があれば、認証の Authorization は送らない。
  - ntlm-authentication は扱わない (要求が失敗する)。
  失敗の型は状態コードごと (HttpError にない 418 などは `MULE:UNKNOWN`、description は `failed with status code 418.`)。
  `<error-mapping sourceType targetType>` で付け替える。

## 4. 実行 (`rt/engine.clay`)

- `run-procs(c, ps, e) -> Values(Event Vec(MErr))` (エラーが無ければ空、あれば 1 個)。例外は無く、戻り値の流れで書く。
- **並行**: 1 リクエストを 1 つの green task で処理する (clay 0.88.0 の run-server。コアごとのキャリアが接続ごとの task を回す)。
  ハンドラの中で C の関数 (defextern) が止まると同じキャリアの接続が全部止まるので、長く止まりうる C の呼び出しは置かない
  (clay の client・sleep・future・sys/run は task を止める形。mulay の `system` は `mulay build` だけで使う)。
  - scatter-gather のルートと parallel-foreach の要素は、`future` (OS スレッド) の worker が 1 つずつ取って動かす。
    worker の数は maxConcurrency (無ければ全部)。結果は atom の表 (番号 → Done) で受け取り、番号順に読む。timeout を
    過ぎた仕事は MULE:TIMEOUT にする (動いている仕事は止めない)。`future` が本当に別スレッドで動くのは
    `-DCLAY_PARALLEL` のときだけなので、app/run.clay が `(c-flags "-DCLAY_PARALLEL")` を宣言する。
  - async は別スレッドで動かし (future-detach)、呼び出し側は待たない。maxConcurrency は async ごとの数えで制限する。
  - flow の maxConcurrency はフローごとの数えで制限する (超えた要求は空くまで待つ)。
  - round-robin の通し番号は Ctx の `:rr` の atom (要求をまたいで共有)。
- **deferred の出力** (DW の `output ... deferred=true`、rt/deferred、test/fixtures/apps/dw-deferred): 変換では評価せず、
  書き出したテキストの断片を出すストリーム (rt/stream) にして、payload は TypedValue の DEFER (ストリームの ID) にする。
  読めるのは 1 回だけ (DW で読む、境界で書き出す、logger に出す。2 回目は Pipe closed)。本体が `A map F` で出力が JSON なら
  1 要素ずつ評価して書き、A が streaming=true の JSON の payload なら要素も 1 つずつ読む。file:write と sftp:write は
  断片ごとに書く (出力全体を文字列にしない)。deferred でなくても、本体が `payload map F` で payload が streaming=true の
  JSON の配列なら、変換のときに同じ方法で 1 要素ずつ書いてテキストにする (入力と出力の値の木を作らない。途中で
  失敗したら全体を評価し直してエラーの文言を作る)。100 万件の JSON (232 MB) → map → 書き込み (2026-10-03、同じ負荷で交互に):
  ローカルのファイル 2.9〜3.7 s / RSS 0.25〜0.43 GB (実 Mule 4.0〜4.7 s / 1.06 GB)、SFTP 5.0〜6.1 s (実 Mule 6.2〜8.1 s)。
- **Batch** (`batch:job`、test/fixtures/apps/batch-basic): maxConcurrency が 2 以上か、入力が行のストリーム (DB の select、
  streaming=true の JSON 配列) なら、ブロックを maxConcurrency 本のスレッドで並行に流し、入力はブロックごとに取り出す
  (SFTP の 100 万件の JSON → 記録ごとの変換 → aggregator 5000 件の bulk-insert で Oracle へ: 11.8 s、RSS 0.9 GB。
  実 Mule は 113〜119 s、2.7 GB。2026-10-03)。batch:job は待たずに BatchJobInstance
  (ImmutableBatchJobInstance、status "EXECUTING") を payload にして続け、ジョブは別スレッド (future-detach) で動く。
  入力の配列の要素が記録 (payload と、ジョブを始めたときのフローの変数を持ち、ステップをまたいで引き継ぐ)。
  blockSize 件ずつのブロックごとにステップを順に通す。acceptPolicy (NO_FAILURES / ONLY_FAILURES / ALL) と
  acceptExpression (評価に失敗すれば記録は失敗)。ステップの処理が失敗すれば記録は失敗 (payload と変数はステップの前のまま)。
  aggregator は size 件ずつの配列を流し、残りはジョブの終わりに流す。maxFailedRecords (既定 0、-1 は無制限) を超えたら、
  そのブロックの後に止まる (既に始まっている次の 1 ブロックは流れるが数えない。実 Mule ではこれが競争で、全アプリを 1 つの JVM に載せたときは流れなかった。mulay は必ず流す)。on-complete の payload は
  BatchJobResult (ImmutableBatchJobResult: totalRecords、loadedRecords、processedRecords、successfulRecords、failedRecords、
  elapsedTimeInMillis ..、キーの並びは実 Mule を単独で動かしたときの並び。実 Mule の bean のプロパティの並びは同じ JVM に載っているものによって変わるので、batch-basic は並べてから比べる)。batchStepResults はステップの名前 → BatchStepResult
  (HashMap の順。receivedRecords はステップに来たすべての記録、failedRecords はそのステップでの失敗、
  errorSummary.errorsCount はエラーの型ごとの数)。
- **flow-ref**: 名前で flow / sub-flow を引く。flow には、その flow の error-handler を適用する。
- **initialState="stopped"** (値は `${..}` でもよい。test/fixtures/apps/core-initial-state): そのフローのソース (http:listener、
  scheduler、コネクタの listener) は始めない。listener の path は登録されず 404 (`No listener for endpoint: ..`)、同じ path を
  動いているフローが持ってもよい。止まったフローへの flow-ref は `MULE:UNKNOWN` (`Cannot process event as "<名前>" is stopped`)。
- **ログ**: 既定の log4j2 と同じく、root は WARN、`org.mule.*` (logger の既定カテゴリ LoggerMessageProcessor を含む) は
  INFO。独自のカテゴリの INFO は出ない。stdout は 1 行ごとに flush する。
  - message の値: RAW/BOTH (JSON などに書き出したもの) はそのバイト列、Java の値は Java の toString
    (`{a=1, b=[x, y]}`、null は `null`)。`a #[x] b` の埋め込みは部品ごとに評価してつなぐ。
  - message が無いときは Message の toString (HttpRequestAttributes の形を含む)。

## 5. HTTP

- **listener**: `clay.http/run-server` の上で動かす。listener-config (ポート) ごとに run-server を別スレッドで回す。
  要求を受けたポートは run-server の `local-port` (clay 0.51.2) で分かるので、経路表はそのポートのものを使う。
  - listener-config (host, port, basePath) の path パターン (`/{id}`、`/*`) で flow を選ぶ。
  - 要求に `X-Correlation-ID` があれば、その値をフローの correlationId にする (無ければ mulay が作る。core-http-request の /cid/echo)。
  - 存在しない listener-config を参照する http:listener は、実 Mule の配備の検査と同じく
    `[<file>:<line>]: Referenced component '<名前>' must be one of stereotypes [HTTP:LISTENER_CONFIG].` で起動を拒む。
    起動を拒む理由は全部、1 行ずつ出す (実 Mule と同じ。以前は最初の 1 件だけを出していた)。
  - `attributes` は Mule の HttpRequestAttributes と同じ形 (method, requestPath, queryParams, uriParams, headers, ...) にする。
  - 応答は `http:response` (statusCode、headers、body) と `http:error-response` の規則に従う。
  - `attributes`: requestUri・requestPath・queryString はデコードした形、rawRequestUri・rawRequestPath は受け取ったまま。
    queryParams は同じキーの値がまとまる (MultiMap)。statusCode は Integer に変換する (`'abc'` は変換エラー、200 未満は
    `java.lang.IllegalArgumentException: Cannot send a status code lower than 200`)。204/304 は本文を落とす。
    http:headers の値に Array / Object は不可。
  - 経路が無いときの 404 `No listener for endpoint: <パス>` と、method が許されないときの 405
    `Method not allowed for endpoint: <パス>` は、経路はデコードしたパスで選び、文言には受け取ったままのパス (クエリを除く) を
    escapeHtml4 して出す (`PUT /method%73` は `/methods` の経路に当たり、文言は `/method%73`。`&` は `&amp;`。ADR 074)。
  - 要求の対象が `java.net.URI` として読めなければ (壊れた `%`、パスやクエリに使えない `{` `|` など) 経路を選ぶ前に 400
    `HTTP request parsing failed with error: "Malformed escape pair at index 26: http://0.0.0.0:18120/nope/%zz"` を返して接続を閉じる (ADR 074)。
  - 応答のヘッダは `Vec(hm/Header)` で任意に送れる。remoteAddress は run-server の `remote-addr` から取る。
- **request**: `clay.http/request` を使う (実 Mule と同じ順で `User-Agent: Mule HTTP Client`、利用者のヘッダ、X-Correlation-ID、
  Content-Type .. を付ける。followRedirects は操作か設定で決め、既定は辿る (5 回まで))。responseTimeout は `timeout-ms` に渡し、超えたら `HTTP:TIMEOUT`。config (host、port、basePath、protocol、TLS)、path、method、query-params、headers、uri-params、responseValidator (既定では 0..399 以外がエラーになり (§3)、エラー型は HTTP:NOT_FOUND など)、responseTimeout に対応する。
  - X-Correlation-ID は `sendCorrelationId` (操作に書けばそれ、無ければ request-config のもの、既定 AUTO) が NEVER なら送らず、
    操作の `correlationId` (式) があればその値を送る (操作に AUTO と書くと設定が NEVER でも送る。core-http-request の /cid/*)。
  - 本文を送るかは `sendBodyMode` (操作、無ければ request-config、既定 AUTO) で決める。AUTO は GET・HEAD・OPTIONS で送らず、
    ALWAYS はどの method でも送り、NEVER は送らない。本文を送らない GET・HEAD・OPTIONS には Content-Length を付けず、
    ほかの method には `Content-Length: 0` を付ける。
  - 本文の送り方は `requestStreamingMode` (同じく既定 AUTO)。長さの分からないストリーム (DW の出力、ファイルの読み込み、
    `streamResponse="true"` の HTTP の応答、Anypoint MQ のメッセージ。`ev/TV` の stream) をそのまま送るとき (本文の指定が無いか、
    `#[payload]`・`#[vars.x]` だけのとき。`en/identity-expr?`) は、NEVER を除いて空でも `Transfer-Encoding: chunked` で送る。
    `<http:body>` のほかの式の結果は、output 指定があっても長さの分かる値として Content-Length で送る。listener で受けた本文と
    ふつうの HTTP の応答も長さが分かっているので Content-Length。ストリームでない本文は ALWAYS で中身があるときだけ chunked。
    Content-Type は、本文が空で chunked でもなければ付けない (core-http-request の /body/*、/stream/*、file-ops の /fwd/file)。

## 6. 検証

- アプリのシナリオ: `test/fixtures/apps/<name>/` に Mule プロジェクトと `scenario.scn` (リクエストと期待レスポンス。形式は docs/fixtures.md) を置く。
- 期待値は実 Mule (4.11.3) でアプリを動かして記録する (`tools/mule-oracle`)。
- 手始めは mulet の `samples/` (mulet から `test/fixtures/mulet-samples` に移した。hello-world、http-test、products-api など。test/fixtures/apps に同じ名前のアプリがある)。

## 7. コネクタ

- `http` (conn/http): request。listener は app/run が扱う。
- `os` (conn/os): ObjectStore (store / retrieve / contains / remove / clear / retrieve-all /
  retrieve-all-keys)。objectStore 属性で店を分ける。値は TypedValue のまま持つ (retrieve-all の値は、バイト列で
  しまったものはその文字列)。`<os:object-store>` の entryTtl・maxEntries・expirationInterval に対応し、persistent の店
  (既定の店を含む) は rt/persist のファイルに書いて再起動をまたぐ。
- ほかのコネクタは src/mulay/conn/ の各ファイル (db、file、sftp、vm、salesforce、anypoint_mq、apikit、wsc、a2a、mcp など)。
  rt はコネクタを直接知らず、conn/registry の登録表を通す。

## 8. 運用 (`rt/ops.clay`、`app/run.clay`。mulay 独自で、実 Mule には無い)

- 状態は STARTING → READY (listener とソースを始めた後) → DRAINING (終了のシグナルを受けた後)。
- 端点は `mulay.admin.port=<ポート>` を指定したときだけ専用のポートを開いて答える。アプリの HTTP の listener では、
  指定の有無にかかわらず `/__/` もアプリの経路 (認証の無い計測を外に出す listener に見せず、アプリの `/__/` を隠さない。
  2026-10-25 までは、admin のポートが無ければアプリの listener の各ポートで答えていた):
  - `GET /__/health`: `{"status": "healthy" | "degraded" | "unhealthy", "uptime": 秒, "checks": {"memory": "ok" | "warning" | "critical"}}`
    (mulet と同じ形)。memory はコンテナ (cgroup v2) の上限に対する使用量 (80% で warning、90% で critical)。
    unhealthy、起動中、停止中は 503 (`{"status":"unhealthy","reason":"starting"|"stopping",..}`)。
  - `GET /__/ready`: READY なら 200 "ready"、それ以外は 503。
  - `GET /__/metrics`: Prometheus のテキスト。`?format=json` なら JSON。プロセス (`process_cpu_seconds_total`、
    `process_resident_memory_bytes`、`process_open_fds`、`process_threads`、`process_start_time_seconds`)、コンテナの
    メモリ、処理中の要求の数、フローごとの `mulay_flow_requests_total`、`mulay_flow_errors_total{type=..}`
    (フローがエラーで終わった回数。on-error-continue で扱ったものは数えない)、`mulay_flow_duration_seconds` (histogram)。
    フローは、ソース (HTTP の listener、scheduler、コネクタのソース) から始まったものを数える (flow-ref は数えない)。
  - それ以外の `/__/` は 404。
  - `GET /mule/healthcheck/applications/<名前>/ready` (`mulay.admin.port` のポートだけ。RTF = Runtime Fabric の
    準備完了の問い合わせ): RTF の Pod で答える Mule エージェント (mule-agent-web-interface 2.7.13 の HealthCheckRequestHandler、
    poseidon-runtime 4.11.4 のイメージから読んだ) と同じ形。READY は 200 で本文も Content-Type も無い、起動中は 409 text/plain の
    `Not ready. Status: CREATED`、名前が違えば 404 で本文が空。止めるとき (SIGTERM) は admin のポートも止めるので、
    開いたままの接続には 409 `Not ready. Status: STOPPED`、新しい接続は断る (処理中の要求が無ければ、すぐ終わる)。名前は `mulay.health.app` (既定はアプリの名前。RTF の `APP_NAME` は
    jar の中の名前と違うことがあるので、RTF では明示する)。READY は listener を開く直前に立てる (listener が開いたことの確認ではない。数ミリ秒の差)。
    実 Mule の状態は CREATED → INITIALISED → STARTED と進むが、mulay は起動中を区別しないので CREATED だけを返す。
  - RTF の Pod の起動 (`deploy/rtf/docker-entrypoint.sh`) は、設定のプロパティ (Secret から読んだ安全なプロパティの値を含む) を
    コマンドラインに載せず (`ps` で誰にでも見える)、`/tmp/mulay/app.props` (権限 600) に NUL 区切りで書いて `mulay run -P` で渡す。
- graceful shutdown: SIGTERM か SIGINT を受けると DRAINING にし (scheduler は流さない)、HTTP の listener と admin の
  ポートを止める (clay の http/stop: 新しい接続は断り、処理中の応答は書き終え、idle の keep-alive は閉じる。止める間の
  応答には `Connection: close` が付く。止める間に既存の接続で届いた要求と health / ready は 503)。処理中の要求が 0 に
  なるか `mulay.shutdown.timeout` (ミリ秒、既定 5000) が過ぎたら終える (終了コード 0。残った接続は切る)。
- 大きな要求の本文 (HTTP/1.1 と HTTP/2) は流して受け、512 KB を超えた分は `mulay.work.dir/<アプリ>/spool` に逃がす (ADR 104)。
  `mulay.http.maxRequestBody` (バイト、既定 0 = 上限なし) を超えると 413。
  流して受ける要求でも、経路が無いか method が合わなければ、本文を読まずに 404 / 405 で答える (HTTP/1.1 は接続を閉じる。ADR 118)。
  本文をディスクに溜める間、spool の置き場のファイルシステムの空きが `mulay.http.spoolMinFree` (バイト。既定はファイルシステムの 10% と
  1 GiB の小さいほう、0 で調べない) を下回れば、503 "Not enough free disk space to receive the request body (mulay.http.spoolMinFree)" で
  接続を閉じ、溜めた分を消す (ADR 118)。
  シグナルは起動時に全スレッドで止め (clay.sys の block-signals)、専用のスレッドの wait-signal で受ける。

### OpenTelemetry のメトリクス (`app/otel.clay`、`rt/meter.clay`、`lib/otlp.clay`)

実 Mule 4.12 の `mule.openTelemetry.meter.exporter.*` と同じ設定で、Mule のメトリクスを OTLP で決まった間隔で送る
(`mulay run <app> mule.openTelemetry.meter.exporter.enabled=true mule.openTelemetry.meter.exporter.type=HTTP ..`)。
メトリクスは実 Mule 4.12 から (公式ドキュメント mule-runtime/latest/otel-support)。4.11.3 にも同じ設定の名前はあるが、
隠れた `mule.open.telemetry.metric.exporter=true` が要り、scope の名前も違う試作なので、4.12.0 に合わせた。

- 設定: `enabled` (既定 false)、`type` (GRPC が既定、HTTP)、`endpoint` (GRPC の既定 `http://localhost:4317`、HTTP の既定
  `http://localhost:4318/v1/metrics`。HTTP はそのまま POST)、
  `headers` (`名前=値,..`)、`compression` (none / gzip)、`timeout` (ミリ秒、既定 10000)、`interval` (秒、既定 60)、
  `resource.attributes` (`名前=値,..`)、`resource.service.name` / `resource.service.namespace` (既定はアプリの名前と `mule`。
  `mule.openTelemetry.exporter.resource.*` でもよい)、`tls.enabled` と `tls.caFileLocation` / `tls.certFileLocation` / `tls.keyFileLocation` (PEM)。
  設定の誤り (type の綴り、http でない endpoint、0 以下の interval など) は起動時に理由を言って終える (終了コード 1)。
- **type=GRPC** (OTLP/gRPC): 宛先の scheme と host:port に `/opentelemetry.proto.collector.metrics.v1.MetricsService/Export` を
  付けて送る (宛先のパスは SDK と同じく無視する)。`http://` なら h2c (平文の HTTP/2)、`https://` なら TLS と ALPN の h2。
  本文は 5 バイトの枠 (圧縮の印と長さ) を付けた protobuf で、`te: trailers`、`content-type: application/grpc`、gzip なら
  `grpc-encoding: gzip`。結果は trailer の `grpc-status` (無ければヘッダ、どちらにも無ければ UNKNOWN の 2) と `grpc-message`
  (パーセント符号を戻す)。
- 送るもの (scope、名前、説明は実 Mule 4.12.0 と同じ。どれも整数の累積の Sum):
  - `org.mule.runtime.errors` の `error-count` (`mule.artifact.id`、`mule.error.type`)。エラー 1 つにつき 1 回 (on-error-propagate で
    外側のハンドラまで伝わっても 1 回)。エラーがまだ無ければ scope ごと出さない。
  - `org.mule.runtime.flow.statistics` のフローの数 (`declared-` / `active-` の `trigger-flows`、`private-flows`、`apikit-flows` と、
    同じ値の `-v2`)。trigger は source のあるフロー、apikit は名前が `method:\resource:config` で config が apikit:config のもの、
    private はそれ以外 (sub-flow は数えない)。`initialState="stopped"` は declared だけ。
  - 同じ scope のフローごとの `received.events` (フローに入るたび。flow-ref で呼ばれたフローも)、`dispatched.messages` と
    `dispatched.primary.messages` (source から来た 1 件ごと)、`execution.errors` (フローのエラーハンドラ (既定も) が受けたとき。
    try の中で扱ったものは数えない)、`fatal.errors` (いつも 0)。属性は `mule.artifact.id` と `mule.flow.name`。
    **これらは `mule.enable.statistics=true` のときだけ数える** (実 Mule と同じ。無ければ 0 のまま送る)。
- `jvmMetrics.enabled=true` なら、JVM のメトリクスのうち mulay のプロセスの値に付け替えられるものも送る (scope
  `io.opentelemetry.runtime-telemetry`、resource は `service.name=mule-container`。`mule.openTelemetry.exporter.resource.container.service.name`
  / `.namespace` で変えられる): `jvm.cpu.count`、`jvm.cpu.time`、`jvm.cpu.recent_utilization`、`jvm.memory.used` / `committed`
  (heap = 匿名のメモリ、non_heap = ファイルに載ったメモリ)、`jvm.memory.limit` (cgroup の上限があるとき)、`jvm.thread.count`。
  名前、説明、単位、種類は実 Mule 4.12.0 と同じ (`test/fixtures/otel/jvm-metrics.mule-4.12.0.*`)。GC とクラスのものは送らない。
- resource: `service.name`、`service.namespace`、`service.instance.id` (起動ごとの UUID)、`telemetry.sdk.name=mulay`、
  `telemetry.sdk.language=clay`、`resource.attributes` の分。
- 送れなければ OTel の SDK と同じく、HTTP は 429、502、503、504、gRPC は状態 1、4、8、10、11、14、15 と、接続の失敗で 5 回まで
  試す (待ちは 1 秒から 1.5 倍、上限 5 秒、その間の乱数)。諦めたら `io.opentelemetry.exporter.internal.http.HttpExporter`
  (gRPC は `..grpc.GrpcExporter`) のカテゴリで出す (文言も SDK と同じ)。段は実 Mule 4.12.0 で確かめた: 接続の失敗は ERROR、
  HTTP の状態は WARN (Error message は応答の本文を google.rpc.Status として読んだ message、読めなければ
  `Unable to parse response body, HTTP status message: <理由句>`)、gRPC の UNAVAILABLE (14) は ERROR、UNIMPLEMENTED (12) は
  ERROR で最初の 1 回だけ、他の状態は WARN。
- SIGTERM で止めるときに最後に 1 回送る (実 Mule もアプリを止めるときに送る)。止めるのを待たせないよう、このときは試し直さない。
- 送る設定が無ければ何も数えない (フローに入るたびとエラーのたびに atom を 1 つ読むだけ)。
- 実 Mule と比べる道具: `tools/otlp/otlp` (`serve` と `serve-grpc` で受けて保存、`decode`、`norm`)。実 Mule 4.12.0 の記録は
  `test/fixtures/otel/otel-metrics.mule-4.12.0.*` (アプリは `test/fixtures/apps/otel-metrics`)。

### OpenTelemetry のトレース (`rt/trace.clay`、`app/otel.clay`、`lib/tracectx.clay`。ADR 116)

実 Mule (4.11 から) の `mule.openTelemetry.tracer.exporter.*` と同じ設定で、フローの実行をスパンにして OTLP で送る
(`mulay run <app> mule.openTelemetry.tracer.exporter.enabled=true mule.openTelemetry.tracer.exporter.type=HTTP ..`)。
形は実 Mule 4.11.3 の記録と同じ (4.12.0 でも同じ。`test/fixtures/otel/traces/*.expected`、照合は `tools/otlp/trace-oracle check`、ゲートに入っている)。

- 設定: `enabled`、`type` (GRPC が既定、HTTP)、`endpoint` (GRPC の既定 `http://localhost:4317`、HTTP の既定
  `http://localhost:4318/v1/traces`)、`headers`、`compression`、`timeout`、`tls.*`、`resource.*` (メトリクスと同じ。
  `mule.openTelemetry.exporter.resource.*` でもよい)、`sampler.type` (既定 `parentbased_traceidratio`。`always_on`、`always_off`、
  `traceidratio`、`parentbased_always_on`、`parentbased_always_off`)、`sampler.arg` (比率、既定 0.1)、`batch.scheduledDelay`
  (ミリ秒、既定 5000)、`batch.maxSize` (既定 512)、`batch.queueSize` (既定 2048。あふれたスパンは捨てる)。
  レベルは `mule.openTelemetry.tracer.level` (`OVERVIEW`、`MONITORING` が既定、`DEBUG`)。設定の誤りは起動時に理由を言って終える。
- スパン (scope は `mule` 版 `1.0.0`):
  - 根: HTTP リスナーのフローは SERVER の `<METHOD> <basePath + path>` (`http.method`、`http.flavor`、`http.route` と `http.target`
    は path の型、`http.scheme`、`http.user_agent` (ヘッダーがあるとき)、`net.host.name` (listener-config の host。`localhost` は
    `127.0.0.1`)、`net.host.port`、`http.status_code`)。状態は状態コードがちょうど 500 のときだけ ERROR、ほかは UNSET
    (HTTP コネクタの `HttpSpanUtils.updateServerSpanStatus` と同じ)。scheduler とほかのソースのフローは INTERNAL の `mule:flow`。
  - MONITORING: プロセッサごとに `<ns>:<名前>` (`mule:logger`、`ee:transform`、`mule:flow-ref` ..)。flow-ref の先は `mule:flow` か
    `mule:subflow` (location はフローの名前)。route は `mule:choice:route`、`mule:foreach:iteration`、`mule:scatter-gather:route`、
    `mule:until-successful:attempt` (location は外の要素の場所)。エラーハンドラーは `mule:on-error-continue` /
    `mule:on-error-propagate` (location は `<..>/errorHandler/N`、どれにも当たらなければ `unknown`)。
  - OVERVIEW: 根、`mule:flow`、`mule:subflow` と、CLIENT になったコネクタの操作だけ。DEBUG は MONITORING と同じ
    (docs/compat/deviations.md)。
  - http:request は CLIENT の `<METHOD>` (`http.method`、`http.flavor`、`http.url`、`net.peer.name`、`net.peer.port`、
    応答があれば `http.status_code`)。状態コードが 400 以上なら ERROR。要求に `traceparent` (このスパン) と、
    受けた tracestate があれば `tracestate` を付ける。
  - どのスパンも `artifact.id`、`artifact.type` (`app`)、`location`、`correlation.id`、`thread.start.id`、`thread.start.name`、
    `thread.end.name` を持つ。エラーで終わったスパンは ERROR と `Exceptions have been recorded.`、`exception` のイベント
    (`exception.type`、`exception.message`、`exception.stacktrace` (フロースタック)、`exception.escaped`)。
- 受け渡し (W3C Trace Context): 受けた `traceparent` が正しければ同じ trace の子になり (flags 769)、tracestate を全スパンに
  引き継ぐ。形の崩れた値は無いのと同じ (flags 257)、形は合うが ID が不正 (大文字、全 0) なら新しい trace で flags 769。
  サンプラーが送らないと決めたトレースもスパンの ID は持ち、`-00` の traceparent を渡す。
- 送り出しは 5 秒ごと (または maxSize がたまったとき) に maxSize ずつ。送れなければメトリクスと同じ規則で試し直し、
  諦めたら SDK の文言 (`Failed to export spans. ..`) と `Batch span export failed.` (WARN、
  `org.mule.runtime.tracer.exporter.impl.export.batch.BlockingBatchSpanProcessor$Worker`)。SIGTERM で止めるときに残りを送る。
- 送る設定が無ければ、プロセッサごとに文字列が空かを 1 回見るだけ。

### Anypoint Monitoring のメトリクスのファイル (`app/ammetric.clay`)

RTF の Pod では、実 Mule の監視のエージェントが `/opt/mule/logs/_metric.log` に 1 分ごとに JSON を 1 行ずつ書き、
同じ Pod のサイドカー (`anypoint-monitoring`、中身は OTel Collector) がそれを読んで Anypoint (`/api/v2/lmetrics`) へ送る。
Anypoint Insights の要求数と応答時間 (`mulesoft.app.inbound`) はここから来る (OTLP の口は、この組織では Anypoint が 400 で断った)。
mulay は `mulay.am.metricFile=<パス>` があれば、そのうち `app_inbound_metric` を同じ形で書く
(`deploy/rtf/docker-entrypoint.sh` が `/mnt/overlay/opt/mule/logs/_metric.log` を渡す。空を渡せば書かない)。

- 数えるもの: HTTP リスナーのフローに届いた要求 1 件ごとの応答時間 (ミリ秒、切り捨て)。どのリスナーにも当たらない要求
  (404、405)、a2a・MCP・OAuth の口、運用の端点は数えない。フローがエラーで終わったら `FAILED` (状態コードによらない。
  on-error-continue で扱ったものは `OK`)。
- 1 分の窓で、保つ次元 (`flow_id`、`endpoint_type`=http、`response_type`、`protocol`、`host_header`) の組ごとに、`remote_host`
  (アドレスだけ) と `endpoint` の組を届いた順に 5 つまで。6 つ目からの新しい組は `endpoint` を `other` にまとめる。
- `endpoint` はデコードしたパス (クエリを除く) の区切りのうち、文字・`-`・`_` 以外を含むもの、全部が大文字のもの
  (最初の区切りは除く) を `X` にしたもの。listener-config の `basePath` までは残す。
- 行の形 (キーの順、件数・合計・最小・最大・二乗和、平均の切り捨て、`metadata`) は実 Mule 4.12.0 の行と同じ
  (`test/fixtures/am/`、hello-world の行とバイト単位で一致)。`commons` は RTF が置く環境変数 `ORG_ID`、`ENV_ID`、`APP_NAME`、
  `POD_NAME`、`NODE_NAME` から。
- 時計の分の境目ごとに前の 1 分を書く (`time` は窓の始まり)。要求の無かった窓は書かない。起動時に空のファイルを作る
  (サイドカーは途中から読み始めるため)。SIGTERM で止めるときに残りを書く。10 MB を超えたら `<file>.1` に移す。
- 書く設定が無ければ何もしない (要求ごとに atom を 1 つ読むだけ)。
