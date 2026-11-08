# 051 — コネクタは関数の record で表し、ソースの周期とトランザクションの確定は rt と app が持つ

状態: **採用** (2026-09-29 136894f。待ち受けるソースは 2026-09-30 724688d、トランザクションは 2026-09-30 65de06c)

docs/design.md §6.3 の計画 (connect / disconnect / schema を持つ record) より小さい形にした。この ADR はその差の中身を書く。

## 決定
- **操作**: `Connector` の `:run` 1 つが `OpCall` を受けて `OpResult` を返す。パラメータの式は `OpCall` の `:eval` (engine が用意し、PVal を
  その時点の Event で評価する) で評価する。フローや操作の中の経路は `OpCall` の `:flow` / `OpCall` の `:chain` で名前で呼び、無ければ
  3 つ目の戻り値が false。
- **OpResult**: err があれば失敗。`event` が 1 個あれば、payload と attributes だけでなく Event 全体をそれで置き換える
  (フローを呼ぶ操作: apikit:router)。失敗のときもその時点の Event にする。結果を payload にしない void の操作は `keep-result`。
- **ソース**: ポーリングするソースは `Connector` の `:poll` が 1 回分 (流した件数と失敗の説明) を実装する。周期
  (`<scheduling-strategy>`) は app 層が回し (`mulay.app.run/run-poller`)、見つけたものは `SrcCall` の `:dispatch` か `SrcCall` の `:run` で
  フローに流す。1 回の poll が終わってから次の時刻を決める。
  - 待ち受けるソース (`Connector` の `:push` に名前があるもの。vm:listener など) は、poll の中で来るまで少し待ち、返ったらすぐに
    次の poll を呼ぶ (周期を置かない)。並行に回す数は numberOfConsumers (既定は VM の listener が 4、それ以外は 1)。
  - ソースごとの状態は `SrcCall` の `:state` の Atom に持ち、poll をまたぐ。
- **初期化**: `Connector` の `:init` は起動の前に 1 回 (設定の検査や読み込み)。返した問題の列が空でなければ起動しない。
- **トランザクション**: Event が今のトランザクションの ID (`tx`) を持つ。ID は通し番号 (`TX-SEQ`)。終わりは
  `mulay.rt.engine/end-tx` が**すべてのコネクタの `tx-end` に知らせ**、持っている資源 (DB の接続など) を commit か rollback させる。
  - try の transactionalAction: ALWAYS_BEGIN (と、トランザクションの外での BEGIN_OR_JOIN) は新しく始め、終わりで確定する。
    INDEPENDENT (既定) と中の BEGIN_OR_JOIN は今のトランザクションのまま。
  - 確定の規則: エラーが無いか on-error-continue で扱えば commit、そうでなければ rollback。ソースから流すとき
    (`SrcCall` の `:run` に ID を渡したとき) も同じ。

## 理由
- Clay には protocol が無いので、コネクタは関数を持つ record にする (docs/design.md §6.3)。
- rt はコネクタを直接知らない (層の向き)。周期とスレッドは app 層が持ち、コネクタは 1 回分だけを書く。
  トランザクションの終わりも、特定のコネクタではなく登録表のすべてに知らせる。

## 場所
- `mulay.rt.conn`: `OpCall`、`OpResult`、`keep-result`、`SrcCall`、`Connector`、`connector`
- `mulay.rt.engine`: `end-tx`、`TX-SEQ`、`run-chain`、`call-flow`、try の実行
- `mulay.app.run`: `run-poller`、`consumers`、`run-in`、`dispatch-to`、`init-conns`、`polled-flows`
