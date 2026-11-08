#!/usr/bin/env python3
# mulay.lib.sqlexec (式の評価) の差分テストを作り、test/sql/eval_test.clay に書く。式を組み合わせで作り、tools/sqlite-oracle
# (実 Mule と同じ sqlite-jdbc 3.50.3.0) の答え (値と格納型、または errmsg) を期待値にする。
# 使い方: python3 -I tools/gen-sqleval-golden.py  (リポジトリの根で)
import random, subprocess

random.seed(311)
ATOMS = ["NULL", "0", "1", "-1", "2", "3", "7", "-7", "9223372036854775807", "-9223372036854775808", "4294967296",
         "0.5", "-1.5", "1.0", "0.0", "-0.0", "1e300", "2.5e-10", "9007199254740993", "0x10", "0xffffffffffffffff",
         "''", "'abc'", "'ABC'", "'12'", "' 12 '", "'1.5'", "'1e3'", "'12abc'", "'x1'", "'0x10'", "'a '", "'-3'",
         "X''", "X'00ff'", "X'3132'", "TRUE", "FALSE", "'9223372036854775808'", "'1.0'"]
BIN = ["+", "-", "*", "/", "%", "||", "&", "|", "<<", ">>", "=", "==", "!=", "<>", "<", "<=", ">", ">=", "IS", "IS NOT",
       "AND", "OR"]
CASTS = ["INTEGER", "INT", "REAL", "TEXT", "BLOB", "NUMERIC", "VARCHAR(10)", "FLOAT", "BOOLEAN", "DOUBLE PRECISION",
         "BIGINT", "CHARINT", "STRING", "DECIMAL(10,2)"]

exprs = []
for a in ATOMS:
    for op in ["-", "+", "~", "NOT "]:
        exprs.append(op + a)
    for t in CASTS:
        exprs.append("CAST(%s AS %s)" % (a, t))
    exprs.append("%s IS NULL" % a)
    exprs.append("%s NOTNULL" % a)
    exprs.append("%s NOT NULL" % a)
for op in BIN:
    for i in range(140):
        a, b = random.choice(ATOMS), random.choice(ATOMS)
        exprs.append("%s %s %s" % (a, op, b))
for i in range(300):
    a, b, c = random.choice(ATOMS), random.choice(ATOMS), random.choice(ATOMS)
    k = random.randint(0, 7)
    if k == 0: exprs.append("%s BETWEEN %s AND %s" % (a, b, c))
    elif k == 1: exprs.append("%s NOT BETWEEN %s AND %s" % (a, b, c))
    elif k == 2: exprs.append("%s IN (%s, %s)" % (a, b, c))
    elif k == 3: exprs.append("%s NOT IN (%s, %s, NULL)" % (a, b, c))
    elif k == 4: exprs.append("CASE %s WHEN %s THEN 'w' ELSE 'e' END" % (a, b))
    elif k == 5: exprs.append("CASE WHEN %s THEN %s ELSE %s END" % (a, b, c))
    elif k == 6: exprs.append("CAST(%s AS INTEGER) = %s" % (a, b))
    else: exprs.append("CAST(%s AS TEXT) < %s" % (a, b))
