# 063 — SQL の本文は mule-db-client の規則で読み、読んだ結果と構文解析の結果を本文ごとに控える

状態: **採用** (2026-09-30、e012ab6。控えは 2026-10-11、15a28b2 と 2e9a1bc)

## 決定
- SQL の本文の読み方は mule-db-client の `SimpleQueryTemplateParser` と `StatementTypeDetector` に合わせる。
  - 前後の空白を除く。`:name` を `?` にして名前を並べる。名前は区切りの文字 (空白、`" ' : & , ; ( ) | = + - * % / \ < > ^`)
    の手前まで。`:=` と `::` はそのまま、`\:` は `:` にする。`?` は名前の無いパラメータ ("")。
  - `'...'`、`"..."`、`--` から行末、`/* ... */` の中は読み飛ばす (そのまま残す)。
  - 種類は、大文字にした本文が次の形の最初のもの (どれでもなければ DDL): SELECT / INSERT / DELETE / UPDATE
    (語の後に空白 1 つ以上と 1 文字以上)、STORE_PROCEDURE_CALL (`{ ` と `:x =` を前に置いてよい CALL、後ろに空白が要る)、
    TRUNCATE (`TRUNCATE TABLE`)、MERGE、WITH (種類は SELECT)。判定の正規表現は Java の `Pattern` の (?ms)
    (MULTILINE 8、DOTALL 32) に当たる指定で作る。
- 読んだ結果 (`Template`) は本文の文字列ごとに atom に控える。SQLite の構文解析の結果 (`sp/Stmt`) も同じく控える。
  どちらも 256 件を超えたら空にしてから入れる。

## 理由
- foreach の中で同じ文を実行するたびに、種類を見分ける正規表現を作り直していた (1 回あたり約 3 万 6 千命令)。
  SQLite の構文解析は 1 回あたり約 2 万 2 千命令。

## 場所
- `mulay.db.sqltext/parse`、`mulay.db.sqltext/parse-text`、`mulay.db.sqltext/query-type`、`mulay.db.sqltext/DETECTORS`、
  `mulay.db.sqltext/SEPARATORS`、`mulay.db.sqltext/PARSED-MAX`
- `mulay.db.sqlite/parse`、`mulay.db.sqlite/STMTS`、`mulay.db.sqlite/STMT-MAX`
