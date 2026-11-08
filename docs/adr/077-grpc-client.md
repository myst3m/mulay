# 077 — gRPC のクライアント (grpc:unary-call) は h2c で送り、結果は TypedValue に包んだ protobuf にする

状態: **採用** (2026-10-18)

## 決定
- `<grpc:client-config>` の `<grpc:no-auth-connection host port>` から、`stub.S/Echo` の形のメソッドを HTTP/2 の POST で呼ぶ。
  - 平文 (`<grpc:connection-mode><grpc:plain-text/>`) は h2c の prior knowledge (`clay.http` の `:h2c`)。
  - connection-mode を書かなければ TLS (実コネクタの既定)。https の h2 は clay の ALPN に任せる (照合していない)。
- 送るヘッダは実 Mule と同じ: `content-type: application/grpc`、`te: trailers`、`user-agent: Mule HTTP Client`、`accept: */*`、
  接続と操作の `request-headers` (名前は小文字)。`grpc-timeout` と `grpc-accept-encoding` は送らない。
  - 実コネクタは grpc-java ではなく Mule の HTTP クライアントの上で動く (user-agent と accept で分かる)。
- 送る本文は content (既定は payload) のバイト列をそのまま 5 バイトの枠に入れる。protobuf かどうかは見ない (JSON や
  `'abc' as Binary` もそのまま送る)。
- 応答の読み方 (`mulay.conn.grpc/read-reply`、純粋な関数):
  - grpc-status は trailer から、無ければ最初の HEADERS から (Trailers-Only) 読む。どちらにも無ければ成功 (実 Mule も成功)。
  - 0 から 16 でない番号は UNKNOWN、文言は `Unknown code <値>`。
  - grpc-message はパーセント符号化を戻す。無ければ文言は `No description`。
  - メッセージが 2 つ以上あれば最初のもの。
  - 失敗のエラー型は `GRPC:<status の名前>` (UNKNOWN だけ `GRPC:GRPC_UNKNOWN`)。説明は
    `gRPC operation 'UNARY' failed with status <名前>: <文言>\nMethod: <メソッド>`。
  - 接続できなければ UNAVAILABLE で `Connection refused: Connection refused: localhost/127.0.0.1:<port>`。
  - メソッドが記述子に無ければ、実コネクタの NullPointerException の文言で `MULE:UNKNOWN`。
- 実 Mule が応答を返さずに止まる形は、mulay が決める (docs/compat/deviations.md):
  - 枠の壊れた本文は INTERNAL `Received a truncated gRPC message`。
  - メッセージ無しの成功は INTERNAL `No value received for unary call` (grpc-java の文言)。
  - grpc-status の無い 200 以外の HTTP 応答は、gRPC の HTTP の状態コードの対応表で決める
    (400 INTERNAL、401 UNAUTHENTICATED、403 PERMISSION_DENIED、404 UNIMPLEMENTED、429・502・503・504 UNAVAILABLE、
    他は UNKNOWN)。文言は `HTTP status code <n>`。
  - 圧縮の旗が立ったメッセージは INTERNAL (mulay は grpc-accept-encoding を送らないので、来ないはず)。
- 結果の payload は TV の新しい状態 `ev/TYPED` (`ev/tv-typed`) で持つ。外向きは Java の TypedValue で、中身は
  `application/x-protobuf; descriptorUrl=..; messageType=<出力の型>` のバイト列。
  - mime は `*/*; charset=UTF-8`、`^class` は `org.mule.runtime.api.metadata.TypedValue`。`^raw` は空のバイト列を
    中の mime で読んだもの (実 Mule ではストリームを読み終えているので、出力の型の既定のメッセージになる)。
  - DW で読むときだけ中の mime で読む。読めなければ、その式の失敗になる (操作は成功している)。
  - 直列化できない: listener の応答にすると 500 `Could not serialize object`。別の unary-call の content にすると
    `MULE:TRANSFORMATION` (`_ObjectToInputStream` の文言)。
  - 中の mime は TV の props の `mediaType` に置く。set-payload の mimeType で mime を変えても props は残す。
  - attributes は null。

## 理由
- 実 Mule 4.11.3 + mule-grpc-connector 1.0.4 で test/fixtures/apps/grpc-client を記録した (2026-10-18)。相手は
  mule-oracle の gRPC のスタブ (`%%% grpcserver`) で、成功・失敗・Trailers-Only・trailer 無し・範囲外の番号・2 つの
  メッセージ・protobuf として読めない本文・ヘッダの送り方を確かめた。
- 結果を protobuf の TV (mime を application/x-protobuf) にすると、`^mediaType`、listener の応答、次の unary-call への
  受け渡しが実 Mule と変わる。中の値だけ protobuf として遅延して読む別の状態にした。
- 実 Mule が止まる形は記録できないので、gRPC の仕様と grpc-java の文言に寄せた。単体テストは test/grpc。

## 残した差
- TLS (connection-mode の tls と tlsContext)、oauth-client-credentials と Google のサービスアカウントの接続、Deadline と
  responseWaitTime、ストリーミングの 3 つの操作は未対応。
