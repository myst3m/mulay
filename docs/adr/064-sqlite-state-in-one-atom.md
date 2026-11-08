# 064 — 純 Clay の SQLite は接続と DB を 1 つの atom に置き、文は swap! の中で実行する

状態: **採用** (2026-10-11、4fa22d6。DB と接続を表から抜いて使う形は ec59b7b)

## 決定
- 接続と DB は 1 つの atom (`STATE`) に置き、文は `swap!` の中で lib/sqlexec で実行する。Db は値なので、同じ DB の
  文は順に並ぶ。直前の文の結果 (res・code・msg) は接続のレコードに入れて swap! の外へ渡す。
- DB の置き場所は JDBC の url の `jdbc:sqlite:` の後ろで決める:
  - `""`、`:memory:`、`file:x?mode=memory` (cache=shared でない): その接続だけのメモリの DB。
  - `file:x?mode=memory&cache=shared`: 同じ名前の接続で共有するメモリの DB。最後の接続を閉じると消える。
  - 他 (パス、`file:パス?..`): ファイル。開くときに全部読み、変えた文の後 (自動コミットか COMMIT) に全部書く。
    無ければ空の DB で始め (sqlite3_open の CREATE と同じ)、書くのは最初の変更のとき。bulk は組を全部実行した後に 1 回だけ書く。
- トランザクションの中の変更はその接続だけの写し (`work`) に積み、COMMIT で共有の DB に置く。トランザクションの外で
  実行した文 (失敗なら元の DB が返る) と COMMIT は共有の DB に置き、トランザクションの中の文と ROLLBACK は置かない。
- select の結果は open-query で全部作り、fetch で n 行ずつ渡す。
- 値と文言は xerial sqlite-jdbc に合わせる: 値の Java の型は値の格納型で決まる (INTEGER は 32 ビットに収まれば Integer、
  そうでなければ Long、REAL は Double、TEXT は String、BLOB は byte[])。更新件数は changes()、生成されたキーは列
  "last_insert_rowid()" の 1 行、失敗の文言は "[<拡張コードの名前>] <その説明> (<errmsg>)" (org.sqlite.SQLiteException)。

## 理由
- 他の接続の書き込みを、トランザクションの間待たせない。
- ファイルの rollback journal とロックは未実装 (docs/todo.md、deviations.md の「SQLite のファイルの DB」)。

## 注意
- DB と接続は使う前に表から抜き、終わったら戻す。理由は ADR「Clay の制約を避ける書き方 (src/mulay/db)」。

## 場所
- `mulay.db.sqlite/STATE`、`mulay.db.sqlite/locate`、`mulay.db.sqlite/open`、`mulay.db.sqlite/step`、`mulay.db.sqlite/exec1`、
  `mulay.db.sqlite/persist`、`mulay.db.sqlite/changed?`、`mulay.db.sqlite/run-batch`、`mulay.db.sqlite/open-query`、`mulay.db.sqlite/val->cell`、`mulay.db.sqlite/run`、`mulay.db.sqlite/err-of`
