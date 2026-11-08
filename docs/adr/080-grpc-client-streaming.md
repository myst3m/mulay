# ADR 080: gRPC のクライアントのストリーミングは gRPC として正しく流す (実 Mule のコネクタを真似しない)

日付: 2026-10-18。状態: 決定 (同じ日の「行きも帰りも溜めた 1 つの HTTP の要求にする」を置き換えた)。mule-grpc-connector 1.0.4 の
クライアントの server-streaming-call-with-response、server-streaming-call-with-delegation、client-streaming、bidirectional-streaming と、
source の server-streaming-delegated-listener、bidi-streaming-listener、それに client-config と操作の `<grpc:deadline>`。ADR 077 の続き。

## 経緯

最初は実 Mule の振る舞いに合わせた。調べると、実 Mule のコネクタのクライアントは gRPC のストリーミングとして使えない作りだった:

- 通信は grpc-java の netty ではなく、Mule の HTTP client の上の自前の `MuleHttpClientCall` (逆コンパイル)。`sendMessage` は枠を
  buffer に積むだけで、`halfClose` (endClientStreaming) の時に 1 つの本文として POST する。応答は本文を全部受けてから枠に切る。
- 記録で確かめた: client-streaming と双方向で 1 つ目を送ってから 4 秒後に end を送ると、スタブにも mulay の gRPC サーバーにも、
  呼び出しの頭と全部のメッセージが end の時刻に届く (`MULE_ORACLE_GRPC_TRACE`)。1 つ送って返事を待つ双方向はできない。
- Iterable は回し始めて pollTimeout (既定 500 ms) を 2 回待っても応答が全部届かないと NoSuchElementException で、エラーハンドラを
  素通りして 500 になる。listener は 500 ms に 1 フレームしか取り出さない。双方向の attributes は requestId の欄に routingId、
  messageSent はいつも true。相手が status 0 でメッセージ無しに終えると client-streaming は返らない (コードから)。

ユーザーの判断 (2026-10-18):「grpcに関しては本家の真似しないでいいです。きちんとした実装にして。つかいたいから」。

## 決定

- ストリーミングの 4 つの操作は clay の `http/open-call` (ADR 108 の段 2) で 1 つの呼び出しを開き、メッセージは届いた順にすぐ
  送り (`call-send`)、応答はメッセージが届くたびに渡す (`call-next` を読むスレッド、`read-live`、`start-reader`)。unary-call は
  今の `http/request` のまま (接続を使い回す)。
- 応答の status (`live-status`): trailer の grpc-status、無ければ頭のもの (`stream-status`)。どちらにも無い時は、HTTP の status が
  200 でなければそこから (unary-call と同じ対応表、"HTTP status code N")、200 なら UNKNOWN "Missing grpc-status in the response"。
- server-streaming-call-with-response: 呼び出しを開いて送り、すぐ返る。payload は Iterable のカーソル (`^class` は
  com.mulesoft.connectors.grpc.api.StreamedResponseIterable、`^mimeType` は `*/*`) で、foreach は届いたメッセージを順に回す
  (行は protobuf を読んだ値に mimeType application/x-protobuf と mediaType のメタ)。間が空いても待つ (pollTimeoutMs は使わない)。
  失敗は回し終えた後に GRPC:<CODE> "gRPC operation 'SERVER_STREAMING' failed with status <CODE>: <説明>\nMethod: <method>"
  (GrpcModuleException の形。型は終わった時に決まるので、カーソルの errorIdentifier を * にする。`ev/typed-error`)。
  カーソルを閉じる (フローが終わる) と呼び出しを cancel する。
- server-streaming-call-with-delegation: payload は新しい requestId、attributes は null。応答はメッセージが届くたびに routingId の
  server-streaming-delegated-listener に渡す。
- client-streaming: requestId (空なら UUID) ごとに最初の呼び出しで開き、content があればすぐ送る。相手の答え (`Outcome`) を
  読む側が持ち、操作の前後に答えが来ていればその場で返す (成功なら応答と ClientStreamingAttributes {endOfStream: true}、失敗なら
  GRPC:<CODE> "gRPC operation 'CLIENT_STREAMING' failed .. \nAdditional Details:\n  Method: ..\n  RequestId: ..")。end なら送る側を
  閉じて答えを待つ。end でなく responseWaitTime があればそのぶん答えを待ち、来なければ空の protobuf と {endOfStream: false}。
  相手が status 0 でメッセージを返さなければ INTERNAL "No value received for client streaming call"。答えたら表から消え、同じ
  requestId の次の呼び出しは新しい呼び出しになる。
