#!/usr/bin/env python3
# mulay.lib.sqlexec (文の実行) の差分テストを作り、test/sql/exec_test.clay に書く。台本 (文の並び) を同じ接続で順に実行し、
# 文ごとの結果を tools/sqlite-oracle script (実 Mule と同じ sqlite-jdbc 3.50.3.0) と比べる。
# 結果: Q:列の名前|..|;行の値 .. (値は N / I:10 進 / R:double のビット / T:16 進 / B:16 進)、C:changes:last_insert_rowid、
# E:拡張結果コード:errmsg
# 使い方: python3 -I tools/gen-sqlexec-golden.py  (リポジトリの根で)
import subprocess

PERSON = [
    "CREATE TABLE person (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, age INTEGER, score REAL, active BOOLEAN, born DATE, seen TIMESTAMP, note NUMERIC, big INTEGER, blob BLOB)",
    "INSERT INTO person (name, age, score, active, born, seen, note, big, blob) VALUES ('Ann', 30, 12.5, 1, '1996-01-02', '2026-09-30 10:11:12.345', '12.50', 9007199254740993, x'0102ff'), ('Bob', NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL), ('Cid', 41, 100, 1, '1985-12-31', '2026-01-01 00:00:00', 7, -5, x'')",
]
T = [
    "CREATE TABLE t (id INTEGER PRIMARY KEY, k INTEGER, name TEXT, v REAL)",
    "INSERT INTO t (k, name, v) VALUES (3, 'c', 1.5), (1, 'a', 2), (2, 'b', NULL), (1, 'A', 0.5), (NULL, 'z', 7), (2, 'b', 3)",
]
U = [
    "CREATE TABLE u (k INTEGER, label TEXT)",
    "INSERT INTO u VALUES (1, 'one'), (2, 'two'), (2, 'deux'), (4, 'four')",
]
scripts = [
    PERSON + [
        "SELECT id, name FROM person ORDER BY id", "SELECT * FROM person ORDER BY id",
        "UPDATE person SET age = age WHERE 1 = 0", "SELECT * FROM person WHERE id = 2",
        "UPDATE person SET age = age + 1 WHERE age IS NOT NULL", "DELETE FROM person WHERE name = 'Bob'",
        "INSERT INTO person (name, age) VALUES ('Dan', '52')", "SELECT count(*) AS n, max(age) AS oldest FROM person",
        "SELECT * FROM nothing_here", "INSERT INTO person (name) VALUES (NULL)", "SELECT * FROM person ORDER BY id",
        "SELECT name FROM person WHERE name LIKE 'a%' ORDER BY name", "SELECT seq FROM sqlite_sequence", "SELECT * FROM sqlite_sequence",
        "DROP TABLE person", "SELECT * FROM person", "DROP TABLE IF EXISTS person", "DROP TABLE person",
    ],
    ["CREATE TABLE bulk_t (id INTEGER PRIMARY KEY, name VARCHAR(20) NOT NULL, n INTEGER DEFAULT 0)",
     "INSERT INTO bulk_t (id, name) VALUES (30, 'a')", "INSERT INTO bulk_t (id, name) VALUES (31, 'b')", "INSERT INTO bulk_t (id, name) VALUES (30, 'c')",
     "UPDATE bulk_t SET n = n + 1 WHERE id >= 31", "SELECT id, name, n FROM bulk_t ORDER BY id", "DELETE FROM bulk_t WHERE id = 30",
     "SELECT COUNT(*) AS c FROM bulk_t WHERE id >= 30", "INSERT INTO no_such_table (id) VALUES (1)", "INSERT INTO bulk_t (id, name) VALUES ('x', 'y')",
     "INSERT INTO bulk_t (id, name) VALUES ('7', 'y')", "INSERT INTO bulk_t (id, name) VALUES (7.0, 'y2')", "INSERT INTO bulk_t VALUES (1)",
     "INSERT INTO bulk_t (id, nope) VALUES (1, 2)", "INSERT INTO bulk_t (name) VALUES ('auto')", "SELECT rowid, * FROM bulk_t", "SELECT oid, _rowid_ FROM bulk_t"],
    ["SELECT 1 AS a", "SELECT 2 AS a, 'x' b, 1 + 1, \"a\" || 'b'",
     "WITH RECURSIVE c(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM c WHERE n < 10) SELECT n FROM c",
     "WITH RECURSIVE c(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM c WHERE n < 3) SELECT n FROM c",
     "WITH RECURSIVE c(n) AS (SELECT 1 UNION SELECT n % 3 + 1 FROM c) SELECT n FROM c",
     "WITH a AS (SELECT 1 AS x UNION ALL SELECT 2), b(y) AS (SELECT x * 10 FROM a) SELECT * FROM a, b ORDER BY x, y",
     "WITH RECURSIVE c(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM c WHERE n < 5) SELECT sum(n), count(*) FROM c",
     "VALUES (1, 'a'), (2, 'b')", "VALUES (1), (2, 3)", "SELECT * FROM (VALUES (1), (2)) AS v", "SELECT 1 UNION SELECT 1 UNION ALL SELECT 2",
     "SELECT 3 UNION SELECT 1 UNION SELECT 2 ORDER BY 1 DESC", "SELECT 1 a UNION SELECT 2 ORDER BY a", "SELECT 1 INTERSECT SELECT 1", "SELECT 1 EXCEPT SELECT 1",
     "SELECT 1, 2 UNION SELECT 3", "SELECT 1 ORDER BY 2", "SELECT 1 UNION SELECT 2 ORDER BY 3", "SELECT nope", "SELECT max(1, 2), min(3)",
     "SELECT count(*)", "SELECT sum(1)", "SELECT 1 LIMIT 0", "SELECT 1 LIMIT 'x'", "SELECT * ", "SELECT t.*"],
    T + [
        "SELECT * FROM t", "SELECT * FROM t ORDER BY k", "SELECT * FROM t ORDER BY k DESC, name", "SELECT * FROM t ORDER BY k NULLS LAST, id DESC",
        "SELECT name FROM t ORDER BY name COLLATE NOCASE, id", "SELECT name FROM t ORDER BY name", "SELECT DISTINCT k FROM t ORDER BY k",
        "SELECT k, count(*), sum(v), avg(v), total(v), min(v), max(name), group_concat(name) FROM t GROUP BY k",
        "SELECT k, count(*) AS n FROM t GROUP BY k HAVING n > 1 ORDER BY n DESC, k", "SELECT k, count(*) FROM t GROUP BY 1",
        "SELECT k AS kk, count(*) FROM t GROUP BY kk", "SELECT count(*), count(v), count(k), sum(k) FROM t",
        "SELECT count(DISTINCT k), group_concat(DISTINCT k) FROM t", "SELECT group_concat(name, '-') FROM t", "SELECT string_agg(name, '') FROM t",
        "SELECT sum(v) FROM t WHERE 0", "SELECT total(v), avg(v), count(*), max(v) FROM t WHERE 0", "SELECT name FROM t WHERE k IN (1, 3) ORDER BY id",
        "SELECT name FROM t WHERE k BETWEEN 2 AND 3 ORDER BY id", "SELECT name FROM t WHERE v IS NULL", "SELECT * FROM t LIMIT 2", "SELECT * FROM t LIMIT 2 OFFSET 3",
        "SELECT * FROM t LIMIT 3, 2", "SELECT * FROM t LIMIT -1 OFFSET 4", "SELECT * FROM t ORDER BY id LIMIT 1 OFFSET 10", "SELECT k + 1 AS x FROM t ORDER BY x",
        "SELECT id FROM t ORDER BY -id", "SELECT name, k FROM t ORDER BY 2, 1", "SELECT nope FROM t", "SELECT t.nope FROM t", "SELECT x.id FROM t x WHERE x.k = 2",
        "SELECT x.id FROM t AS x WHERE t.k = 2", "SELECT count(*) FROM t WHERE count(*) > 1", "SELECT sum(sum(k)) FROM t",
        "SELECT k, name FROM t GROUP BY k ORDER BY k", "SELECT max(v), name FROM t", "SELECT min(v), name FROM t", "SELECT name, count(*) FROM t",
        "SELECT (SELECT max(k) FROM t), (SELECT name FROM t WHERE k = 99)", "SELECT name FROM t WHERE k = (SELECT min(k) FROM t) ORDER BY id",
        "SELECT name FROM t WHERE k IN (SELECT k FROM t WHERE v > 1) ORDER BY id", "SELECT name FROM t WHERE k NOT IN (SELECT k FROM t WHERE k > 1)",
        "SELECT name FROM t a WHERE EXISTS (SELECT 1 FROM t b WHERE b.k = a.k AND b.id <> a.id) ORDER BY id",
        "SELECT name, (SELECT count(*) FROM t b WHERE b.k = a.k) FROM t a ORDER BY id", "SELECT * FROM (SELECT k, count(*) AS n FROM t GROUP BY k) WHERE n > 1",
        "SELECT sub.name FROM (SELECT * FROM t WHERE k = 1) sub ORDER BY sub.id",
        "UPDATE t SET v = v * 2 WHERE k = 1", "SELECT id, v FROM t", "UPDATE t SET id = id + 100 WHERE id = 1", "SELECT id, name FROM t ORDER BY id",
        "UPDATE t SET id = 2 WHERE id = 3", "UPDATE t SET k = 'x', v = '1e2' WHERE name = 'z'", "SELECT k, typeof(k), v, typeof(v) FROM t WHERE name = 'z'",
        "UPDATE t SET nope = 1", "DELETE FROM t WHERE k IS NULL", "DELETE FROM t WHERE nope = 1", "SELECT count(*) FROM t", "DELETE FROM t", "SELECT * FROM t",
        "INSERT INTO t (k) VALUES (1)", "SELECT id FROM t",
    ],
    T + U + [
        "SELECT t.name, u.label FROM t JOIN u ON t.k = u.k ORDER BY t.id, u.label", "SELECT t.name, u.label FROM t LEFT JOIN u ON t.k = u.k ORDER BY t.id, u.label",
        "SELECT * FROM t JOIN u USING (k) ORDER BY id, label", "SELECT * FROM t NATURAL JOIN u ORDER BY id, label", "SELECT k FROM t JOIN u ON t.k = u.k",
        "SELECT count(*) FROM t, u", "SELECT count(*) FROM t CROSS JOIN u WHERE t.k = u.k", "SELECT t.k, u.* FROM t LEFT OUTER JOIN u ON u.k = t.k AND u.label <> 'two' ORDER BY t.id, u.label",
        "SELECT u.label, count(t.id) FROM u LEFT JOIN t ON t.k = u.k GROUP BY u.label ORDER BY u.label", "SELECT * FROM t JOIN nope ON 1",
        "SELECT a.name, b.name FROM t a JOIN t b ON a.k = b.k AND a.id < b.id ORDER BY a.id, b.id",
    ],
    ["CREATE TABLE c (a INTEGER PRIMARY KEY, b TEXT UNIQUE, c INTEGER CHECK (c > 0), d TEXT NOT NULL DEFAULT 'dd', e REAL DEFAULT -1, f DEFAULT (1 + 2))",
     "INSERT INTO c (a, b, c) VALUES (1, 'x', 5)", "SELECT * FROM c", "INSERT INTO c (b, c) VALUES ('x', 1)", "INSERT INTO c (b, c) VALUES ('y', 0)",
     "INSERT INTO c (b, c) VALUES (NULL, NULL)", "INSERT INTO c (b, c) VALUES (NULL, 3)", "INSERT INTO c (b, d) VALUES ('z', NULL)",
     "INSERT OR IGNORE INTO c (b, c) VALUES ('x', 9)", "INSERT OR REPLACE INTO c (b, c) VALUES ('x', 9)", "SELECT * FROM c ORDER BY a",
     "REPLACE INTO c (a, b) VALUES (2, 'w')", "SELECT * FROM c ORDER BY a", "INSERT INTO c (a) VALUES (2)", "UPDATE c SET b = 'w' WHERE a = 4",
     "UPDATE OR IGNORE c SET b = 'w'", "SELECT * FROM c ORDER BY a", "UPDATE c SET c = -1", "UPDATE c SET d = NULL WHERE a = 2", "INSERT INTO c DEFAULT VALUES", "SELECT * FROM c ORDER BY a",
     "CREATE TABLE c (z)", "CREATE TABLE IF NOT EXISTS c (z)", "CREATE TABLE sqlite_x (a)", "SELECT type, name, tbl_name, sql FROM sqlite_schema ORDER BY name",
     "CREATE TABLE p (a, b, PRIMARY KEY (a, b))", "INSERT INTO p VALUES (1, 2)", "INSERT INTO p VALUES (1, 2)", "INSERT INTO p VALUES (1, NULL)", "INSERT INTO p VALUES (1, NULL)",
     "SELECT rowid, * FROM p", "SELECT name FROM sqlite_master ORDER BY name"],
    ["CREATE TABLE ix (a INTEGER, b TEXT COLLATE NOCASE)", "CREATE INDEX ix_a ON ix (a)", "CREATE UNIQUE INDEX ix_b ON ix (b)", "INSERT INTO ix VALUES (1, 'Hello')",
     "INSERT INTO ix VALUES (2, 'HELLO')", "INSERT INTO ix VALUES (2, 'other')", "SELECT * FROM ix WHERE a = 2", "CREATE INDEX ix_a ON ix (b)", "CREATE INDEX IF NOT EXISTS ix_a ON ix (b)",
     "CREATE INDEX ix_c ON ix (nope)", "CREATE INDEX ix_d ON nope (a)", "CREATE UNIQUE INDEX ix_u ON ix (a)", "DROP INDEX ix_a", "DROP INDEX ix_a", "DROP INDEX IF EXISTS ix_a",
     "SELECT name FROM sqlite_schema ORDER BY name", "SELECT b FROM ix ORDER BY b", "SELECT b = 'hello' FROM ix ORDER BY a", "SELECT DISTINCT b FROM ix",
     "CREATE TABLE q (a TEXT UNIQUE)", "DROP INDEX sqlite_autoindex_q_1"],
    ["CREATE TABLE lk (id INTEGER PRIMARY KEY, k INTEGER, s TEXT COLLATE NOCASE, r REAL, u)", "CREATE INDEX lk_k ON lk (k)", "CREATE INDEX lk_s ON lk (s)",
     "CREATE INDEX lk_r ON lk (r)", "CREATE INDEX lk_u ON lk (u COLLATE NOCASE)",
     "INSERT INTO lk (k, s, r, u) VALUES (3, 'Abc', 1.0, 'X'), (1, 'abc', 2.5, 'x'), (3, 'b', 1, 'y'), (NULL, NULL, NULL, NULL), ('3', 'ABC', '1', 'X'), (2, 'c', 3, 'Y')",
     "SELECT id FROM lk WHERE k = 3", "SELECT id FROM lk WHERE k = '3'", "SELECT id FROM lk WHERE 3 = k", "SELECT id FROM lk WHERE k = 3.0", "SELECT id FROM lk WHERE k = NULL",
     "SELECT id FROM lk WHERE k = 3 AND s = 'b'", "SELECT id FROM lk WHERE s = 'abc'", "SELECT id FROM lk WHERE s = 'ABC' COLLATE BINARY", "SELECT id FROM lk WHERE r = 1",
     "SELECT id FROM lk WHERE r = '1'", "SELECT id FROM lk WHERE u = 'x'", "SELECT id FROM lk WHERE u = 'X' AND k = 3", "SELECT id, k FROM lk WHERE id = 3", "SELECT id FROM lk WHERE id = '3'",
     "SELECT id FROM lk WHERE rowid = 2.0", "SELECT id FROM lk WHERE id = 'x'", "SELECT id FROM lk WHERE k = 1 + 2", "SELECT id FROM lk WHERE k = abs(-3)", "SELECT id FROM lk WHERE k = 99",
     "UPDATE lk SET k = 7 WHERE k = 3", "SELECT id, k FROM lk WHERE k = 7", "DELETE FROM lk WHERE k = 7", "SELECT id FROM lk ORDER BY id", "SELECT count(*) FROM lk WHERE k = 2 OR k = 1"],
    ["CREATE TABLE tx (a)", "BEGIN", "INSERT INTO tx VALUES (1)", "INSERT INTO tx VALUES (2)", "SELECT * FROM tx", "ROLLBACK", "SELECT * FROM tx",
     "BEGIN TRANSACTION", "INSERT INTO tx VALUES (3)", "BEGIN", "COMMIT", "SELECT * FROM tx", "COMMIT", "ROLLBACK", "END",
     "BEGIN", "CREATE TABLE tx2 (b)", "ROLLBACK", "SELECT * FROM tx2", "INSERT INTO tx SELECT a + 10 FROM tx", "SELECT * FROM tx", "INSERT INTO tx (a) SELECT 1, 2",
     "SELECT changes(), total_changes(), last_insert_rowid()"],
    ["CREATE TABLE s (i INTEGER, r REAL)", "INSERT INTO s VALUES (9223372036854775807, 0.1), (1, 0.2), (NULL, 0.3)", "SELECT sum(i) FROM s", "SELECT total(i), avg(i) FROM s",
     "SELECT sum(r), avg(r), total(r) FROM s", "INSERT INTO s VALUES (-9223372036854775807, 1e308), (-3, 1e308)", "SELECT sum(i), sum(r) FROM s",
     "SELECT sum(i) FROM s WHERE i > 0", "SELECT sum(i) FROM s WHERE i < 9223372036854775807", "SELECT sum('3'), sum('x'), sum(x'31') FROM s WHERE i = 1",
     "SELECT max(i), min(i), max(r), min(r) FROM s", "SELECT r FROM s ORDER BY r", "SELECT i, r FROM s ORDER BY i DESC NULLS FIRST"],
    ["CREATE TABLE r (a INTEGER PRIMARY KEY, b TEXT UNIQUE, c INTEGER)", "CREATE INDEX r_c ON r (c)", "INSERT INTO r VALUES (1, 'x', 1), (2, 'y', 2), (3, 'z', 3)",
     "UPDATE r SET a = a + 10 WHERE a = 1", "SELECT * FROM r ORDER BY a", "UPDATE OR IGNORE r SET a = 3 WHERE a = 2", "SELECT * FROM r ORDER BY a",
     "UPDATE OR IGNORE r SET a = 20, b = 'z' WHERE a = 2", "SELECT * FROM r ORDER BY a", "UPDATE r SET a = 3 WHERE a = 2", "UPDATE r SET b = 'z' WHERE a = 2",
     "SELECT * FROM r ORDER BY a", "UPDATE OR REPLACE r SET a = 3, c = 9 WHERE a = 2", "SELECT * FROM r ORDER BY a",
     "UPDATE OR REPLACE r SET b = 'x' WHERE a = 3", "SELECT * FROM r ORDER BY a", "INSERT INTO r VALUES (5, 'p', 5), (6, 'q', 6)",
     "UPDATE r SET b = b, a = a", "SELECT * FROM r ORDER BY a", "UPDATE OR IGNORE r SET a = a + 1", "SELECT * FROM r ORDER BY a",
     "SELECT a FROM r WHERE c = 9", "SELECT a FROM r WHERE b = 'x'", "SELECT a FROM r WHERE b = 'y'"],
    ["CREATE TABLE z (a INTEGER PRIMARY KEY, b, c)", "INSERT INTO z VALUES (-1, 'd', 1), (2, 'd', 2), (-2, 'e', 3)", "CREATE UNIQUE INDEX zb ON z (b)",
     "SELECT name FROM sqlite_schema WHERE type = 'index'", "CREATE UNIQUE INDEX zc ON z (c)", "INSERT INTO z VALUES (3, 'f', 1)", "INSERT OR IGNORE INTO z VALUES (4, 'g', 3)",
     "UPDATE z SET c = 3 WHERE a = 2", "UPDATE z SET c = 3 WHERE a = -2", "UPDATE z SET a = -3 WHERE a = -1", "SELECT * FROM z ORDER BY a"],
]
q = "".join("".join(s + "\n" for s in sc) + "----\n" for sc in scripts)
out = subprocess.run(["tools/sqlite-oracle/sqlite-oracle", "script"], input=q.encode(), capture_output=True, check=True).stdout.decode().split("\n")

