# 079 — gRPC のサーバー (unary-method) は http:listener の h2c の上で受ける

状態: **採用** (2026-10-18)

## 決定
- `<grpc:server-config>` の `<grpc:grpc-server-connection listenerConfig="..">` が指す http:listener-config の口で、記述子
  (`<grpc:single-binary-protobuf protobufDescriptorFile>`) にある全メソッドのパス `/<pkg.Service>/<Method>` を POST で受ける
  (`mulay.conn.grpc/server-methods`、`server-mounts`。コネクタの `:mounts`、ADR 081)。basePath は付けない (`Mount` の `:base` が false)。
  - listener-connection に `<http:protocol-support><http:http2-support enable="true"/>` があれば、平文の口で h2c の prior knowledge
    を受ける (clay の ServerOpts の h2c。同じ口で HTTP/1.1 も受ける)。無ければ h2c を受けない (実 Mule と同じ)。
  - 記述子に無いパスは、ほかの listener と同じく 404 "No listener for endpoint: <パス>"。
  - 記述子にあってフローの無いメソッドは grpc-status 12 "No source executor registered for method: <メソッド>"。
- フローの source は `<grpc:unary-method config-ref methodName>`。パーサーは grpc の名前空間の unary-method、server-streaming-method、
  client-streaming-method、bidirectional-streaming-method を source と見る。
  - メソッドの種類と source の組み合わせ (`mulay.conn.grpc/dispatch`): unary-method をストリーミングのメソッドに付けたフローは
    grpc-status 2 (メッセージ無し)。ストリーミングの source を種類の違うメソッドに付けると 12 "No source executor registered for method: .."
    (どちらも実 Mule と同じ)。
- 要求の本文の読み方 (`mulay.conn.grpc/read-request`、grpc-java の MessageDeframer と同じ文言):
  - 本文が空: 13 "Half-closed without a request"。
  - 枠の途中で終わる: 13 "Encountered end-of-stream mid-frame"。
  - 旗の予約ビット: 13 "gRPC frame header malformed: reserved bits not zero"。
  - 長さが maxInboundMessageSize (既定 4194304) を超える: 8 "gRPC message exceeds maximum size <上限>: <長さ>" (本文を読む前に判定)。
  - 圧縮の旗: 13 "Can't decode compressed gRPC message as compression not configured"。
  - メッセージが 2 つ以上: 13 "Too many requests"。
- payload は要求のメッセージのバイト列をそのまま持つ (読まなければ解釈しない。壊れたバイト列もそのまま返せる)。mime は
  `application/x-protobuf; charset=UTF-8; messagetype="<入力の型>"; descriptorurl="<記述子>"` (実 Mule の小文字の引数と順)。
    DW の `output application/x-protobuf ..` の結果の mediaType は、書いた順に関わらず descriptorurl、messagetype の順
    (形式の設定の順。ほかの形式の書き手の引数は HashMap の順。`mulay.rt.engine/out-media`。grpc-basic の /var-pass-rev)。
  DW で読むための descriptorUrl と messageType は TV の props で渡す。`payload.^mediaType` はこの mime そのもの。
- attributes は `com.mulesoft.connectors.grpc.api.server.UnaryServerAttributes` の {headers (名前は小文字、`:` で始まるものを除く),
  methodName, connectionId: ""}。
- 応答: HEADERS は `:status 200`、`content-type: application/grpc`、`grpc-encoding: identity`、
  `grpc-accept-encoding: identity,deflate,gzip`。本文は `<grpc:response-unary>` の値 (無ければ payload) のバイト列を 5 バイトの枠に
  入れたもの (protobuf かどうかは見ない。JSON は JSON のまま、Java の値は Java の直列化)。trailer は `grpc-status: 0`。
  - 失敗は本文無しで trailer に grpc-status と grpc-message (パーセント符号化)。`<grpc:error-response statusCode description>`
    があればその status と description (式も可)、無ければ 2 でメッセージ無し。
  - 応答の値を書けなければ 2。

## ストリーミング (2026-10-18)
- server-streaming-method: 要求のメッセージは単項と同じく 1 つ。属性は ServerStreamingServerAttributes {headers, methodName,
  connectionId (UUID)}。フローの中の `<grpc:send-stream-message config-ref attributes="#[..]">` (`<grpc:stream-message>` の
  バイト列) がメッセージを足し、`<grpc:end-stream attributes>` で閉じる (connectionId で引く。`mulay.conn.grpc/open-stream`、
  `push-message`、`end-stream`、`take-stream`)。閉じた後や知らない connectionId への send は MULE:UNKNOWN
  "No active stream found for connection: <id>"。フローの結果そのものは送らない。フローが失敗したら、それまでのメッセージの
  後に error-response の status。
- client-streaming-method: 受けたメッセージごとにフローを 1 回動かし (属性 ClientStreamingServerAttributes {headers,
  messageCount, streamState, streamCompleted: false})、`<grpc:output streamState="#[..]">` の値を次の streamState にする
  (書かなければ `{}`)。最後に payload null、streamCompleted true で動かし、`<grpc:output response="#[..]">` (既定は payload)
  を 1 つの応答にする。途中の失敗はそこで止めて error-response の status。
