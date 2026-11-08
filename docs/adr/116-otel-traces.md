# 116 — OpenTelemetry のトレース: 文脈はイベントが持ち、スパンは engine が作る

状態: **採用** (2026-11-02)

## 決定
- 実 Mule の `mule.openTelemetry.tracer.exporter.*` と同じ設定で、フローの実行をスパンにして OTLP (HTTP / gRPC) で送る。
  形 (名前、種類、親子、属性、状態、イベント、flags、受け渡し) は実 Mule 4.11.3 の記録に合わせる。
- トレースの文脈 (`ev/SpanCtx`: trace ID、今のスパン ID、sampled、tracestate、コネクタが書く置き場) はイベントの欄に持たせる。
  - 子のスパンは、そのときのイベントの文脈を親にして開き、中を動かすイベントの文脈を新しいスパンにし、閉じたら戻す
    (`with-frame` と同じ戻し方)。
  - 全体の「今のスパン」は持たない。要求は並行に走り、async と scatter-gather はスレッドをまたぐため。
- スパンは engine の決まった場所で開く。livenote の hook (`Hook`) は使わない。hook の before は Int を返し、中へ親を
  渡せないため。また hook の口は 1 つで、livenote が使っている。
  - `run-procs`: プロセッサごと。
  - `run-flow-ref` と `call-flow`: `mule:flow` / `mule:subflow`。
  - `handle-error-in`: ハンドラー。当たるものが無ければ位置 `unknown` の `mule:on-error-propagate`。
  - choice・foreach・scatter-gather・until-successful: route。otherwise の無い choice で当たる when が無ければ、route のスパンは
    出さない (実 Mule 4.11.3 で記録した。choice-none.case、2026-11-07)。
  - `run-flow-top` / `run-flow-done`: HTTP 以外のソースの根 `mule:flow`。
  - HTTP リスナーの根は app/run が作る。名前と属性、状態コードは HTTP の要求と応答から決まるため。
- コネクタは `tr/set-name!` と `tr/add-attr!` でスパンを変える。
  - 種類と状態の上書きは、実 Mule の HTTP コネクタと同じ属性の名前 (`span.kind.override`、`status.override`) で受け、
    閉じるときに属性から除く。
  - 根の状態は上書きが決める (SERVER は 500 だけ ERROR)。
  - 子はエラーが上書きより勝つ。client-500 の CLIENT は、上書き ERROR とエラーで "Exceptions have been recorded."。
- OVERVIEW では、コネクタの操作を仮のスパンで開く。
  - 種類が上書き (CLIENT など) されなければ送らない。
  - 仮のスパンの中の子は、上書きされていなければ 1 つ上を親にする。どのコネクタが CLIENT になるかは、操作が動くまで分からないため。
- エラーの `exception.stacktrace` はエラーのフロースタック (`MErr` の stack) を使う。実 Mule に合わせて次の 2 つを変える。
  - on-error-propagate が中のプロセッサを動かした後に伝えるエラーは、スタックを最後のプロセッサの位置にする。
  - until-successful が諦めた `MULE:RETRY_EXHAUSTED` は、スタックを until-successful の位置にする。
  - スタックはログの診断 (note: flow stack) にしか使っていないので、ほかの出力は変わらない。
- ID は OS の乱数 (`prim/random-bytes`、getrandom) で作る。clay の `rand-int` は起動ごとに同じ列になり、複数の mulay や
  再起動で trace ID がぶつかるため。
- 送り出しは app/otel のメトリクスと同じ道 (configure-at、export-http / export-grpc、試し直し) を使う。
  - 送る列は rt/trace の atom。
  - 100 ミリ秒ごとに見て、scheduledDelay が過ぎたか maxSize がたまれば maxSize ずつ送る。
  - トレースの設定は scheduler を動かす前に入れる。起動直後に動く scheduler のフローもトレースするため。

## 理由
- 実 Mule 4.11.3 と 4.12.0 を `tools/otlp/trace-oracle fill` で記録した (2026-11-02)。`otlp tree` の形では 2 つは同じで、
  違うのは SDK の版 (resource の `telemetry.sdk.version`) だけ。
- HTTP の SERVER と CLIENT の名前・属性・状態の規則は、HTTP コネクタ 1.11.3 の次のクラスを javap で読んだもの。
  - `HttpListenerCurrentSpanCustomizer`
  - `HttpRequestCurrentSpanCustomizer`
  - `HttpCurrentSpanCustomizer`
  - `HttpSpanUtils` (`updateServerSpanStatus` は `== 500`、`updateClientSpanStatus` は `>= 400`)
- CLIENT の `net.peer.name` と `net.peer.port` は送る先の url から取り、`http.url` にはクエリを入れない。
  `url` 属性で呼ぶとき、config の host と port (無ければ localhost と 80) ではない。実 Mule 4.11.3 で記録した (client-url.case、2026-11-03)。
