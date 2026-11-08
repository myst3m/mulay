# 043 — HTTP の経路で動くソース (A2A・MCP) は、要求を段に分け、フローは本体から渡された口で流す

状態: **採用** (2026-10-02 A2A、2026-10-07 MCP。2026-10-20 に経路と処理をコネクタへ移した、ADR 081 の段 5)

## 決定
- A2A のサーバーと MCP のサーバーは、自分でポートを開かず、http:listener-config のポートに経路を足す。経路はコネクタの
  `:mounts` (`mulay.rt.conn/Mount`) が返し、app/run が listener の設定を引いて経路表に入れる。ポーリングしない
  「HTTP の経路で動くソース」として、source の名前をコネクタの `:routed` に書く。
- 1 つの要求を段に分ける。コネクタの関数は「次に何をするか」を表す `Step` を返し、`Mount` の処理 (`srv-*`) が、
  app/run から渡された `Host` の `run` でフローを流し、その結果を次の段の関数に渡す。
  - A2A: `begin-rpc` が要求を読んで検査し、kind を返す。"done" はすぐ答える、"flow" は task-listener のフローに流す、
    "auth" は authorization-listener のフローに流して成否を `after-auth` に、"push" は push-notification-config-listener の
    フローに流して成否を `after-push` に渡す、"async" は 202 をすぐ返してフローを別に流し、`end-rpc` の答えを `push-answer` で
    通知の URL に送る。ストリーム (message/stream) は `start-stream` で SSE の応答を開き、task-stream-listener の
    フローを別に流す。`end-rpc` はフローの結果から答えを作り、タスクの記録に写す。
  - MCP: `begin` が kind を返す ("done" はすぐ答える、"call" は tool のフロー、"read" は resource のフロー、"prompt" は
    prompt のフロー)。フローが終わってから `finish` / `finish-resource` / `finish-prompt` / `finish-failure` が答えを作る。
    on-new-session-listener も同じく Step で流し、`finish-session` が答える。
- `Host` の `run` はフローを番号で動かし、所要時間を記録する (http:listener の経路と同じ `ops/record`)。listener の経路だけが
  行う `stream/enter`、`mt/flow-dispatched`、`am/record!` は呼ばない (移す前と同じ)。

## 理由
- 経路表とフローを動かす仕組み (`rt/engine`) は本体が持つ。コネクタは `rt/engine` の `Ctx` を型として持てない
  (`rt/engine` が `rt/conn` を読む) ので、Ctx の要る関数だけを `Host` の関数として受け取る。
- 外のコネクタも同じ口で経路を足せる (ADR 081)。
- 1 つの要求の中で複数のフロー (認可 → 本体、通知の設定 → 本体) を順に流すことがあり、その間の状態を Step に持たせる。

## 場所
- `mulay.conn.a2a/begin-rpc`、`mulay.conn.a2a/after-auth`、`mulay.conn.a2a/after-push`、`mulay.conn.a2a/end-rpc`、
  `mulay.conn.a2a/push-answer`、`mulay.conn.a2a/start-stream`、`mulay.conn.a2a/stream-failed`
- `mulay.conn.mcp/begin`、`mulay.conn.mcp/finish`、`mulay.conn.mcp/finish-resource`、`mulay.conn.mcp/finish-prompt`、
  `mulay.conn.mcp/finish-failure`、`mulay.conn.mcp/finish-session`
- ソースの見分け: `mulay.conn.a2a/ROUTED`、`mulay.conn.mcp/ROUTED` (Connector の `:routed`)
- A2A の経路と処理: `mulay.conn.a2a/server-mounts`、`task-mounts`、`Served`、`srv-*`
- MCP の経路と処理: `mulay.conn.mcp/server-mounts`、`SrvEnv`、`srv-*`
- 口: `mulay.rt.conn/Mount`、`Host`、`At`、`host-eval`、`host-eval-tv`。呼ぶ側: `mulay.app.run/mount-routes`、`mount-host`、`handle-app`
