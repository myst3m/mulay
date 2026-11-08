# 066 — PostgreSQL のドライバはセッション・値・キー・失敗を pgjdbc 42.7 に合わせる

状態: **採用** (2026-09-30、586f716。TLS は 2026-10-04、4df5373)

## 決定
- 接続のときにセッションの TimeZone を実行環境の既定の地域 (JVM の既定と同じ)、DateStyle を ISO にする。
- 値の Java の型は列の型 (OID) で決める: int2 / int4 は Integer、int8 と oid は Long、float4 は Float、float8 は Double、
  numeric は BigDecimal、bool は Boolean、bytea は byte[]、date は java.sql.Date、timestamp と timestamptz は
  java.sql.Timestamp、それ以外は文字列。timestamptz はセッションの地域の時刻にし、時差の部分は捨てる。
- パラメータは pgjdbc の setObject と同じ OID で送る (String は varchar、BigDecimal は numeric など)。
- 生成されたキー: 文の後に `RETURNING *` (列を指定したらその列) を付け、返った行を使う (pgjdbc の getGeneratedKeys と同じ)。
- 失敗の文言は pgjdbc の `ServerErrorMessage#toString` と同じ形 ("ERROR: .." に Detail、Hint、Position、Where を続ける)。
  接続が壊れたときは SQLState 08006。clay.postgres の接続の失敗の文言も pgjdbc の形にする (サーバーが SSLRequest を
  断ったときは PSQLState.CONNECTION_REJECTED)。
- ストアドプロシージャの書き換え (docs/connectors.md) で、OUT だけのパラメータは void (OID 2278) で送り、結果の 1 行目の列を
  OUT のパラメータに順に当てる。

## 理由
- 実 Mule のアプリが使う JDBC ドライバが pgjdbc 42.7 なので、値の class・文言・エラーの型をそれに揃える。
- void で送るのは、PostgreSQL が void のパラメータを関数の引数から外すため (pgjdbc と同じ)。
- TLS の規則は docs/connectors.md と deviations.md にある。利用者の証明書 (sslcert / sslkey) と NonValidatingFactory 以外の
  sslfactory を失敗にするのは、黙って無視して証明書なしで繋がないため。

## 場所
- `mulay.db.pg/open`、`mulay.db.pg/cell-of`、`mulay.db.pg/timestamp`、`mulay.db.pg/param-of`、`mulay.db.pg/run`、
  `mulay.db.pg/error-text`、`mulay.db.pg/connect-err`、`mulay.db.pg/call-sql`、`mulay.db.pg/VOID-OID`、`mulay.db.pg/call-proc`、
  `mulay.db.pg/ssl-of`
