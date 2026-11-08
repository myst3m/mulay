# 071 — ドライバの文言と型の表は JDBC ドライバの jar から生成し、手で編集しない

状態: **採用** (sqlite_codes は 2026-09-30、9e7932e。ora_sqlstate は 2026-09-30、5e8148a。ora_zones は 2026-10-01、2f2558f)

## 決定
- 次の ns は Java の生成器の出力で、手で編集しない:
  - `db/sqlite_codes` (`tools/gen-sqlite-codes.java`): xerial sqlite-jdbc の `org.sqlite.SQLiteErrorCode`。
    SQLException の文言 `[<名前>] <文言> (<sqlite3_errmsg>)` を作るのに使う。拡張コードで見つからなければ下位 8 ビットで引く。
  - `db/ora_sqlstate` (`tools/gen-ora-sqlstate.java`): ojdbc11 23.8 の `oracle.jdbc.driver.SQLStateMapping`。
    RANGES は `[low high SQLState 例外の class]` で、ORA 番号が low 以上 high 以下の最初のものを使う。
  - `db/ora_zones` (`tools/gen-ora-zones.java`): ojdbc11 23.8 の `oracle.sql.ZONEIDMAP`。地域の番号 (TIMESTAMP WITH
    TIME ZONE の 12・13 バイト目の 13 ビット、10 進の文字列) → 地域の名前。
- 表を変えるときは生成器を直して作り直す。

## 理由
- 文言、SQLState、例外の class、時間帯の名前は Mule のエラーの型と description、DW の値にそのまま出るので、実 Mule が
  使うドライバの表と同じでなければならない。

## 場所
- `mulay.db.sqlite_codes/CODES`、`mulay.db.ora_sqlstate/RANGES`、`mulay.db.ora_zones/ZONES`、`mulay.db.sqlite/err-of`、
  `mulay.db.oracle/ora-state`、`mulay.db.oraproto/tz-name`
