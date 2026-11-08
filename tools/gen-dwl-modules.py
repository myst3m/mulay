#!/usr/bin/env python3
"""tools/dwl/ の DataWeave モジュール (mulay が持つ dw::test など) を src/mulay/dw/stdmods.clay の文字列にする。

  python3 tools/gen-dwl-modules.py > src/mulay/dw/stdmods.clay

モジュールの名前はパスから決める (tools/dwl/dw/test/Asserts.dwl は dw::test::Asserts)。docs/adr/111。
"""
import os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dwl")

def esc(s):
    out = []
    for c in s:
        if c == "\\": out.append("\\\\")
        elif c == '"': out.append('\\"')
        elif c == "\n": out.append("\\n")
        elif c == "\t": out.append("\\t")
        elif c == "\r": out.append("\\r")
        else: out.append(c)
    return "".join(out)

mods = []
for d, _, fs in os.walk(ROOT):
    for f in fs:
        if f.endswith(".dwl"):
            p = os.path.join(d, f)
            rel = os.path.relpath(p, ROOT)[:-4]
            mods.append((rel.replace(os.sep, "::"), open(p, encoding="utf-8").read()))
mods.sort()
o = ["(ns mulay.dw.stdmods)", "", "(def MODS: Vec(Vec(Str)) ["]
for n, src in mods:
    o.append('  ["%s"\n   "%s"]' % (n, esc(src)))
o.append("])")
o.append("")
o.append("(defn source Values(Str Bool) [m: &Str]")
o.append("  (loop [i 0] (if (>= i (count MODS)) (values \"\" false) (let [e (nth MODS i)] (if (= (nth e 0) m) (values (str (nth e 1)) true) (recur (+ i 1)))))))")
o.append("")
o.append("(defn std? Bool [m: &Str] (let [[s found] (source m)] found))")
sys.stdout.write("\n".join(o) + "\n")
