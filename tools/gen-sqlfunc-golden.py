#!/usr/bin/env python3
# mulay.lib.sqlfunc (組み込みのスカラー関数、LIKE、GLOB) の差分テストを作り、test/sql/func_test.clay に書く。期待値は
# tools/sqlite-oracle (実 Mule と同じ sqlite-jdbc 3.50.3.0) の答え。式は gen-sqleval-golden.py と同じ形で書き出す。
# 使い方: python3 -I tools/gen-sqlfunc-golden.py  (リポジトリの根で)
import random, subprocess

random.seed(4242)
V = ["NULL", "0", "1", "-1", "2", "-3", "9223372036854775807", "-9223372036854775808", "0.5", "-1.5", "2.5", "-2.5",
     "1e300", "-0.0", "0.1", "123.456", "''", "'abc'", "'ABC'", "' a b '", "'12'", "'1.5'", "'-7x'", "'日本語'", "'aé'",
     "X''", "X'00ff'", "X'616263'", "'a''b'", "'%'", "'_'", "'xx'", "'0x10'", "'9e999'"]
F1 = ["abs", "length", "octet_length", "typeof", "lower", "upper", "hex", "quote", "unicode", "zeroblob", "sign",
      "ceil", "floor", "trunc", "sqrt", "exp", "ln", "log", "log10", "degrees", "radians", "sin", "cos", "tan",
      "likely", "unlikely", "round", "trim", "ltrim", "rtrim", "unhex", "unistr", "char"]
F2 = ["instr", "substr", "round", "trim", "ltrim", "rtrim", "nullif", "max", "min", "concat", "concat_ws", "coalesce",
      "ifnull", "iif", "pow", "log", "unhex", "like", "glob"]
exprs = []
for f in F1:
    for v in V:
        exprs.append("%s(%s)" % (f, v))
for f in F2:
    for i in range(45):
        exprs.append("%s(%s, %s)" % (f, random.choice(V), random.choice(V)))
for i in range(120):
    exprs.append("substr(%s, %s, %s)" % (random.choice(["'hello world'", "'日本語テキスト'", "X'0102030405'", "12345", "NULL"]),
                                         random.choice(["0", "1", "2", "-1", "-3", "10", "-10", "NULL", "'2'", "1.9"]),
                                         random.choice(["0", "1", "3", "-1", "-2", "100", "NULL", "-100"])))
    exprs.append("replace(%s, %s, %s)" % (random.choice(V), random.choice(V), random.choice(V)))
    exprs.append("round(%s, %s)" % (random.choice(["1.005", "2.675", "-1.5", "123.456789", "0.000123456", "1e20", "9.995", "-0.45", "1234567.891", "'1.25'", "5", "NULL"]),
                                    random.choice(["0", "1", "2", "3", "5", "10", "-1", "31", "NULL"])))
    exprs.append("max(%s, %s, %s)" % (random.choice(V), random.choice(V), random.choice(V)))
    exprs.append("concat_ws(%s, %s, %s, %s)" % (random.choice(["','", "''", "NULL", "1"]), random.choice(V), random.choice(V), random.choice(V)))
for x in ["0.1", "1e300", "-1.5", "1.0", "123456789012345678", "0.30000000000000004", "1.7976931348623157e308", "5e-324", "1e-7", "2.0e15"]:
    exprs.append("quote(%s)" % x)
    exprs.append("round(%s, 2)" % x)
STR = ["'abc'", "'ABC'", "'a'", "''", "'a%c'", "'a_c'", "'aXc'", "'日本'", "'ab\\c'", "'[a]'", "'a-b'", "'xyz'", "'abcabc'", "NULL", "123", "'1.5'"]
PAT = ["'abc'", "'a%'", "'%c'", "'%'", "'_'", "'a_c'", "'A%'", "'%b%'", "'a\\%c'", "'%%%'", "'_%_'", "''", "'日%'", "'%本'",
       "'a*'", "'*c'", "'[a-c]*'", "'[^a]*'", "'?b?'", "'[]]*'", "'*[abc]'", "'a[-]b'", "NULL", "'1%'"]
for i in range(260):
    s, p = random.choice(STR), random.choice(PAT)
    k = random.randint(0, 3)
    if k == 0: exprs.append("%s LIKE %s" % (s, p))
    elif k == 1: exprs.append("%s GLOB %s" % (s, p))
    elif k == 2: exprs.append("%s NOT LIKE %s" % (s, p))
    else: exprs.append("%s LIKE %s ESCAPE %s" % (s, p, random.choice(["'\\'", "'%'", "'_'", "'ab'", "''", "NULL", "'x'"])))
