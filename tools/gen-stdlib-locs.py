#!/usr/bin/env python3
"""DataWeave の標準ライブラリの native 関数の位置を、実 Mule 同梱の .dwl ソースから作る。

  python3 tools/gen-stdlib-locs.py [mulay のルート]

.dwl は $MULE_ORACLE_HOME (既定 ~/srv/mule-enterprise-standalone-4.11.3) の
services/mule-service-weave-ee-2.11.2/lib/wlang-2.11.2.jar から読む (読むだけ)。

出力: src/mulay/dw/stdlib_locs.clay
  NATIVE-LOC   Map: "モジュール 名前" -> 宣言の順のオーバーロードごとの [index line column endIndex endLine endColumn]
               (本体の native(...) の位置。index は 0 から、line と column は 1 から、end は直後。native でなければ [])
  NATIVE-TEXT  Map: "モジュール 名前" -> オーバーロードごとの宣言の行 (native でなければ "")
実 DW の location(f) と、native の関数の中で起きた失敗の try の error.location / stack に使う。
"""
import os
import re
import sys
import zipfile


def line_col(src, i):
    line = src.count("\n", 0, i) + 1
    ls = src.rfind("\n", 0, i) + 1
    return line, i - ls + 1


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    home = os.environ.get("MULE_ORACLE_HOME", os.path.expanduser("~/srv/mule-enterprise-standalone-4.11.3"))
    jar = os.path.join(home, "services/mule-service-weave-ee-2.11.2/lib/wlang-2.11.2.jar")
    locs, texts = {}, {}
    with zipfile.ZipFile(jar) as z:
        for n in sorted(z.namelist()):
            if not (n.startswith("dw/") and n.endswith(".dwl")):
                continue
            module = n[:-4].replace("/", "::")
            src = z.read(n).decode("utf-8")
            for m in re.finditer(r"(?m)^fun\s+([A-Za-z_][A-Za-z0-9_]*|`[^`]+`|\+\+|--)", src):
                name = m.group(1).strip("`")
                key = module + " " + name
                ls = m.start()
                le = src.find("\n", ls)
                le = len(src) if le < 0 else le
                line_text = src[ls:le]
                # 本体が同じ行の native("...") のものだけ
                nm = re.search(r"=\s*(native\(\"[^\"]*\"\))\s*$", line_text)
                if nm:
                    s = ls + nm.start(1)
                    e = ls + nm.end(1)
                    l1, c1 = line_col(src, s)
                    l2, c2 = line_col(src, e)
                    locs.setdefault(key, []).append([s, l1, c1, e, l2, c2])
                    texts.setdefault(key, []).append(line_text)
                else:
                    locs.setdefault(key, []).append([])
                    texts.setdefault(key, []).append("")

    def lit(s):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

    out = ["(ns mulay.dw.stdlib_locs)\n",
           "(def NATIVE-LOC: Map(Str Vec(Vec(Int)))\n  {" + "\n   ".join(
               lit(k) + " [" + " ".join("[" + " ".join(str(x) for x in e) + "]" for e in v) + "]"
               for k, v in sorted(locs.items())) + "})\n",
           "(def NATIVE-TEXT: Map(Str Vec(Str))\n  {" + "\n   ".join(
               lit(k) + " [" + " ".join(lit(x) for x in v) + "]" for k, v in sorted(texts.items())) + "})"]
    open(os.path.join(root, "src/mulay/dw/stdlib_locs.clay"), "w", encoding="utf-8").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