- bidirectional-streaming: routingId と requestId (空なら UUID) ごとに最初の呼び出しで開き、content をすぐ送り、end で送る側を閉じる。
  応答のメッセージは届くたびに routingId の bidi-streaming-listener に渡し、最後に空の payload で endOfStream、失敗なら error と
  errorMessage ("ABORTED: chat stopped") のフレーム。attributes は ClientStreamingAttributes {endOfStream, messageSent (本当に送れたか),
  requestId (requestId)}。相手が終えた後の送りは捨てて messageSent は false (grpc-java と同じ)。終わった会話は表から消える。
- listener (source): push 型の source (`conn/Connector` の sources と push、`poll`)。表は config + routingId + 種類 (`s|` と `b|`)。
  1 つの poller が届いたフレームを順にフローに渡す。attributes は ServerStreamingAttributes {routingId, endOfStream, errorMessage,
  error, requestId}。payload は TypedValue に包んだ protobuf (`^mimeType` は `*/*`)。
- Deadline: 操作の子の `<grpc:deadline duration units>` か client-config の子 (既定 10 SECONDS)。あれば `grpc-timeout` ヘッダ
  (8 桁までの数と単位。`timeout-header`) を送り、時間が過ぎたら呼び出しを cancel して DEADLINE_EXCEEDED "Deadline exceeded"。
  unary-call も同じ (無ければ今まで通り 30 秒で INTERNAL "Unexpected error: Timeout exceeded")。ストリーミングは Deadline が無ければ
  待ち続ける (gRPC の決まり)。end を送らずに放った会話は、相手が閉じるか Deadline まで接続とスレッドを持つ。SIGTERM の停止は
  開いたままの呼び出しを待たない (確かめた)。
- server-streaming-subscriber-source は未対応。

## 確かめ方

- 実 Mule と同じ結果のもの (iterate の成功、Iterable の型、client-streaming の requestId ごとの送りと end、delegation): シナリオ
  test/fixtures/apps/grpc-client-stream (実 Mule 4.11.3 で記録)。
- 実 Mule と違うもの: test/fixtures/apps/grpc-client-live (`%%% oracle mulay`、mulay で記録して中身を確かめた)。流していることを
  シナリオ自体で示す: end を送らない双方向の 1 つ目の要求の窓に echo 1 が出る、相手が先に答える client-streaming が responseWaitTime
  の間にその場で失敗する、1.2 秒空く server-streaming を pollTimeoutMs 100 でも全部回す、delegation の 1 つ目が 0.6 秒の窓に届く、
  Deadline と grpc-timeout ヘッダ。

## 性能

h2load (HTTP/1.1 の listener から呼ぶ。相手はどちらも mulay の gRPC サーバー): foreach で回す server-streaming は 1 秒あたり
約 1.32 万件 (実 Mule 0.41 万)、end を 1 回の client-streaming は 1.35 万 (0.82 万)。呼び出しごとに接続を開くが、逐次の 3000 回で
`http/request` (接続を使い回す) と同じ速さだった。

## 関わるコード

- `mulay.conn.grpc`: `open-live`、`read-live`、`start-reader`、`live-status`、`stream-status`、`grpc-op-error`、`client-stream-error`、
  `status-text`、`deadline-of`、`op-deadline`、`timeout-header`、`next-rows`、`run-iterate`、`run-delegation`、`run-client-stream`
  (`Outcome`、`cs-resolve`)、`run-bidi` (`LIVE`)、`Frame` と `push-frame` / `take-frame`、`poll`、`CLIENT-SOURCES`、`run-unary` の Deadline。
- `mulay.rt.event`: `tv-cursor-of`、`typed-error`、`cursor-error`。`mulay.rt.engine/run-foreach-stream`。
- テスト: test/grpc/grpc_client_stream_test.clay。
