# 純 Clay の SQLite (libsqlite3 を外す)

2026-10-11 にユーザが決めた (外部ライブラリを減らす)。同じ日に純 Clay の版 (db/sqlite2) に差し替え、FFI 版を消した
(6c1a996、964eeec。db/sqlite2 は後で db/sqlite に改名した: 860b4bf、aa7c33d)。mulay は libsqlite3 をリンクしない。
この文書は経緯と設計の記録。今の SQL の範囲と実 Mule との違いは docs/compat/deviations.md の SQLite の行。

## 正しさの基準

- 実 Mule の db-sqlite が使う SQLite は、sqlite-jdbc 3.50.3.0 に同梱の **SQLite 3.50.3**。値、格納型、失敗の文言はこれに合わせる。
- 手元の libsqlite3 (差し替え前の FFI 版が使っていたもの) と Python の sqlite3 は **3.53.4**。3.50.3 との違いは、新しい関数や細かな文言だけと見込む。
  差分テストの oracle には 3.53.4 を使う。食い違えば、実 Mule (mule-oracle) で 3.50.3 の答えを確かめる。
- ファイルは SQLite の形式 (https://www.sqlite.org/fileformat2.html) そのまま。mulay が書いたファイルを sqlite3 で開いて
  `PRAGMA integrity_check` が ok になることを、書き込みの受け入れの条件にする。

## 範囲

段に分ける。範囲の外の SQL は、"unsupported: .." で失敗させて deviations.md に記す (黙って違う答えを返さない)。

1. 第 1 段: db-sqlite のシナリオが使うもの (CREATE / DROP TABLE、INSERT、SELECT の WHERE・ORDER BY・集約、UPDATE、DELETE、
   AUTOINCREMENT、パラメータ)。これに JOIN、副問い合わせ、GROUP BY・HAVING、LIMIT・OFFSET、CREATE INDEX、トランザクション
   (BEGIN / COMMIT / ROLLBACK)、よく使う関数 (文字列、数、日付の一部)、型の affinity と比較の規則。
2. 第 2 段: ビュー、トリガー、ALTER TABLE、UPSERT、RETURNING、ウィンドウ関数、CTE (WITH)。CTE (再帰を含む) は入れた
   (0b3d064、dde62b4)。他は未実装 (unsupported で失敗する)。
3. 範囲外: 仮想テーブル (FTS など)、WAL (rollback journal だけ。WAL のファイルは開けないと失敗させる)、拡張の読み込み。
   WAL のファイルは "unsupported: WAL database" で失敗する (lib/sqlfile)。rollback journal は未実装 (docs/todo.md)。

## 層

- `lib/sqlfile`: ファイル形式 (varint、record、ページ、table と index の B-tree、overflow、freelist、ヘッダ)。ページの読み書きの
  入口は差し替えられる形にする (ファイルと、`:memory:` のメモリ上のページ。どちらも同じ道を通す)。
- `db/sqlite`: SQL の字句と構文、式の評価 (affinity、比較、NULL、整数の溢れ)、実行、トランザクションと
  rollback journal、接続の間で共有する DB (`file:..?mode=memory&cache=shared`) とロック。API は今の db/sqlite と同じ。
- 差し替えは SFTP と同じく 1 コミットで、db-sqlite のシナリオと単体テストで確かめる。
- 実際の分け方: SQL の字句・構文・実行は lib/sqlparse・sqlexec (と sqlval・sqlfunc・sqlnum)、B-tree は lib/sqlbtree、
  ファイル形式は lib/sqlfile、ドライバ (接続、共有のメモリの DB、トランザクション) は db/sqlite。

## clay に頼むもの

- ファイルの I/O: 切り詰めずに開く、pread / pwrite、fsync、ftruncate、大きさ、POSIX のバイト範囲のロック (他のプロセスの
  sqlite と安全に共存するため。Windows は LockFileEx)。2026-10-11 に依頼。clay 0.85.0 の clay.io の File に入った
  (pread、pwrite、sync、truncate、size、バイト範囲のロック)。mulay はまだ使わない (ファイルの DB は全部読み、全部書く。docs/todo.md)。

## テスト

- 差分テスト: 同じ SQL を基準の SQLite (Python の sqlite3) と純 Clay に流し、値、格納型 (typeof)、errmsg を比べる。
  式は `SELECT <式>` を大量に作って突き合わせる (ファイル I/O が要らない)。
- ファイル形式: Python で作った .db を読む。mulay が書いた .db を Python で読み、integrity_check を通す。

## 速さ

実 Mule (sqlite-jdbc、ネイティブの SQLite) と段ごとに比べる。純 Clay の版はこれを下回らないこと。

基準 (2026-10-11、target/sqlite-bench のアプリ。共有キャッシュのメモリの DB、表 t (id INTEGER PRIMARY KEY, k INTEGER, name TEXT,
v REAL) と k の索引。どちらも CPU 0-1 に固定し、温めた後の値):

| 段 | 実 Mule | mulay (libsqlite3 の FFI) |
|---|---:|---:|
| bulk-insert 10 万行 (DW で作った行) | 0.42〜0.45 s | 0.24 s |
| select 20 万行 (sizeOf) | 0.55〜0.57 s | 0.13〜0.14 s |
| foreach 1 万回の索引の等値の select | 0.75〜0.89 s | 2.2 s |

foreach の select は FFI 版でも実 Mule より遅かった。原因は rt/stream のカーソルの登録表 (Atom(Map)) で、Clay の swap! が値を
共有のまま関数に渡すため、select ごとに表全体が写されて二次の時間になっていた (1000 回 0.03 s、2 万回 8.8 s)。clay 0.85.0 の
swap! のその場の更新で解決した (1 万回 0.13 s)。

純 Clay の版 (2026-10-11、db/sqlite、同じアプリ。負荷のある時に測ったので振れる):

| 段 | 実 Mule | mulay (純 Clay) | ライブラリだけ (lib/sqlexec) |
|---|---:|---:|---:|
| bulk-insert 10 万行 | 0.42〜0.45 s | 0.63〜0.66 s | 0.22 s |
| select 20 万行 | 0.55〜0.57 s | 0.30〜0.33 s | |
| foreach 1 万回の索引の等値の select | 0.75〜0.89 s | 3.0〜3.6 s | 0.04 s |

bulk-insert の差は、文ごとの swap! が STATE (と DB の値) を写すこと (clay 0.84 の swap!。clay の修正を待つ)。lookup の差は
rt/stream の swap! (todo) と、STATE の写し。

clay の swap! の修正 (b0213f78、まだ出ていない版) で作った mulay (2026-10-11、同じアプリ、CPU 0-1): bulk-insert 10 万行
0.33 s、select 20 万行 0.24 s、foreach 1 万回の lookup 0.14 s。どの段も実 Mule より速い。差し替えはこの版が出てから。

差し替えた版 (clay 0.85.0、target/sqlite-bench、CPU 0-1。964eeec): bulk-insert 10 万行 0.31〜0.32 s (実 Mule 0.42 s)、
select 20 万行 0.23 s (0.55 s)、foreach 1 万回の索引の lookup 0.13 s (0.8 s)。

## 分かっている違い (差し替えのときに deviations.md へ移した。「SQLite の ORDER BY の無い問い合わせ ..」の行)

- 集約のある問い合わせの ORDER BY で、並べる値が同じ行の順: SQLite は DESC の項目で入れた順の逆になることがある (内部の
  sorter の都合で、SQL では決まっていない)。純 Clay の版はいつも入れた順 (安定)。
- ORDER BY の無い問い合わせの行の順: SQLite は索引だけで答えられるとき (covering index) その索引の順に返すことがある。純 Clay の版は
  WHERE の「列 = 値」で索引を使うときだけ索引の順で、他は rowid の順。
