#!/usr/bin/env python3
# mulay.lib.sqlnum (SQLite 3.50.3 と同じ数と文字列の変換) の golden を作り、test/sql/num_test.clay に書く。期待値は
# tools/sqlite-oracle (実 Mule と同じ sqlite-jdbc 3.50.3.0) の答え:
#   atof: CAST('<文字列>' AS REAL) の double のビット (前後の空白、後ろの余り、溢れる桁、大きな指数を含む)
#   real->text: CAST(CAST('<文字列>' AS REAL) AS TEXT)
# 使い方: python3 -I tools/gen-sqlnum-golden.py  (リポジトリの根で)
import random, struct, subprocess

random.seed(20261011)
texts = ["0", "1", "-1", "1.5", "  2.5  ", "12abc", "1e", "1e+", ".5", "5.", "-0", "-0.0", "0.1", "1e308", "1e309", "-1e309",
         "1e-320", "4.9e-324", "2e-324", "123456789012345678901234567890", "0.000000000000000000000000000001234",
         "18446744073709551615", "18446744073709551616", "9223372036854775807", "9223372036854775808",
         "1.7976931348623157e308", "1e10000", "1e-10000", "3.14159265358979323846264338327950288", "1e22", "1e23",
         "8.219597356351074e+174", "4.028792867998315e-156", "+7", "\t9\f", "1.0e0", "0x10", "abc", "", " ", "1.2.3", "1e5x",
         "100", "1000000000000000", "1e15", "1e16", "0.0001", "0.00001", "123.456e-7"]
for i in range(400):
    b = random.getrandbits(64)
    x = struct.unpack(">d", struct.pack(">Q", b))[0]
    if x != x or abs(x) == float("inf"): continue
    texts.append(repr(x))
for i in range(300):
    texts.append("%.*g" % (random.randint(1, 20), random.random() * 10 ** random.randint(-30, 30)))
for i in range(100):
    texts.append(str(random.getrandbits(random.randint(1, 80))) + "." + str(random.getrandbits(random.randint(1, 60))))

def sq(t): return "'" + t.replace("'", "''") + "'"
q = "".join("CAST(%s AS REAL)\nCAST(CAST(%s AS REAL) AS TEXT)\n" % (sq(t), sq(t)) for t in texts)
out = subprocess.run(["tools/sqlite-oracle/sqlite-oracle"], input=q.encode(), capture_output=True, check=True).stdout.decode().split("\n")

# Clay の文字列リテラル (エスケープは \n \t \r \" \\ だけ。他の制御文字は (chr n) でつなぐ)
def clay_str(t):
    parts, cur = [], ""
    for ch in t:
        if ch in "\\\"": cur += "\\" + ch
        elif ch == "\t": cur += "\\t"
        elif ord(ch) < 32:
            parts.append('"' + cur + '"'); parts.append("(chr %d)" % ord(ch)); cur = ""
        else: cur += ch
    parts.append('"' + cur + '"')
    return parts[0] if len(parts) == 1 else "(str " + " ".join(parts) + ")"

def expect_text(tx):
    return clay_str(bytes.fromhex(tx[2:]).decode()) if tx.startswith("T:") else clay_str(tx)

with open("test/sql/num_test.clay", "w") as f:
    w = lambda s="": f.write(s + "\n")
    w(";; tools/gen-sqlnum-golden.py で作った (手で直さない)。期待値は sqlite-jdbc 3.50.3.0 (SQLite 3.50.3)")
    w("(ns num-test (:require [mulay.lib.sqlnum :as n] [mulay.lib.ieee :as ieee] [mulay.dw.lib.binaries :as bin]))")
    w()
    w("(defn- hex64 Str [x: Int] (loop [i 0 out \"\"] (if (>= i 8) out (recur (+ i 1) (str out (chr (bit-and (unsigned-bit-shift-right x (* 8 (- 7 i))) 255)))))))")
    w("(defn- bits Str [s: Str] (let [[x k] (n/atof s)] (str \"R:\" (bin/hex-lower (hex64 (ieee/double->bits x))))))")
    w("(defn- text Str [s: Str] (let [[x k] (n/atof s)] (n/real->text x)))")
    w()
    for i in range(0, len(texts), 50):
        w("(deftest conv-%d" % (i // 50))
        for j, t in enumerate(texts[i:i + 50]):
            k = i + j
            r, tx = out[2 * k], out[2 * k + 1]
            w("  (is (= (bits %s) %s))" % (clay_str(t), clay_str(r)))
            w("  (is (= (text %s) %s))" % (clay_str(t), expect_text(tx)))
        w("  )")
