# 058 — http:listener はポートごとの経路表で振り分け、全ポートが開いてから READY にする

状態: **採用** (2026-09-28。host の bind は 2026-10-04 bec8edf、chunked の応答は 2026-10-09 cdf0d86 と 588c98c、
READY の待ちは 2026-10-12 f271218)

## 決定
- **経路表** (`mulay.app.run/Route`): アプリの http:listener に加え、A2A のサーバー (カードと JSON-RPC)、MCP のサーバー、
  Salesforce の OAuth の認可コード (authorize と callback。フローは無い)、gRPC のサーバーの口も同じ表に入れる。
  listener 以外は、コネクタの `:mounts` が返す `Mount` から作る (ADR 081 の段 5)。listener-config (ポート) ごとに
  run-server を 1 つ回し、要求を受けたポートの経路だけから選ぶ。
- **経路の選び方** (`find-route`): パスが一致する経路のうち、具体さ (`specificity`: `*` 1 つにつき −100、`{` 1 つにつき −10) に
  メソッドが合えば +1000 を足した点の最も高いもの。
- **host**: listener-connection の host を bind 先にする (`bind-host`。制約は ADR 048)。同じポートの listener-config が別の
  host を指すと、ポートごとに 1 回しか待たないので片方が黙って無視される。起動の失敗にする (`host-conflicts`)。
- **READY**: すべての listener が待ち受けを始めるまで待ってから Listening のログと READY を出す (`wait-listeners`。実 Mule も
  全部のポートを開けてから配備を終える)。開けないポートがあれば理由を 1 度だけ言って終わる (終了コード 1)。
- **scheduler とポーリングは listener が開いてから動かす** (2026-11-08)。実 Mule は listener-config (サーバーのソケット) を
  フローのソースより先に始めるので、起動直後に動く scheduler が自分の listener を呼んでもつながる (トレースの記録
  propagation の own-tp-tick)。前は scheduler を先に起こし、その要求が 3 回に 1 回ほど Connection refused になった。
- **chunked の応答**: 本文は別のスレッド (`ops/spawn-bg`) で書く。読む側が遅くても handler を待たせない (`chunked-resp`)。
  streamResponse の応答 (PIPE) は、届いた断片ごとに書き、ストリームを新しい所有者に移して要求の終わりで閉じられないようにする。
  書き終えたら (失敗したときも) 所有者から抜けて閉じる (`piped-resp`。ADR 053)。
- **initialState="stopped"**: そのフローからソースを外したアプリで経路表と scheduler を作る (`live-app`)。フローの番号は変えない
  (止まったフローへの flow-ref は engine が断る)。メトリクスのフローの数は外す前のアプリで数える。

## 退けた案
- listener を 50 ms ずつずらして起こし、開いたかを見ずに準備完了にする (2026-10-12 まで)。後のポートへの要求が
  Connection refused になり、RTF の readiness がポートの開く前に 200 になりえた。

## 場所
- `mulay.app.run`: `Route`、`routes`、`mount-routes`、`ports`、`specificity`、`find-route`、
  `bind-host`、`host-conflicts`、`port-opts`、`start-listeners`、`wait-listeners`、`chunked-resp`、`piped-resp`、`live-app`、`serve`