# 優先順位と結合、照合順序、構文の誤り
exprs += ["1 + 2 * 3", "(1 + 2) * 3", "2 - 3 - 4", "8 / 2 / 2", "1 || 2 + 3", "- - 1", "-9223372036854775808 - 1",
          "9223372036854775807 + 1", "-9223372036854775807 - 2", "9223372036854775807 * 2", "-9223372036854775808 / -1",
          "-9223372036854775808 % -1", "1 < 2 = 1", "NOT 1 = 2", "1 = 1 AND NULL", "0 AND NULL", "NULL OR 1", "1 << 63",
          "1 << 64", "-1 >> 70", "-8 >> 1", "1 << -1", "~0", "5 % -3", "-5 % 3", "5.5 % 2", "1 / 0", "1.0 / 0", "1 % 0",
          "'abc' = 'ABC' COLLATE NOCASE", "'abc' COLLATE NOCASE = 'ABC'", "'a ' = 'a' COLLATE RTRIM", "'b' < 'a' COLLATE NOCASE",
          "x'41' = 'A'", "1 = '1'", "1 = CAST('1' AS INTEGER)", "CAST(1 AS TEXT) = 1", "CAST('1' AS NUMERIC) = '1'",
          "1 IN ()", "NULL IN ()", "NULL NOT IN ()", "1 IN (NULL)", "1 IN (1, NULL)", "2 IN (1, NULL)",
          "1 IS NOT DISTINCT FROM 1", "1 IS DISTINCT FROM NULL", "NULL IS NULL", "1 ISNULL", "CASE 1 WHEN 2 THEN 3 END",
          "1 +", "(1", "1 2", "!", "'abc", "0x", "1_000", "1__0", "1_", "0xffffffffffffffffff", "-0x8000000000000000",
          "0x8000000000000000", "-0x7fffffffffffffff", "x", "\"abc\"", "[abc]", "`abc`", "\"a\" || 'b'", "12abc", "1e", "1e+",
          ".5", "5.", "1.5e3", "1e309", "-1e309", "99999999999999999999", "-99999999999999999999", "9223372036854775808",
          "-9223372036854775808", "-9223372036854775809", "00012", "0x00000000000000001", "?", "?2", ":a", "@b", "$c",
          "CAST(1 AS)", "CAST(1)", "CASE END", "CASE WHEN 1 THEN 2", "1 BETWEEN 2", "1 IN 2", "1 NOT 2", "NOT", "~", "--x\n1",
          "/* c */ 2", "1 /* x", "'it''s'", "x'0'", "x'zz'", "X'414'", "1 IS NOT", "1 IS DISTINCT 2", "TRUE + TRUE", "1 = TRUE",
          "1 COLLATE BINARY", "'a' COLLATE nocase < 'B'", "1.0 = 1", "1 = 1.0", "9007199254740993 = 9007199254740992.0",
          "9223372036854775807 = 9223372036854775807.0", "9223372036854775807 < 9223372036854775807.0", "-0.0 = 0",
          "'1.0' = 1.0", "CAST('1.0' AS REAL) = '1.0'", "'' = 0", "x'' = ''", "x'' < ''", "'' < x''", "1 < x''", "'z' < x'00'"]

q = "".join(e.replace("\n", " ") + "\n" if "--" not in e else e.replace("\n", " ").replace("--x", "/*x*/") + "\n" for e in exprs)
exprs = [l for l in q.split("\n")[:-1]]
out = subprocess.run(["tools/sqlite-oracle/sqlite-oracle"], input=q.encode(), capture_output=True, check=True).stdout.decode().split("\n")

def clay_str(t):
    return '"' + t.replace("\\", "\\\\").replace('"', '\\"').replace("\t", "\\t").replace("\n", "\\n") + '"'

with open("test/sql/eval_test.clay", "w") as f:
    w = lambda s="": f.write(s + "\n")
    w(";; tools/gen-sqleval-golden.py で作った (手で直さない)。期待値は sqlite-jdbc 3.50.3.0 (SQLite 3.50.3)。")
    w(";; 値は N / I:10 進 / R:double のビット / T:16 進 / B:16 進、失敗は E:errmsg")
    w("(ns eval-test (:require [mulay.lib.sqlparse :as sp] [mulay.lib.sqlexec :as ev] [mulay.lib.sqlfile :as sf] [mulay.lib.ieee :as ieee]")
    w("                         [mulay.dw.lib.binaries :as bin]))")
    w()
    w("(defn- hex64 Str [x: Int] (loop [i 0 out \"\"] (if (>= i 8) out (recur (+ i 1) (str out (chr (bit-and (unsigned-bit-shift-right x (* 8 (- 7 i))) 255)))))))")
    w("(defn- enc Str [v: &sf/Val]")
    w("  (match v")
    w('    (sf/VNull) "N"')
    w('    (sf/VInt n) (str "I:" n)')
    w('    (sf/VReal x) (str "R:" (bin/hex-lower (hex64 (ieee/double->bits x))))')
    w('    (sf/VText s) (str "T:" (bin/hex-lower s))')
    w('    (sf/VBlob s) (str "B:" (bin/hex-lower s))))')
    w("(defn- ev Str [sql: Str]")
    w("  (let [[n e] (sp/parse-expr sql)]")
    w("    (if (not= e \"\") (str \"E:\" e)")
    w("      (let [[v e2] (ev/eval-expr n (ev/empty-env))] (if (not= e2 \"\") (str \"E:\" e2) (enc v))))))")
    w()
    for i in range(0, len(exprs), 100):
        w("(deftest exprs-%d" % (i // 100))
        for j, e in enumerate(exprs[i:i + 100]):
            w("  (is (= (ev %s) %s))" % (clay_str(e), clay_str(out[i + j])))
        w("  )")
print(len(exprs))
