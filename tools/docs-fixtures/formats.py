#!/usr/bin/env python3
"""dataFormatsDescriptor() (実 DW 2.11.2) と docs-dataweave v2.11 の表から docs/dw-formats.md を作る。"""
import json, os, re, glob
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
S = os.path.dirname(os.path.abspath(__file__))
PAGES = f"{S}/dwdocs/modules/ROOT/pages"
DEST = os.path.join(ROOT, "docs/dw-formats.md")
raw = open(f"{S}/df.json").read().split("\n", 1)[1]
fmts, seen = [], set()
for f in json.loads(raw):
    if f["name"] not in seen:
        seen.add(f["name"]); fmts.append(f)

PAGE = {"dw": "dataweave-formats-dw", "urlencoded": "dataweave-formats-urlencoded"}

def doc_tables(name):
    p = f"{PAGES}/{PAGE.get(name, 'dataweave-formats-' + name)}.adoc"
    if not os.path.exists(p):
        return {}, {}
    txt = open(p).read()
    out = {"r": {}, "w": {}}
    for kind, head in (("r", "Reader Properties"), ("w", "Writer Properties")):
        m = re.search(r"=== " + head + r"(.*?)\n\|===\n\|Parameter[^\n]*\n(.*?)\n\|===", txt, re.S)
        if not m:
            continue
        for row in re.split(r"\n(?=\|`)", m.group(2)):
            cells = [c.strip() for c in row.split("|")[1:]]
            if len(cells) >= 3:
                req = "Required" in cells[0]
                nm = re.sub(r"\s*\(Required\)", "", cells[0]).strip("` ")
                out[kind][nm] = {"type": cells[1].strip("`"), "default": cells[2].strip("`").strip("'"), "required": req}
    return out["r"], out["w"]

def fmt_default(v):
    if v is None: return "`null`"
    if isinstance(v, str):
        if v == "None": return "(なし)"
        return "`" + v.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t").replace("|", "\\|") + "`" if v != "" else '`""`'
    return "`" + json.dumps(v) + "`"

def short(desc):
    d = re.sub(r"\s+", " ", desc or "").strip()
    d = re.sub(r"<<[^>]*>>", "", d)
    d = re.sub(r"https?://\S+\[([^\]]*)\]", r"\1", d)
    d = re.sub(r"xref:\S+\[([^\]]*)\]", r"\1", d)
    m = re.match(r"(.+?\.)(\s|$)", d)
    s = m.group(1) if m else d
    return s.replace("|", "\\|")[:220]

L = []
L.append("# DataWeave のデータ形式と reader / writer プロパティ\n")
L.append("実 Mule 4.11.3 同梱の DataWeave 2.11.2 で `dw::Runtime::dataFormatsDescriptor()` を評価した結果を一次資料とし、")
L.append("型 (Type) は公式ドキュメント (docs-dataweave v2.11 の `dataweave-formats-*.adoc`) の表から補った。")
L.append("既定値の列は実 DW の値。ドキュメントの既定値と食い違うものは「doc 既定値」の列に書いた。\n")
L.append("- 既定値 `(なし)` は実 DW が `None` (未設定) を返すもの。`encoding` の `(なし)` は、入力/出力の既定の文字コード (多くは UTF-8) に従う意味。")
L.append("- プロパティは `output application/csv separator=\";\"` のように output / input 指示子に書くか、Mule の `outputMimeType` の MIME パラメータで渡す。")
L.append("- 例は `test/fixtures/dw/docs/formats/` (ドキュメントの各形式ページ由来) にある。\n")
L.append("## 形式の一覧\n")
L.append("| ID | 既定の MIME | 受け付ける MIME | 拡張子 | バイナリ | 既定の文字コード | reader | writer |")
L.append("|---|---|---|---|---|---|---|---|")
for f in fmts:
    L.append(f"| `{f['name']}` | `{f['defaultMimeType']}` | {', '.join('`'+m+'`' for m in f['acceptedMimeTypes'])} | {' '.join(f['extensions'])} | {'yes' if f['binary'] else 'no'} | {f.get('defaultEncoding', '')} | {len(f['readerProperties'])} | {len(f['writerProperties'])} |")
L.append("")
ndiff = 0
for f in fmts:
    dr, dwr = doc_tables(f["name"])
    L.append(f"## {f['name']} (`{f['defaultMimeType']}`)\n")
    for kind, props, docp in (("reader", f["readerProperties"], dr), ("writer", f["writerProperties"], dwr)):
        if not props:
            L.append(f"{kind} プロパティ: なし\n")
            continue
        L.append(f"### {kind} プロパティ\n")
        L.append("| 名前 | 型 | 既定値 | 取りうる値 | 省略可 | doc 既定値 | 説明 |")
        L.append("|---|---|---|---|---|---|---|")
        for p in props:
            d = docp.get(p["name"], {})
            dd = d.get("default", "")
            rt = fmt_default(p["defaultValue"]).strip("`")
            note = ""
            if d and dd.strip('"') != str(p["defaultValue"]).strip('"').lower() and dd.strip('"') != str(p["defaultValue"]).strip('"'):
                if not (dd in ("null", "") and p["defaultValue"] in (None, "None", "")):
                    note = f"`{dd}`"
                    ndiff += 1
            elif not d and docp:
                note = "(doc の表に無い)"
            pv = ", ".join("`" + json.dumps(v) + "`" for v in p.get("possibleValues", []))
            L.append(f"| `{p['name']}` | {('`'+d['type']+'`') if d.get('type') else ''} | {fmt_default(p['defaultValue'])} | {pv} | {'yes' if p['optional'] else 'no'} | {note} | {short(p['description'])} |")
        extra = [n for n in docp if n not in {p['name'] for p in props}]
        if extra:
            L.append(f"\ndoc の表にだけあるもの: {', '.join('`'+n+'`' for n in extra)}")
        L.append("")
open(DEST, "w").write("\n".join(L) + "\n")
print("formats", len(fmts), "default diffs", ndiff)
