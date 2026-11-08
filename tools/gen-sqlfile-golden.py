#!/usr/bin/env python3
# SQLite のファイル形式の読み取り (mulay.lib.sqlfile) の golden を作る。Python の sqlite3 (SQLite 3.53.4) で .db を作り、
# test/sqlfile/fixtures/ に置き、中身の要約 (下の dump の SHA-256) を test/sqlfile/file_test.clay に書く。
# 使い方: python3 -I tools/gen-sqlfile-golden.py   (リポジトリの根で)
import hashlib, os, sqlite3, struct

OUT = "test/sqlfile/fixtures"
os.makedirs(OUT, exist_ok=True)

def pat(n, m, a):
    return bytes((i * m + a) % 256 for i in range(n))

# 値を 1 つの文字列に: N、I:10 進、R:double のビット (16 桁の 16 進)、T:16 進、B:16 進。行は rowid と値を | でつなぐ
def enc(v):
    if v is None: return "N"
    if isinstance(v, int): return "I:%d" % v
    if isinstance(v, float): return "R:%016x" % struct.unpack(">Q", struct.pack(">d", v))[0]
    if isinstance(v, str): return "T:" + v.encode().hex()
    return "B:" + bytes(v).hex()

def make(name, page_size, setup):
    path = os.path.join(OUT, name)
    if os.path.exists(path): os.remove(path)
    c = sqlite3.connect(path)
    c.execute("PRAGMA page_size=%d" % page_size)
    c.execute("PRAGMA journal_mode=DELETE")
    setup(c)
    c.commit()
    c.close()
    return path

# cols: 選ぶ列 (rowid の別名の INTEGER PRIMARY KEY の列は、ファイルの record では NULL なので NULL と書く)
def rows_dump(path, table, cols="*"):
    c = sqlite3.connect(path)
    out = []
    for r in c.execute("SELECT rowid, %s FROM %s ORDER BY rowid" % (cols, table)):
        out.append("|".join([str(r[0])] + [enc(v) for v in r[1:]]))
    c.close()
    return "\n".join(out)

def index_dump(path, sql):
    c = sqlite3.connect(path)
    out = ["|".join(enc(v) for v in r) for r in c.execute(sql)]
    c.close()
    return "\n".join(out)

def sha(s): return hashlib.sha256(s.encode()).hexdigest()

def types(c):
    c.execute("CREATE TABLE t (a, b)")
    vals = [None, 0, 1, -1, 127, 128, -129, 32767, 32768, 8388607, 8388608, 2**31 - 1, 2**31, 2**47, 2**63 - 1, -2**63,
            1.5, -0.0, 1e300, -2.5e-300, "", "abc", "日本語", b"", pat(5, 3, 1)]
    for i, v in enumerate(vals):
        c.execute("INSERT INTO t VALUES (?, ?)", (v, i))

def many(c):
    c.execute("CREATE TABLE m (id INTEGER PRIMARY KEY, name TEXT, n INT)")
    c.execute("CREATE INDEX m_name ON m (name)")
    for i in range(1500):
        c.execute("INSERT INTO m VALUES (?, ?, ?)", (i * 7 + 1, "name-%05d-%s" % ((i * 37) % 1500, "x" * (i % 40)), i * i))

