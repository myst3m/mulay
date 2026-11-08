#!/usr/bin/env python3
# mulay.lib.sqlparse の文の構文解析の差分テストを作り、test/sql/parse_test.clay に書く。期待値は tools/sqlite-oracle prepare
# (sqlite-jdbc 3.50.3.0): 構文の誤りなら その errmsg、構文として通れば OK (表が無いなどの誤りは構文ではないので OK)。
# 使い方: python3 -I tools/gen-sqlparse-golden.py  (リポジトリの根で)
import re, subprocess

fixture = open("test/fixtures/apps/db-sqlite/src/main/mule/db-sqlite.xml").read()
stmts = []
for m in re.finditer(r"<db:sql>(.*?)</db:sql>", fixture, re.S):
    t = m.group(1).replace("<![CDATA[", "").replace("]]>", "").replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
    for part in t.split(";"):
        part = " ".join(part.split())
        if part: stmts.append(part)
stmts += [
    "SELECT 1", "SELECT", "SELECT 1,", "SELECT 1 AS", "SELECT a b FROM t", "SELECT a AS b, c d FROM t x", "SELECT * FROM t AS x WHERE x.a = 1",
    "SELECT t.* , 1 FROM t", "SELECT DISTINCT a FROM t", "SELECT ALL a FROM t", "SELECT a FROM t GROUP BY a HAVING count(*) > 1",
    "SELECT a FROM t ORDER BY a DESC, b ASC NULLS LAST, c COLLATE NOCASE", "SELECT a FROM t LIMIT 10", "SELECT a FROM t LIMIT 10 OFFSET 5",
    "SELECT a FROM t LIMIT 5, 10", "SELECT a FROM t LIMIT", "SELECT a FROM t ORDER", "SELECT a FROM t ORDER BY", "SELECT a FROM t GROUP a",
    "SELECT 1 UNION SELECT 2", "SELECT 1 UNION ALL SELECT 2 UNION SELECT 3 ORDER BY 1", "SELECT 1 INTERSECT SELECT 1 EXCEPT SELECT 2",
    "SELECT 1 UNION", "VALUES (1, 2), (3, 4)", "VALUES (1", "VALUES ()", "SELECT * FROM (SELECT 1 AS x) AS s", "SELECT * FROM (SELECT 1)",
    "SELECT * FROM t JOIN u ON t.a = u.a", "SELECT * FROM t LEFT JOIN u USING (a, b)", "SELECT * FROM t LEFT OUTER JOIN u ON 1",
    "SELECT * FROM t, u, v WHERE 1", "SELECT * FROM t CROSS JOIN u", "SELECT * FROM t NATURAL JOIN u", "SELECT * FROM t INNER JOIN u ON",
    "SELECT * FROM t JOIN", "SELECT (SELECT 1)", "SELECT EXISTS (SELECT 1)", "SELECT 1 IN (SELECT 1)", "SELECT 1 NOT IN (SELECT 2 UNION SELECT 3)",
    "SELECT (SELECT 1", "WITH c AS (SELECT 1) SELECT * FROM c", "WITH RECURSIVE c(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM c WHERE n<3) SELECT n FROM c",
    "WITH c AS SELECT 1", "WITH c(a, b) AS NOT MATERIALIZED (SELECT 1, 2) SELECT * FROM c", "WITH", "SELECT * FROM main.t", "SELECT * FROM t INDEXED BY i",
    "SELECT * FROM t NOT INDEXED", "INSERT INTO t VALUES (1)", "INSERT INTO t (a, b) VALUES (1, 2), (3, 4)", "INSERT INTO t SELECT * FROM u",
    "INSERT INTO t DEFAULT VALUES", "INSERT OR REPLACE INTO t VALUES (1)", "REPLACE INTO t VALUES (1)", "INSERT OR IGNORE INTO t VALUES (1)",
    "INSERT INTO t", "INSERT INTO t (a VALUES (1)", "INSERT t VALUES (1)", "INSERT INTO t VALUES", "UPDATE t SET a = 1", "UPDATE t SET a = 1, b = b + 1 WHERE c",
    "UPDATE OR IGNORE t SET a = 1", "UPDATE t SET", "UPDATE t a = 1", "UPDATE t SET a = 1 WHERE", "DELETE FROM t", "DELETE FROM t WHERE a = 1", "DELETE t",
    "DELETE FROM", "CREATE TABLE t (a)", "CREATE TABLE t (a INTEGER PRIMARY KEY AUTOINCREMENT, b TEXT NOT NULL DEFAULT 'x', c REAL UNIQUE CHECK (c > 0))",
    "CREATE TABLE IF NOT EXISTS t (a, b, PRIMARY KEY (a, b))", "CREATE TABLE t (a, b, UNIQUE (a), CHECK (a > b), FOREIGN KEY (a) REFERENCES u (x) ON DELETE CASCADE)",
    "CREATE TABLE t (a INT DEFAULT -1, b DEFAULT (1 + 2), c VARCHAR(10) COLLATE NOCASE, d DECIMAL(10, 2))", "CREATE TABLE t (a) WITHOUT ROWID",
    "CREATE TABLE t (a) STRICT", "CREATE TABLE t", "CREATE TABLE t ()", "CREATE TABLE t (a,)", "CREATE TABLE (a)", "CREATE TABLE t (a PRIMARY KEY DESC)",
    "CREATE TABLE t (a CONSTRAINT pk PRIMARY KEY, b CONSTRAINT nn NOT NULL)", "CREATE TABLE t (a REFERENCES u)", "CREATE INDEX i ON t (a)",
    "CREATE UNIQUE INDEX IF NOT EXISTS i ON t (a DESC, b COLLATE NOCASE)", "CREATE INDEX i ON t (a) WHERE a > 0", "CREATE INDEX i ON t",
    "CREATE INDEX ON t (a)", "DROP TABLE t", "DROP TABLE IF EXISTS t", "DROP INDEX i", "DROP TABLE", "DROP t", "BEGIN", "BEGIN TRANSACTION",
    "BEGIN IMMEDIATE", "COMMIT", "END", "END TRANSACTION", "ROLLBACK", "ROLLBACK TRANSACTION", "SELECT 1; SELECT 2", ";SELECT 1", "SELECT 1 FROM t WHERE a = 1 b",
    "SELECT a, FROM t", "SELECT count(*) FROM t", "SELECT count(DISTINCT a) FROM t", "SELECT a FROM t WHERE a IN (1, 2) AND b LIKE 'x%'",
    "SELECT CASE WHEN a THEN 1 END FROM t", "SELECT a FROM t WHERE NOT EXISTS (SELECT 1 FROM u WHERE u.a = t.a)", "SELECT * FROM t AS", "SELECT a FROM t t2",
    "SELECT end FROM t", "SELECT a FROM t WHERE end = 1", "SELECT \"a\" FROM \"t\"", "SELECT [a] FROM [t]", "SELECT a FROM t ORDER BY 1 DESC LIMIT 1",
    "SELECT * FROM t WHERE a = ?", "SELECT * FROM t WHERE a = :name", "SELECT 1 FROM t GROUP BY 1 ORDER BY 1",
]
q = "".join(s + "\n" for s in stmts)
out = subprocess.run(["tools/sqlite-oracle/sqlite-oracle", "prepare"], input=q.encode(), capture_output=True, check=True).stdout.decode().split("\n")

def clay_str(t):
    return '"' + t.replace("\\", "\\\\").replace('"', '\\"') + '"'

with open("test/sql/parse_test.clay", "w") as f:
    w = lambda s="": f.write(s + "\n")
    w(";; tools/gen-sqlparse-golden.py で作った (手で直さない)。期待値は sqlite-jdbc 3.50.3.0 の prepare:")
    w(";; 構文の誤りならその errmsg (E:..)、構文として通れば OK")
    w("(ns parse-test (:require [mulay.lib.sqlparse :as sp]))")
    w()
    w("(defn- pr Str [sql: Str] (let [[st e] (sp/parse sql)] (if (= e \"\") \"OK\" (str \"E:\" e))))")
    w()
    for i in range(0, len(stmts), 60):
        w("(deftest stmts-%d" % (i // 60))
        for j, s in enumerate(stmts[i:i + 60]):
            w("  (is (= (pr %s) %s))" % (clay_str(s), clay_str(out[i + j])))
        w("  )")
print(len(stmts))