# 集約関数 (count(*) など) は FROM の無い SELECT でも 1 行を返すが、それは文の層で確かめる
exprs += ["abs(-9223372036854775808)", "abs()", "ABS(1, 2)", "foo(1)", "length()", "char()", "zeroblob(9223372036854775807)",
          "randomblob(2000000000)",
          "char(65, 0x1F600, -1, 1114112)", "unicode('')", "hex(NULL)", "hex(12)", "hex(1.5)", "zeroblob(-1)", "zeroblob(3)",
          "typeof(zeroblob(2))", "nullif(1, 1.0)", "nullif('a', 'A')", "nullif('a' COLLATE NOCASE, 'A')", "max('a', 'B' COLLATE NOCASE)",
          "min(1, '1', x'31')", "max(1, NULL, 3)", "coalesce(NULL, NULL, 3)", "coalesce(NULL, abs(-9223372036854775808))",
          "coalesce(1, abs(-9223372036854775808))", "iif(0, 1)", "iif(NULL, 1, 2)", "likelihood(1, 0.5)", "likelihood(1, 1)",
          "likelihood(1, 1.5)", "unistr('a\\u0041\\+01F600\\\\')", "unistr('\\x')", "unistr('\\u00')", "sqlite_version()",
          "typeof(random())", "typeof(randomblob(4))", "length(randomblob(0))", "pi()", "pow(2, 0.5)", "pow(-8, 1.0/3)",
          "log(2, 8)", "log(1, 8)", "log(-1)", "ln(0)", "sqrt(-1)", "exp(1000)", "trunc(-0.5)", "ceil('1.2')", "floor('x')",
          "round(-0.4)", "round(0.5)", "round(1e300, 2)", "round(-2.5, 0)", "quote('it''s')", "quote(X'00')", "quote('a' || char(0) || 'b')",
          "length('a' || char(0) || 'b')", "instr('abc', '')", "instr(X'0102', X'02')", "instr('ab', X'62')", "instr(NULL, 'a')",
          "trim('xxaxx', 'x')", "trim('  a  ')", "ltrim('aab', 'a')", "rtrim('baa', 'a')", "trim('日本日', '日')", "trim('abc', '')",
          "replace('aaa', 'a', 'bb')", "replace('abc', '', 'x')", "replace(123, 2, 9)", "replace(NULL, 'a', 'b')", "replace('a', 'a', NULL)",
          "upper('aé')", "lower('ÀB')", "concat()", "concat_ws(',')", "concat(NULL)", "concat(1, 2.5, x'41')", "log10(1000)",
          "'a' LIKE 'A'", "'é' LIKE 'É'", "'a' GLOB 'A'", "'abc' LIKE 'a%' ESCAPE 'a'", "'%' LIKE 'x%' ESCAPE 'x'",
          "'a' LIKE 'a' ESCAPE ''", "'x' LIKE NULL", "upper(1.5)", "typeof(upper(1))", "length(1.0)", "length(-0.0)", "length(X'00')"]

q = "".join(e + "\n" for e in exprs)
out = subprocess.run(["tools/sqlite-oracle/sqlite-oracle"], input=q.encode(), capture_output=True, check=True).stdout.decode().split("\n")

def clay_str(t):
    return '"' + t.replace("\\", "\\\\").replace('"', '\\"') + '"'

# 乱数の関数は型だけを確かめる
with open("test/sql/func_test.clay", "w") as f:
    w = lambda s="": f.write(s + "\n")
    w(";; tools/gen-sqlfunc-golden.py で作った (手で直さない)。期待値は sqlite-jdbc 3.50.3.0 (SQLite 3.50.3)。")
    w(";; 値は N / I:10 進 / R:double のビット / T:16 進 / B:16 進、失敗は E:errmsg")
    w("(ns func-test (:require [mulay.lib.sqlparse :as sp] [mulay.lib.sqlexec :as ev] [mulay.lib.sqlfile :as sf] [mulay.lib.ieee :as ieee]")
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
        w("(deftest funcs-%d" % (i // 100))
        for j, e in enumerate(exprs[i:i + 100]):
            o = out[i + j]
            if e.startswith("typeof(random") or e.startswith("typeof(randomblob") or e.startswith("length(randomblob"):
                pass
            w("  (is (= (ev %s) %s))" % (clay_str(e), clay_str(o)))
        w("  )")
print(len(exprs))