- http:request は traceparent と、tracestate を (空でも) いつも付ける。アプリが headers に traceparent や tracestate を書いても
  置き換えず、アプリの値の後にランタイムの値を足す (同じ名前のヘッダーが 2 つになる)。受ける側の Mule は先の値を親にするので、
  アプリが書いた traceparent の trace につながる (スケジューラから始まったフローでも同じ)。実 Mule 4.11.3 で記録した (own-traceparent.case、2026-11-03)。
- Database コネクタの操作 (select、insert、update、delete、bulk-insert、query-single、execute-ddl) は、MONITORING では
  名前 `db:<操作>` の INTERNAL のスパンで、属性はほかのプロセッサと同じ (artifact.id、artifact.type、location) だけ。
  `db.system`、`db.statement`、`db.user`、`net.peer.name` などは付かず、CLIENT にもならない。SQL の失敗 (一意制約違反、
  無い列) は、そのスパンを ERROR ("Exceptions have been recorded.") にし、exception のイベント (型 DB:QUERY_EXECUTION) を付ける。
  OVERVIEW では DB の操作のスパンは出ない (種類を CLIENT に上書きしないため)。実 Mule 4.11.3 と 4.12.0 で記録して同じだった
  (db.case、db-overview.case、DB コネクタ 1.16.4、2026-11-03)。mulay は直さずに一致した。
- A2A コネクタ 1.1.1 (a2a.case、2026-11-07 に実 Mule 4.11.3 で記録):
  - task-listener のフローの根は SERVER ではなく `mule:flow` (INTERNAL)。受けた traceparent と tracestate を親にし、
    応答の状態コードを `http.status_code` に付け、500 なら ERROR にする。HTTP の属性 (http.method など) は付かない。
    実コネクタの `InboundSpanCustomizer` は SERVER と属性を書くが、記録には現れない。
  - task-stream-listener は traceparent を引き継がず、新しいトレースの根になる。
  - JSON-RPC を送る操作 (send-message など) のスパンは CLIENT で、属性は http.method (POST)、http.flavor、http.url
    (送り先の url をそのまま)、net.peer.name、net.peer.port。traceparent と tracestate を付ける。状態コードは付けない。
    send-message だけを記録した。ほかの操作 (send-stream-message、get-task など) は、実コネクタの `A2AClient` の
    `doRequest` と `doStreamRequest` がどれも `TracingUtils.traceOutboundRequest` と `propagateTraceContext` を通すことを
    javap で読んで同じにした。エージェントカードの取得 (GET) には付けていない (確かめていない)。
- traceparent と tracestate の扱いは記録 (propagation.case) と OTel Java SDK の W3CTraceContextPropagator の規則。
- 比率のサンプラーは SDK 1.60.1 の `TraceIdRatioBasedSampler` を読んだもの。
- UNIMPLEMENTED の文言の `OTEL_TRACES_EXPORTER` は `GrpcExporterUtil` を読んだもの。
- テストで守っているもの:
  - lib/tracectx (traceparent・tracestate・サンプラー)
  - lib/otlp (スパンのバイト列)
  - rt/trace (親子、flags、状態、仮のスパン、列の上限)
  - 実 Mule の記録との照合 11 場面 (monitoring、overview、propagation、sampler、sampler-zero、client-url、own-traceparent、db、
    db-overview、choice-none、a2a。ゲートの trace の段。db の 2 つは検査用の PostgreSQL (localhost:15432) を使う)
- テストで守っていないもの: gRPC での送り出し (メトリクスと同じ道)、送れなかったときのログ。後者は実 Mule 4.12.0 を閉じた
  ポートに向けて文言を確かめた。

## 未確認の差
- DEBUG の内部の段、parallel-foreach などの route、HTTP 以外のソースと、Database 以外のコネクタのスパンは記録していない
  (docs/compat/deviations.md、docs/todo.md)。
- 実 Mule の BAD (ID が不正な traceparent) は、新しい trace の根に flags 769 を付ける。mulay も同じにしたが、OTel の SDK の
  コードからは理由が読めていない (記録に合わせただけ)。

## 場所
- `mulay.lib.tracectx`: `parse-parent`、`parse-state`、`format-parent`、`sample?`、`new-trace-id`、`new-span-id`
- `mulay.lib.otlp`: `Span`、`SEvent`、`span`、`trace-request`
- `mulay.rt.event`: `SpanCtx`、`SpanMod`、`NO-SPAN`、`with-span`
- `mulay.rt.trace`: `start-root`、`start`、`start-provisional`、`finish`、`set-name!`、`add-attr!`、`traceparent`、`take-batch`
- `mulay.rt.engine`: `run-traced`、`in-span`、`route-span`、`flow-span`、`run-root`、`implicit-handler-span`、`restack`
- `mulay.app.run`: `server-span-attrs`、`end-server-span`
- `mulay.conn.http`: `trace-headers`、`client-span!`、`client-status!`
- `mulay.conn.a2a`: `client-trace`、`srv-answer`
- `mulay.app.otel`: `configure-tracer`、`start-tracer`、`shutdown-tracer`
- `tools/otlp/trace-oracle`、`test/fixtures/otel/traces/`、`test/fixtures/apps/otel-traces`、`test/fixtures/apps/otel-db`、`test/fixtures/apps/otel-a2a`
