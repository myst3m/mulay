# 065 — PostgreSQL の bulk と execute-script は pgjdbc と同じ Sync の区切りごとに 1 回の往復で送る

状態: **採用** (bulk は 2026-10-12、746cc27。execute-script は 2026-10-12、f637b23)

## 決定
- 区切りは先頭が 255 文 (組)、その後は 256 文ずつ。区切りごとに文を続けて送り、最後に Sync を 1 回送る。
  - bulk: Parse + 組ごとの Bind/Execute + Sync (clay.postgres の `execute-batch`)。
  - execute-script: 文ごとに Parse / Bind / Describe / Execute を続けて送り、最後に Sync (`pg/execute-pipeline`)。
- 自動コミットでは Sync までが 1 つのトランザクション。途中で失敗すると、その区切りの中の前の文は取り消され、前の区切り
  までは残る。サーバは Sync まで捨てるので、返った結果の数が失敗した文の位置になる。
- bulk は型を指定せずに文を準備してサーバが推論した引数の型を得て、値をその Java の文字列の形 (Mule が渡す値の
  toString) で送る。準備できなければ (表が無いなど) 値の型 (pgjdbc の setObject の型) で失敗の文言を作る。
- 失敗の文言は pgjdbc の BatchUpdateException: `Batch entry i <値を埋め込んだ SQL> was aborted: ..`。値を埋め込んだ
  SQL は pgjdbc の `ParameterList#toString` の型の後置 (`::int4` など) を付ける。

## 理由
- 区切りの大きさは pgjdbc の `QueryExecutorImpl#flushIfDeadlockRisk` から: 受け取りの見積もりが 64000 バイトに届いたときと
  最後に Sync を送り、結果の行の大きさを知らない文は 1 文 250 バイトと見積もる。足してから比べるので 256 文目を送る前に
  Sync する。区切りでのトランザクションの境目は実 Mule の記録 (db-pg の /bulk-tx-n、/script-tx) で確かめた。
- 引数の型をサーバに問うのは、Mule が ParameterMetaData で型を問い合わせ、値をその型に変換して渡すのと同じにするため。
- execute-script を文ごとに往復と自動コミットで送っていたときは、3118 文の seed.sql が 10〜12 秒かかった
  (実 Mule は 0.17〜0.24 秒)。区切りごとの 1 往復にして 0.14〜0.19 秒。区切りの中が 1 つのトランザクションになり、
  途中の失敗で前の文が残る差もなくなった。

## 注意
- 型の後置のうち実 Mule の記録で確かめたのは int4 と文字列だけ。他は pgjdbc 42.7 の SimpleParameterList の表による。
  型が分からないものと文字列の型には付けない。

## 場所
- `mulay.db.pg/batch-segments`、`mulay.db.pg/run-batch`、`mulay.db.pg/run-script`、`mulay.db.pg/script-requests`、
  `mulay.db.pg/result-count`、`mulay.db.pg/java-text`、`mulay.db.pg/type-suffix`、`mulay.db.pg/render-sql`、`mulay.db.pg/batch-err`
