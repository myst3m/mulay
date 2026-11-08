# 076 — DB の queryTimeout は、実行の間だけ動く見張りがドライバの中断を送る

状態: **採用** (2026-10-17)

## 決定
- 秒数は実コネクタの `BaseDbOperations.timeoutToSeconds` と同じく求める (`mulay.lib.time.unit/ceil-seconds`)。
  - `TimeUnit.toSeconds` で 0 の方へ切り捨て、戻したものが元より小さければ 1 秒足す (500 ms は 1 秒、1,500 ms は 2 秒)。
  - int に収まらなければ `MULE:UNKNOWN` "integer overflow"。
  - 負なら `MULE:UNKNOWN` "Query timeout must be positive" (`QueryStatementFactory.setQueryTimeout`)。
  - 0 なら見張りを立てない。
- execute-ddl は queryTimeout を使わない (実 Mule も 3 秒の DDL を最後まで流した)。
- 見張りは操作 1 回に 1 つ。バッチ (bulk-*、execute-script) にも全体で 1 つ。
  - `mulay.rt.ops/spawn-bg-try` で立てる。背景の仕事の上限 (512) に達していれば立てない
    (spawn-bg のようにその場で走らせると、呼び手が秒数だけ止まる)。
  - 見張りは 50 ms ごとに状態を見て、操作が終わっていればすぐ抜ける。
- 中断の送り方はドライバの JDBC ドライバに合わせる。
  - PostgreSQL: pgjdbc と同じく CancelRequest (`clay.postgres/cancel`。別のソケットで送り、サーバーが閉じるまで待つ)。
  - MySQL: Connector/J と同じく、同じ設定で開いた別の接続から `KILL QUERY <スレッド ID>` を送る。スレッド ID はハンドシェイクのもの。
  - Oracle: ojdbc 23.8 と同じく、同じ接続に中断の合図を送る (`mulay.db.oracle/cancel`)。
    - 接続のときに緊急データを受けられると申し出る (CONNECT のサービスのオプションに 0x0C00、接続の旗 2 に 1)。
      サーバーが ACCEPT の旗 2 の 1 で確かめを求めたら、緊急データ `!` と interrupt の marker `[2 0 3]` を送る。
    - 中断は、ACCEPT のオプションに 0x400 があれば緊急データ `!` (`clay.net/write-urgent`) に続けて `[2 0 3]`
      (0x800 があれば marker は送らない)、無ければ in-band の `[1 0 3]`。ojdbc は応答を待っている間の中断に interrupt (3)
      を送る (送っている間なら break (1))。mulay は書き終えるまで待ってから送るので、いつも interrupt。
    - 書き込みは接続の Atom で排他にする (見張りの合図が、送っている途中の要求に割り込まない。ojdbc の書き込みの錠と同じ)。
    - サーバーから marker を受けたら reset `[1 0 2]` を返し、受けたのが break のときだけ、サーバーの reset の marker まで読み捨てる
      (ojdbc の NIOMarkerPacket / sendReset と同じ。受けたのが reset なのに次の reset を待つと、続く ORA-01013 のデータを読み捨てて止まる)。
    - 要求の最後のデータパケットに end-of-request の旗 (0x0800) を立てる (ACCEPT が end-of-response を許したとき。ojdbc と同じ)。
  - SQLite は見張りを立てない (残した差を参照)。
- 状態は 0 実行中、1 終わった、2 中断している、3 中断した の Atom で持つ。
  - 操作が 0 → 1 にできなければ、見張りが 2 にしている。3 になるまで待ってから接続をプールに返す。
  - 中断の要求は、その時に動いている文に効く。プールに返した後に届くと、次の借り手の文を止めてしまうので、待つ。
- MySQL は、見張りが中断したら、操作の結果にかかわらず `DB:QUERY_EXECUTION` "Statement cancelled due to timeout or client request"
  にする (止めた SLEEP は 1 を返して成功するが、Connector/J は MySQLTimeoutException にする)。
  - bulk は除く。Connector/J の executeBatch は例外にせず、止めた文の結果をそのまま返した (SLEEP を止めた組は件数 1)。

## 理由
- 実 Mule 4.11.3 で db-pg (pg_sleep)、db-mysql (SLEEP)、db-oracle (DBMS_SESSION.SLEEP)、db-sqlite を記録した (2026-10-17)。
- 秒への直し方と負の値の扱いは、mule-db-connector 1.16.3 の BaseDbOperations と QueryStatementFactory を javap で読んだ。

## 残した差
- **Oracle:** テストの DB (kind の Oracle 23.26、port-forward 越し) は ACCEPT で緊急データを許さない (オプション 0x0801) ので、
  合図は in-band の marker になり、サーバーは文を終えてから読む。insert は約 3 秒 (sleep の長さ) 後に ORA-01013 で、行は入る
  (実 Mule も同じ。test/fixtures/apps/db-oracle の /qt/insert と /qt/reuse。時機によって ORA-06512 の行が付くので最初の行だけ比べる)。
  - stored-procedure の中断の結果は経路で変わる (実 Mule は直接なら成功、記録用の中継を挟むと ORA-01013 と ORA-06512 の行。
    mulay は中継越しでも ORA-01013 だけ)。シナリオには入れない。
  - 緊急データの道 (オプション 0x400) は、許すサーバーで照合していない。
  - 実 Mule でも select の中断は毎回は起きなかった (3 回中 1 回)。
- **SQLite:** sqlite-jdbc は queryTimeout を、その呼び出しの間の busy timeout (既定 3 秒) にするだけで、実行中の文は止めない。
  - mulay の SQLite には接続どうしの書き込みのロックが無いので、ロック待ちそのものが起きない (docs/todo.md)。

## 場所
- `mulay.conn.db/query-timeout`、`arm`、`watch`、`disarm`、`cancel-handle`、`kill-query`、`timed-out`
- `mulay.lib.time.unit/ceil-seconds`、`mulay.rt.ops/spawn-bg-try`、`mulay.db.mysql/Conn` の thread
- `mulay.db.oracle/cancel`、`reset-after-marker`、`take-wr`、`Conn` の opts と wr、`mulay.db.orawire/marker`、`marker-reset?`、`data-packets` の eor、
  `mulay.db.oraproto/connect-packets`、`accept-options`
