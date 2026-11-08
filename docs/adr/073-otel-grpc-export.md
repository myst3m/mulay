# 073 — OpenTelemetry のメトリクスの gRPC の送り出しは、実 Mule 4.12.0 (OTel Java SDK 1.60.1) の OkHttp の送り手に合わせる

状態: **採用** (2026-10-17)

## 決定
- `mule.openTelemetry.meter.exporter.type=GRPC` (既定) で OTLP/gRPC で送る。これまでは起動を拒んでいた。宛先の既定は
  `http://localhost:4317`。
- 要求:
  - 宛先のパスは無視し、scheme と host:port に `/opentelemetry.proto.collector.metrics.v1.MetricsService/Export` を付ける。
  - `http://` は h2c (事前の知識で HTTP/2)、`https://` は TLS で ALPN の h2。
  - ヘッダは `te: trailers`、`content-type: application/grpc`、gzip なら `grpc-encoding: gzip`、その後に設定の headers。
  - 本文は 5 バイトの枠 (圧縮の印、ビッグエンディアンの長さ) を付けた ExportMetricsServiceRequest。
- 応答:
  - `grpc-status` は trailer、無ければヘッダ (Trailers-Only)。どちらにも無いか数でなければ UNKNOWN (2)。
  - `grpc-message` はパーセント符号を戻す。
- 試し直し: 状態 1、4、8、10、11、14、15 と、接続の失敗で 5 回まで。待ちは HTTP と同じ。
- 諦めたときのログ (カテゴリ `io.opentelemetry.exporter.internal.grpc.GrpcExporter`):
  - 接続の失敗: ERROR `Failed to export metrics. The request could not be executed. Error message: <理由>`
  - UNAVAILABLE (14): ERROR `.. Server is UNAVAILABLE. Make sure your collector is running and reachable from this network. Full error message:<msg>`
    (コロンの後に空白が無いのは SDK のまま)
  - UNIMPLEMENTED (12): ERROR で長い案内の文言。プロセスで最初の 1 回だけ出し、2 回目からは何も出さない。
  - 他の状態: WARN `.. Server responded with gRPC status code <n>. Error message: <msg>`

## 理由
- 実 Mule 4.12.0 (`~/AnypointCodeBuilder/runtime/mule-enterprise-standalone-4.12.0`) を、`tools/otlp/otlp serve-grpc` の受け口に
  向けて記録した (2026-10-17)。
  - パス、ヘッダ (`te: trailers`、`content-type: application/grpc`、`user-agent: OTel-OTLP-Exporter-Java/1.60.1`、
    設定の headers、`accept-encoding: gzip`)、枠。
  - 状態 3、12、14 と、受け口を止めたときのログの段と文言。
  - 状態 14 で 1 回の送り出しにつき 5 回届いた (1 秒、1.5 秒 .. の間隔)。
  - 実 Mule は 5 秒ごとに 2 つの要求を送る。2 つ目は SDK 自身の計測 (`io.opentelemetry.*` の scope) で、mulay は送らない
    (docs/compat/deviations.md)。
- 宛先のパスの扱い、grpc-status の探し方、grpc-message のパーセント符号、試し直す状態の集合は、SDK 1.60.1 の
  `GrpcExporterBuilder` (endpoint.resolve)、`OkHttpGrpcSender` (`grpcStatus`、`grpcMessage`、`unescape`)、`RetryUtil` を
  javap で読んだもの。
- テストで守っているもの: 設定、URL、枠、ヘッダ、状態と文言の読み取り、試し直す状態、ログの段と文言 (test/rt/otel_test.clay)。
  テストで守っていないもの: UNIMPLEMENTED を 1 回だけ出すこと、接続の失敗で試し直すこと、h2c と ALPN の選び方。これらは
  手元の受け口で確かめた (https は https-test の証明書で ALPN が h2 になった)。

## 未確認の差
- OkHttp の送り手の `isRetryable` は応答の**ヘッダ**の grpc-status しか見ないように読める。trailer で返った状態 (普通の応答)
  なら、実 Mule は 14 でも試し直さない可能性がある。mulay はどちらでも試し直す。実 Mule では Trailers-Only の応答でしか
  確かめていない。
- 接続の失敗の理由の文言は clay のもの (`connect 127.0.0.1:4317: Connection refused`)。実 Mule は OkHttp の
  `Failed to connect to /127.0.0.1:4317` (docs/compat/deviations.md)。
- `user-agent` は送らない。
- SDK の ThrottlingLogger (同じ文言を 1 分に数回までに絞る) は真似ない。

## 場所
- `mulay.app.otel`: `configure`、`grpc-url`、`grpc-frame`、`grpc-headers`、`grpc-status-of`、`grpc-retryable?`、`grpc-failure`、
  `post-grpc`、`export-grpc`、`UNIMPLEMENTED-LOGGED`
- `tools/otlp/otlp` の `serve-grpc`
