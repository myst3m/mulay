# 103 — 取ったものは with-cleanup で返す (処理が途中で失敗しても)

状態: **採用** (2026-10-25)

## 決定

- 数を増やす、表に載せる、順番の札を取る、接続を借りる、のように「後で返す」ものは、clay 0.99.0 の `with-cleanup` で返す。
  返す処理を、仕事の後ろの行に書かない。
- Clay の失敗 (範囲外の nth など、mulay の不具合) は run-server のハンドラと、そこから起こした future の中では要求 1 つを止めるだけで、
  プロセスは動き続ける (clay の ADR 024)。失敗した関数の後ろの行は走らないので、後ろに書いた返す処理も走らない。
  with-cleanup の cleanup は、失敗が上がる途中で走る。
- 場所ごとの包み:
  - `rt/ops/spawn-bg-in`・`spawn-bg-try-in`: 裏の処理の数 (BACKGROUND、gRPC のサーバーの stream の数 SERVER-STREAMS)。
  - `rt/ops/tracked`: 処理中の要求の数 (graceful shutdown が 0 になるのを待つ数、/__/metrics)。app/run の要求、dispatch-to、run-in。
  - `rt/stream/owned` と裏の処理の cleanup: 持ち主 (要求の rid など) の数。最後の leave が、その持ち主の開いたままの cursor
    (DB の select の stream など) を閉じる。app/run の要求と piped-resp (sink も閉じる)、db の listener の select、async、batch。
  - `rt/engine/with-sem`: 同時に走る数の札 (flow の maxConcurrency、async の maxConcurrency、batch の取り出しと aggregator)。
    返さない札が残ると、その flow は上限に達した後、新しい event を永遠に待たせる。
  - `rt/ostore/with-turn`: 永続する object store を書き出す順番 (ticket と serving)。serving が進まないと、後の書き出しが永遠に待つ。
  - `rt/ops/on-fail` (失敗した時だけ undo を走らせる): DB の接続。普通の道では、接続は返すか、select の stream (stream/open) に渡すか、
    行を持つ cursor (hold-rows) に渡す。渡した後は cursor が返すので、cleanup が返すのは失敗した時だけ。失敗した接続は壊れたものとして閉じ
    (状態が分からないため)、見張り (query timeout の arm) も外す (pool に戻った接続を後で止めないため)。
    トランザクション (run-in の tx、try の transactionalAction) は、失敗したら rollback して接続を返す。tx-end も接続ごとに返す。
- Values を返す処理も、そのまま with-cleanup の補助関数に渡す (clay 0.100.0、clay の ADR 131 から。それより前は Values を返せず、
  record (Ran・Took・Polled) に詰めて包んでいた。2026-10-26 に外した)。

## 理由

- 返し忘れた数は減らないまま残る。裏の処理の上限 (512) や gRPC の stream の上限 (4096) は、失敗のたびに 1 つずつ減り、
  いつか新しい処理をすべて断る。
- 失敗を値に変えて続けることはしない。失敗は不具合として見えたまま上へ伝わる (要求は 500)。

## 場所

- `mulay.rt.ops/counted`、`spawn-bg-in`、`spawn-bg-try-in`、`tracked`
- `mulay.rt.stream/owned`
- `mulay.rt.engine/with-sem`、`mulay.rt.ostore/with-turn`、`mulay.rt.ops/on-fail`
- `mulay.conn.db/run-op`、`tx-end`、`mulay.rt.engine` の PrTry、`mulay.app.run/run-in`
- 試験: test/rt/cleanup_test.clay (run-server の中で失敗させ、数が戻ることを見る)