- bidirectional-streaming-method: メッセージごとにフローを動かし (属性 BidiStreamingServerAttributes {headers, messageCount,
  clientStreamCompleted, streamState, methodName, messageIndex (1 から), connectionId, timestamp (LocalDateTime)})、
  `<grpc:stream-output response streamState>` の response をそのつど 1 つ送る。最後に payload null、clientStreamCompleted true、
  messageIndex 0 で動かし、その response も送ってから status 0。
- 属性の headers は te を先頭に、残りは要求の順 (host と `:` で始まる名前を除く)。単項も同じ。
- 流して受け、流して送る (clay 0.92.0 の ADR 108)。
  - 受ける側: ストリーミングのフローのある経路 (server-streaming、client-streaming、双方向) だけ、listener の `ServerOpts :body-stream?`
    の述語 (`Mount` の `:stream` が true の経路の、メソッドとパス。`mulay.app.run/mount-streamed?`) が true を返し、本文を `hm/body-next` で片ごとに読む
    (`srv-piece`。期限切れの空読みは読み直す)。片は `split-frames` で枠に切り、途切れた枠は次の片まで残す。届くたびに読めるのは
    tasks の h2 だけで、HTTP/1.1 では本文が 1 つの片で来る (同じ書き方で動き、時機だけが違う)。
  - 送る側: `open-out` が流す応答 (`hm/stream-response`) の sink を connectionId の表 `OUTS` に置き、send-stream-message は
    sink に枠を書き、end-stream とフローの失敗は `hm/sink-close` に trailer (grpc-status 0、または error-response の status と
    description) を渡して閉じる。閉じた後の send は、sink への書き込みが閉じた sink で失敗することで知る。表は lock を取らない
    (全体の spin lock は並行 512 で 1 秒あたり 3 千件まで落ちた)。
  - 応答の頭は、最初の出来事 (メッセージ、終わり、失敗) まで返さない (`wait-out` が channel の close を待つ)。実 Mule も
    client-streaming は応答まで HEADERS を送らず、server-streaming もメッセージと一緒に送る (grpc-stream-live)。フローが何も
    送らずに失敗したときは、頭と trailer が一緒に出る。
  - server-streaming のフローと双方向の読み手は、ハンドラと別のスレッド (`ops/spawn-bg-try-in`) で動かす。ハンドラは頭を返した
    後も sink に書かせるため。数は gRPC のストリームだけで数え (`SERVER-STREAMS`、上限 4096)、超えたら実 Mule の back-pressure と
    同じ RESOURCE_EXHAUSTED (8) "Server streaming capacity exhausted. Please retry later."。共通の上限 512 を分け合うと、
    並行 512 の負荷で実 Mule が断らない要求を断った。client-streaming はハンドラの task の中で、届いたメッセージごとにフローを動かす。
  - 性能 (h2load、4.11.3 と同じ要求、grpc-stream の logger 付きのフロー): server-streaming は並行 128 で 1 秒あたり約 6.9 万件
    (実 Mule 1.0 万)、512 で 4.1 万 (1.5 万)。client-streaming は 512 で 6.2 万 (0.6 万)。双方向は 128 で 3.5 万 (0.7 万)、
    512 で 2.3 万 (0.8 万)。

## 理由
- 実 Mule 4.11.3 + mule-grpc-connector 1.0.4 で test/fixtures/apps/grpc-basic を記録した (2026-10-18、h2c の要求は mule-oracle の
  `request GRPC`)。壊れた枠などの文言は `frame=0` の要求で記録した。
- server-config を 2 つ置くと、実 Mule ではメソッドの登録がぶつかって既存のメソッドの応答まで変わった (記録しない)。

## 関連する式の規則
- 式の出力の形式を payload から推論するとき、protobuf の書き手が設定 (descriptorUrl) の不足で失敗すると、実 Mule と同じく
  `"<文言>\nTrace:\n  at main (Unknown)" evaluating expression: ".."` になる (`#[payload.name]` を set-variable に入れたとき)。
- logger の message は推論した形式で書き、書き手が失敗したら JSON で書き直す (ADR 078)。protobuf の payload の
  `'hello ' ++ payload.name` は `"hello Ann"` (grpc-basic の SayHello と Infer のログ)。
- 生のバイト列の TV で、形式の reader が mediaType を付けないもの (protobuf) の `^mediaType` は TV の mime そのもの
  (`mulay.rt.engine/with-format-meta`)。JSON などは今のまま reader の付ける mime (引数無し)。

## 場所
- `mulay.conn.grpc`: `dispatch`、`split-frames`、`read-messages`、`open-out`、`push-message`、`end-stream`、`fail-stream`、`wait-out`、`EXHAUSTED`、`header-fields`、`server-stream-attributes`、`client-stream-attributes`、`bidi-attributes`、ストリームの登録表、`server-methods`、`read-request`、`server-attributes`、`payload-mime`、`response-headers`、`status-trailers`、`error-status`
- `mulay.conn.grpc` (サーバーの経路。2026-10-20 に app/run から移した): `server-mounts`、`Served`、`srv-respond`、`srv-run`、`srv-server-stream`、`srv-client-stream`、`srv-client-run`、`srv-bidi`、`srv-bidi-run`、`srv-bidi-one`、`srv-piece`、`srv-body`、`srv-reply-frames`、`SERVER-STREAMS`
- `mulay.app.run`: `port-opts` の body-stream? (`mount-stream-paths`、`mount-streamed?`)、`http2?`
- `mulay.mule.parse/source-elem?` (GRPC-SOURCES)
