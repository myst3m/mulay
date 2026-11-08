# 012 — 純 Clay の SQLite は SQLite 3.50.3 のソースの手順を写し、B-tree のページは読み解いた形で持ち、分け方は SQLite と違ってよい

状態: **採用** (2026-10-11。lib/sqlbtree は 5b2ca69、読み解いた形と塊は 0672fec、文の実行は dde62b4、索引で絞るのは a0cfa23)

経緯、層の分け方、正しさの基準、速さは docs/sqlite.md。範囲外の SQL と行の順の違いは docs/compat/deviations.md。

## 決定

### 値と式と関数は SQLite のソースを写す

- `mulay.lib.sqlval` は vdbe.c・vdbemem.c、`mulay.lib.sqlexec` は vdbe.c・expr.c、`mulay.lib.sqlfunc` は func.c の手順を写す。
  失敗の文言は SQLite の errmsg と同じ。
- `mulay.lib.sqlnum` は util.c と printf.c の手順を**ビットまで同じになるように**写す (sqlite3AtoF と printf の `%!.15g`、どちらも
  Dekker の 2 倍の精度の掛け算)。正しく丸めた変換ではない: たとえば "8.219597356351074e+174" は最近接の double より 1 ulp 大きくなる。
- 符号なしの 64 ビットは Int に入れて、比較と割り算だけ符号なしで行う (`ult?`、`udiv10`)。
- 名前の確かめは、行が無くても準備の段で行う (SQLite は準備のときに失敗する。`validate-core`)。
- 文ごとに元に戻す: 失敗した文の変更は返さない。実行の途中の失敗は changes() を 0 にし、準備の段の失敗 (表や列が無いなど) は変えない
  (`exec-general`)。
- WHERE の AND でつながった項に「列 = 式」(式は表の列を使わない) があり、その列が rowid (INTEGER PRIMARY KEY) か、索引の先頭の列
  (照合順序が列と同じ) なら、その値の行の rowid だけを読む。読んだ行は WHERE 全体で確かめる。CAST と COLLATE は affinity と
  照合順序が変わるので使わない (`matching-rows`、`index-rowids`)。
- 構文 (`mulay.lib.sqlparse`): "x" は列が無ければ文字列として読む (SQLite の既定の DQS)。REFERENCES は読んで捨てる (外部キーは
  確かめない。SQLite の既定と同じ)。INDEXED BY と NOT INDEXED は読んで捨てる。WITH の後に INSERT・UPDATE・DELETE が来るものは扱わない。

### B-tree (`mulay.lib.sqlbtree`)

- ページはメモリに持つ (`Pager`)。ファイルとの読み書きは別の層。
- b-tree のページは読み解いた形 (`Pg`: 種類、セルの並び、右端の子、大きさ) で持ち、ファイルの中身に書き出すとき (`to-bytes`) にだけ
  組み立てる。overflow と freelist のページはバイト列のまま持つ。開いたときに木のページ (sqlite_schema の木と、その行の rootpage の木)
  を読み解いておく。
- ページの分け方は SQLite と同じではないが、できるファイルは SQLite の形式どおり (sqlite3 の PRAGMA integrity_check が通る)。
  `split` は左から詰めて半分を超えたら次のページへ送り、親へ上げる区切りは上げた後も 1 つは残るよう 2 つ以上たまってから区切る。
- 空になったページ (`fix-empty`) は木の深さをどこも同じに保って直す: 表の葉は親から外す。索引の葉と内部のページは、親の区切りのセルと
  一緒に隣のページ (左があれば左、無ければ右) へ併せる。根が子 1 つだけの内部のページになれば、その子の中身を根に写して 1 段低くする
  (ページ 1 で収まらなければそのまま)。
- 索引の削除で、葉が空になり、置き換える内部のページも溢れる稀な場合は、木を作り直す (`rebuild-without`)。
- 索引のキーの比べ方 (`KeyCmp`) は呼び出し側が与える (`mulay.lib.sqlval` を使うのは呼び出し側。sqlbtree は sqlval に依存しない)。
- `mulay.lib.sqlval/record-compare-at` は索引のセルから payload を切り出さずに比べ、列を 1 つずつ読み解き (違う列が見つかれば残りは
  読まない)、整数どうしは値を作らずに比べる。

### ファイル形式 (`mulay.lib.sqlfile`)

- ページを読む入口は `page-off` の 1 か所。壊れたファイルでも範囲の外を読まず、"database disk image is malformed" で失敗する。
- UTF-8 以外のファイルと WAL のファイル (版 2) は開けない (`open-bytes`)。

## 理由

- 実 Mule の db-sqlite は sqlite-jdbc 3.50.3.0 に同梱の SQLite 3.50.3 を使う (docs/sqlite.md)。値・格納型・文言はこれに合わせる。
- 読み解いた形で持つと書き込みが速い (0672fec: 1 行あたり約 105 万命令から約 3 万命令)。写しを避ける書き方は ADR 001。

## 場所

- `mulay.lib.sqlnum/atof`、`printf-double`、`real->text`、`mul2`、`ult?`、`udiv10`
- `mulay.lib.sqlexec/validate-core`、`exec-general`、`matching-rows`、`index-rowids`
- `mulay.lib.sqlbtree/Pager`、`Pg`、`decode-pg`、`encode-pg`、`to-bytes`、`from-bytes`、`split`、`split-place`、`fix-empty`、
  `rebuild-without`、`index-delete`、`KeyCmp`
- `mulay.lib.sqlval/record-compare-at`、`mulay.lib.sqlfile/page-off`、`open-bytes`
