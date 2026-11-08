# 070 — Oracle の実行: 指定したキーの列は ROWID で読み直し、LOB の列のある select は全部読み、型の揃わない bulk は組ごとに実行する

状態: **採用** (2026-09-30、a48b0c6。select の少しずつの読み出しは 2026-10-03、c51ee46。配列の DML は 2026-10-03、9f789ad と 00932c1)

## 決定
- 値: TIMESTAMP / TIMESTAMP WITH TIME ZONE は oracle.sql.TIMESTAMP / TIMESTAMPTZ (`CDatum`)。TIMESTAMPTZ の timeZone は
  時差なら "GMT+09:00" (0 なら "GMT")、地域なら "Asia/Tokyo" (12 バイト目の最上位ビットが地域の印)。空の文字列は NULL。
  パラメータは数を NUMBER、文字列を VARCHAR2、真偽を BOOLEAN、LocalDateTime を TIMESTAMP、日付を DATE、バイト列を RAW で送る。
- NUMBER は内部形式 (DUMP(x) で見える形。thin でもこのまま運ぶ) を `db/oranum` で 10 進の綴りと相互に変換する。綴りに
  指数表記は使わない。符号化は 21 桁目以降を四捨五入する (100 進の桁は最大 20 個)。
- 生成されたキーに列の名前を指定したときは、INSERT の表を返った ROWID で読み直した値を返す。
- LOB の列がある問い合わせ (と問い合わせでない文) は少しずつ読まず、define してから `run` で全部読む (open-query で
  開いたカーソルは次の実行の前に閉じる)。define の応答にも行が来ることがあり、ORA-01403 なら読み終わり。
- 配列の DML (bulk) の位置ごとの型は NULL でない組の型で、大きさは全部の組の最大。
  - 組によって値の型が違うとき、問い合わせと PL/SQL は、組ごとに `run` で実行する。
  - 件数が返らないとき (direct-path の APPEND_VALUES など) は ojdbc と同じく組ごとに SUCCESS_NO_INFO (-2)。
  - 失敗は BatchUpdateException (文言と SQLState は元のまま)。接続の失敗 (SQLRecoverableException) はそのまま。

## 理由
- キー: ojdbc は RETURNING .. INTO で返すが、トリガーの後の値なので ROWID で読み直しても同じ値になる。

## 場所
- `mulay.db.oracle/bind-of`、`mulay.db.oracle/run`、`mulay.db.oracle/insert-table`、`mulay.db.oracle/open-query`、
  `mulay.db.oracle/whole-query`、`mulay.db.oracle/fetch-more`、`mulay.db.oracle/batch-binds`、`mulay.db.oracle/run-batch`、
  `mulay.db.oracle/run-each`、`mulay.db.oracle/batch-err`、`mulay.db.oraproto/tz-name`、`mulay.db.oranum/decode`、
  `mulay.db.oranum/encode`