def big(c):
    c.execute("CREATE TABLE b (k TEXT, v BLOB)")
    c.execute("CREATE INDEX b_k ON b (k)")
    for i, n in enumerate([10, 600, 5000, 70000]):
        c.execute("INSERT INTO b VALUES (?, ?)", ("k%d-" % i + "y" * (n // 4), pat(n, 13, i)))

def worowid(c):
    c.execute("CREATE TABLE w (a TEXT, b INT, PRIMARY KEY (a, b)) WITHOUT ROWID")
    for i in range(500):
        c.execute("INSERT INTO w VALUES (?, ?)", ("w%04d" % (i * 13 % 500), i))

cases = []
p = make("types.db", 4096, types); cases.append(("types", p, "t", rows_dump(p, "t")))
p = make("many.db", 1024, many); cases.append(("many", p, "m", rows_dump(p, "m", "NULL, name, n")))
p = make("big.db", 512, big); cases.append(("big", p, "b", rows_dump(p, "b")))
p = make("big64k.db", 65536, big); cases.append(("big64k", p, "b", rows_dump(p, "b")))
p = make("worowid.db", 1024, worowid)

idx_many = index_dump(os.path.join(OUT, "many.db"), "SELECT name, id FROM m ORDER BY name, id")
idx_big = index_dump(os.path.join(OUT, "big.db"), "SELECT k, rowid FROM b ORDER BY k, rowid")
wr = index_dump(os.path.join(OUT, "worowid.db"), "SELECT a, b FROM w ORDER BY a, b")

def schema_dump(path):
    c = sqlite3.connect(path)
    out = ["|".join([t, n, tn, str(r), sql or ""]) for (t, n, tn, r, sql) in c.execute("SELECT type, name, tbl_name, rootpage, sql FROM sqlite_schema ORDER BY rowid")]
    c.close()
    return "\n".join(out)

def rootpage(path, name):
    c = sqlite3.connect(path)
    r = c.execute("SELECT rootpage FROM sqlite_schema WHERE name = ?", (name,)).fetchone()[0]
    c.close()
    return r

def rowcount(dump): return 0 if dump == "" else dump.count("\n") + 1

with open("test/sqlfile/file_test.clay", "w") as f:
    w = lambda s="": f.write(s + "\n")
    w(";; tools/gen-sqlfile-golden.py で作った (手で直さない)。fixtures/*.db は Python の sqlite3 (SQLite %s) が書いたもの。" % sqlite3.sqlite_version)
    w(";; 中身を dump (行は rowid と値を | でつなぎ、値は N / I:10 進 / R:double のビット / T:16 進 / B:16 進) にして SHA-256 で比べる")
    w("(ns file-test (:require [mulay.lib.sqlfile :as sf] [mulay.lib.hash :as hash] [mulay.lib.ieee :as ieee] [mulay.dw.lib.binaries :as bin]))")
    w()
    w("(defn- enc Str [v: &sf/Val]")
    w("  (match v")
    w('    (sf/VNull) "N"')
    w('    (sf/VInt n) (str "I:" n)')
    w('    (sf/VReal x) (let [h (bin/hex-lower (bytes-be (ieee/double->bits x)))] (str "R:" h))')
    w('    (sf/VText s) (str "T:" (bin/hex-lower s))')
    w('    (sf/VBlob s) (str "B:" (bin/hex-lower s))))')
    w()
    w("(defn- bytes-be Str [n: Int] (loop [i 0 out \"\"] (if (>= i 8) out (recur (+ i 1) (str out (chr (bit-and (unsigned-bit-shift-right n (* 8 (- 7 i))) 255)))))))")
    w()
    w("(defn- vals-str Str [vs: &Vec(sf/Val)]")
    w("  (loop [i 0 out \"\"] (if (>= i (count vs)) out (let [e (enc (nth vs i))] (recur (+ i 1) (if (= i 0) e (str out \"|\" e)))))))")
    w()
    w("(defn- rows-dump Str [rows: &Vec(sf/Row)]")
    w("  (loop [i 0 out \"\"]")
    w("    (if (>= i (count rows)) out")
    w("      (let [r (nth rows i) line (str (:rowid r) (if (> (count (:vals r)) 0) \"|\" \"\") (vals-str (:vals r)))]")
    w("        (recur (+ i 1) (if (= i 0) line (str out \"\\n\" line)))))))")
    w()
    w("(defn- keys-dump Str [ks: &Vec(Vec(sf/Val))]")
    w("  (loop [i 0 out \"\"] (if (>= i (count ks)) out (let [line (vals-str (nth ks i))] (recur (+ i 1) (if (= i 0) line (str out \"\\n\" line)))))))")
    w()
    w("(defn- sha Str [s: &Str] (bin/hex-lower (hash/sha256 s)))")
    w()
    w("(defn- db Sf [name: Str] (let [[d e] (read-file (str \"test/sqlfile/fixtures/\" name)) [x e2] (sf/open-bytes d)] x))".replace("Sf", "sf/Db"))
    w()
    w("(defn- table Str [name: Str root: Int] (let [[rows e] (sf/table-rows (db name) root)] (if (= e \"\") (sha (rows-dump rows)) e)))")
    w("(defn- table-n Int [name: Str root: Int] (let [[rows e] (sf/table-rows (db name) root)] (count rows)))")
    w("(defn- index Str [name: Str root: Int] (let [[ks e] (sf/index-keys (db name) root)] (if (= e \"\") (sha (keys-dump ks)) e)))")
    w()
    w(";; rowid の表: 格納型の全部 (整数の各幅、0 と 1 の定数、double、空の TEXT と BLOB)、内部のページのある表、overflow の連なり")
    w(";; (ページ 512 バイトと 64 KB)")
    w("(deftest tables")
    for (name, path, t, dump) in cases:
        w('  (is (= (table "%s" %d) "%s"))' % (os.path.basename(path), rootpage(path, t), sha(dump)))
        w('  (is (= (table-n "%s" %d) %d))' % (os.path.basename(path), rootpage(path, t), rowcount(dump)))
    w("  )")
    w()
    w(";; 索引 (内部のページのセルもキーを持つ) と WITHOUT ROWID の表")
    w("(deftest indexes")
    w('  (is (= (index "many.db" %d) "%s"))' % (rootpage(os.path.join(OUT, "many.db"), "m_name"), sha(idx_many)))
    w('  (is (= (index "big.db" %d) "%s"))' % (rootpage(os.path.join(OUT, "big.db"), "b_k"), sha(idx_big)))
    w('  (is (= (index "worowid.db" %d) "%s")))' % (rootpage(os.path.join(OUT, "worowid.db"), "w"), sha(wr)))
    w()
    w(";; sqlite_schema の行")
    w("(deftest schema")
    w("  (let [[rows e] (sf/schema (db \"many.db\"))")
    w("        s (loop [i 0 out \"\"] (if (>= i (count rows)) out")
    w("            (let [r (nth rows i) line (str (:type r) \"|\" (:name r) \"|\" (:tbl-name r) \"|\" (:root r) \"|\" (:sql r))]")
    w("              (recur (+ i 1) (if (= i 0) line (str out \"\\n\" line))))))]")
    w("    (is (= e \"\"))")
    w('    (is (= (sha s) "%s"))))' % sha(schema_dump(os.path.join(OUT, "many.db"))))