def clay_str(t):
    return '"' + t.replace("\\", "\\\\").replace('"', '\\"') + '"'

with open("test/sql/exec_test.clay", "w") as f:
    w = lambda s="": f.write(s + "\n")
    w(";; tools/gen-sqlexec-golden.py で作った (手で直さない)。期待値は sqlite-jdbc 3.50.3.0 (SQLite 3.50.3) で同じ台本を実行した結果")
    w(";; Q:列の名前|..|;行の値 .. / C:changes:last_insert_rowid / E:拡張結果コード:errmsg")
    w("(ns exec-test (:require [mulay.lib.sqlparse :as sp] [mulay.lib.sqlexec :as ex] [mulay.lib.sqlfile :as sf] [mulay.lib.ieee :as ieee]")
    w("                         [mulay.dw.lib.binaries :as bin]))")
    w()
    w("(defn- hex64 Str [x: Int] (loop [i 0 out \"\"] (if (>= i 8) out (recur (+ i 1) (str out (chr (bit-and (unsigned-bit-shift-right x (* 8 (- 7 i))) 255)))))))")
    w("(defn- enc Str [v: &sf/Val]")
    w("  (match v")
    w("    (sf/VNull) \"N\"")
    w("    (sf/VInt n) (str \"I:\" n)")
    w("    (sf/VReal x) (str \"R:\" (bin/hex-lower (hex64 (ieee/double->bits x))))")
    w("    (sf/VText s) (str \"T:\" (bin/hex-lower s))")
    w("    (sf/VBlob s) (str \"B:\" (bin/hex-lower s))))")
    w("(defn- enc-res Str [r: &ex/Res]")
    w("  (let [head (loop [i 0 out \"Q:\"] (if (>= i (count (:names r))) out (recur (+ i 1) (str out (nth (:names r) i) \"|\"))))]")
    w("    (loop [i 0 out head]")
    w("      (if (>= i (count (:rows r))) out")
    w("        (let [row (nth (:rows r) i)]")
    w("          (recur (+ i 1) (loop [k 0 o (str out \";\")] (if (>= k (count row)) o (let [e (enc (nth row k))] (recur (+ k 1) (if (= k 0) (str o e) (str o \" \" e))))))))))))")
    w("(defn- run Vec(Str) [stmts: Vec(Str)]")
    w("  (let [ps: Vec(sf/Val) [] ns: Vec(Str) []]")
    w("    (loop [i 0 db (ex/new-db 4096) cs (ex/new-conn-state) out: Vec(Str) []]")
    w("      (if (>= i (count stmts)) out")
    w("        (let [[st pe] (ex/prepare (nth stmts i))]")
    w("          (if (not= pe \"\") (recur (+ i 1) db cs (conj out (str \"E:1:\" pe)))")
    w("            (let [[db2 cs2 res code msg] (ex/exec-stmt db cs st ps ns ps)]")
    w("              (cond (not= code 0) (recur (+ i 1) db2 cs2 (conj out (str \"E:\" code \":\" msg)))")
    w("                    (:query res) (recur (+ i 1) db2 cs2 (conj out (enc-res res)))")
    w("                    :else (recur (+ i 1) db2 cs2 (conj out (str \"C:\" (:changes cs2) \":\" (:last-rowid cs2))))))))))))")
    w()
    k = 0
    for si, sc in enumerate(scripts):
        res = out[k:k + len(sc)]
        assert out[k + len(sc)] == "----"
        k += len(sc) + 1
        w("(deftest script-%d" % si)
        w("  (let [r (run [%s])]" % "\n                 ".join(clay_str(s) for s in sc))
        for j, (s, e) in enumerate(zip(sc, res)):
            w("    (is (= (str \"%d \" (nth r %d)) %s))" % (j, j, clay_str("%d " % j + e)))
        w("    ))")
print(sum(len(s) for s in scripts))
