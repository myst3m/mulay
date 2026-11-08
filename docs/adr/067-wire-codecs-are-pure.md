# 067 — DB のプロトコルの値の読み書きはソケットに触らない ns に分け、読み取りは (値 次の位置) と負の位置で失敗を運ぶ

状態: **採用** (Oracle は 2026-09-30、0e659ad と 5014d30。MySQL は 2026-10-10、51588ca)

## 決定
- パケットと値の符号化・復号は純粋な関数だけの ns に置き、I/O はドライバの ns に置く:
  Oracle は `db/orawire` (TNS のパケットと TTC の基本の値) と `db/oraproto` (TTC のメッセージの組み立てと応答の読み取り)、
  I/O は `db/oracle`。MySQL は `db/mywire`、I/O は `db/mysql`。
- 読む関数は `(値 次の位置)` を返す。足りなければ位置 SHORT (-1)、形が壊れていれば BAD (-2、orawire)。位置が負のときに
  呼んでも何もせずにその位置を返す。
- 応答の読み取り (`oraproto/parse`) は応答のバイト列を頭から読み、応答の終わり (メッセージ 29、EOR が無ければ ERROR か
  STATUS) まで読めたら done を立てる。SHORT なら呼び手が次のパケットを足して読み直す。

## 理由
- 続けて読んでから最後に一度だけ位置を調べればよく、読むたびに失敗を分岐しなくて済む。

## 場所
- `mulay.db.orawire/SHORT`、`mulay.db.orawire/BAD`、`mulay.db.orawire/take-packet`、`mulay.db.oraproto/parse`、
  `mulay.db.mywire/SHORT`、`mulay.db.mywire/take-packet`、`mulay.db.oracle/call`、`mulay.db.mysql/read-packet`
