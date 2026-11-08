#!/usr/bin/env python3
"""DW jar の .dwl ソースから関数カタログを作る。catalog.json と dw-stdlib-catalog.md を出す。"""
import json, os, re, glob, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
S = os.path.dirname(os.path.abspath(__file__))
J = f"{S}/jars"
FILES = sorted(glob.glob(f"{J}/wlang-2.11.2/dw/**/*.dwl", recursive=True)) + [f"{J}/mule-service-weave-2.11.2/Mule.dwl"]

def modname(f):
    if f.endswith("Mule.dwl") and "mule-service-weave" in f:
        return "dw::Mule"
    rel = os.path.relpath(f, f"{J}/wlang-2.11.2")[:-4]
    return rel.replace("/", "::")

def sig_end(txt, i):
    """txt[i] は 'fun' の位置。関数本体の '=' の位置を返す"""
    depth, j, n = 0, i, len(txt)
    while j < n:
        c = txt[j]
        if c in "\"'`":
            q = c; j += 1
            while j < n and txt[j] != q:
                j += 2 if txt[j] == "\\" else 1
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == "<" and txt[j+1:j+2] not in ("=", ":"):
            depth += 1; j += 1; continue
        elif c == ">" and depth > 0 and txt[j-1] != "-":
            depth -= 1
        elif c == "=" and depth == 0 and txt[j+1] not in "=>" and txt[j-1] not in "<>!=":
            return j
        j += 1
    return n

def parse(f):
    txt = open(f, encoding="utf-8").read()
    out = []
    for m in re.finditer(r"(?m)^fun\s", txt):
        i = m.start()
        e = sig_end(txt, i)
        sig = re.sub(r"\s+", " ", txt[i + 4:e]).strip()
        sig = re.sub(r"\(\s+", "(", sig); sig = re.sub(r"\s+\)", ")", sig)
        name = re.match(r"([^\s(<]+)", sig).group(1)
        # 直前の注釈と doc コメント
        pre = txt[:i]
        ann = []
        k = len(pre)
        lines = pre.split("\n")
        idx = len(lines) - 1
        if lines[idx] == "": idx -= 1
        while idx >= 0 and (lines[idx].strip().startswith("@") or lines[idx].strip() == ""):
            if lines[idx].strip().startswith("@"): ann.insert(0, lines[idx].strip())
            idx -= 1
        doc = ""
        if idx >= 0 and lines[idx].strip().endswith("*/"):
            j = idx
            while j >= 0 and "/**" not in lines[j]: j -= 1
            doc = "\n".join(lines[j:idx + 1])
        a = " ".join(ann)
        since = re.search(r"@Since\(version\s*=\s*\"([^\"]+)\"", a)
        since = since.group(1) if since else None
        if not since:
            ms = re.search(r"Introduced in DataWeave (?:version )?(\d+\.\d+(?:\.\d+)?)", doc)
            since = ms.group(1) if ms else None
        dep = re.search(r"@Deprecated\(since\s*=\s*\"([^\"]+)\",\s*replacement\s*=\s*\"([^\"]*)\"", a)
        out.append({
            "name": name, "sig": sig, "since": since,
            "deprecated": {"since": dep.group(1), "replacement": dep.group(2)} if dep else None,
            "experimental": "@Experimental" in a, "internal": "@Internal" in a,
            "native": "native(" in txt[e:e + 120],
            "summary": first_sentence(doc),
        })
    return out

def first_sentence(doc):
    lines = [re.sub(r"^\s*/?\*+/?\s?", "", l).strip() for l in doc.split("\n")]
    body = []
    for l in lines:
        if l.startswith("==") or l.startswith("[") or l.startswith("|"):
            break
        if l: body.append(l)
        elif body: break
    s = " ".join(body)
    m = re.match(r"(.+?\.)(\s|$)", s)
    return (m.group(1) if m else s)[:160]

cat = {}
for f in FILES:
    fs = parse(f)
    if fs:
        cat[modname(f)] = fs
json.dump(cat, open(f"{S}/catalog.json", "w"), ensure_ascii=False, indent=1)
for m, fs in cat.items():
    print(m, len({x['name'] for x in fs}), len(fs))

# ---- markdown ----
SAFE = {"++": "plusplus", "--": "minusminus", "+": "plus", "-": "minus", "*": "times", "/": "divide", ">>": "gtgt"}
def safe(n): return SAFE.get(n, re.sub(r"[^A-Za-z0-9_]", "_", n))
post = json.load(open(f"{S}/post.json"))
pf = post["per_func"]
FIX = os.path.join(ROOT, "test/fixtures/dw/docs")
PAGE_PREFIX = lambda m: "dw-" + m.split("::")[-1].lower()
L = []
L.append("# DataWeave 2.x 標準ライブラリ関数カタログ\n")
L.append("一次資料は実 Mule 4.11.3 同梱の DataWeave 2.11.2 の `.dwl` ソース")
L.append("(`services/mule-service-weave-ee-2.11.2/lib/wlang-2.11.2.jar` の `dw/**/*.dwl` と、`mule-service-weave-2.11.2.jar` の `Mule.dwl`)。")
L.append("シグネチャはソースの `fun` 宣言をそのまま (空白だけ詰めて) 写した。")
L.append("`core-modules-2.11.2.jar` には同じモジュールがコンパイル済み (`.bdwl`) で入っている。\n")
L.append("列の意味:\n")
L.append("- **導入**: `@Since(version=...)` 注釈 (無ければ doc コメントの \"Introduced in DataWeave x.y\")。空欄は注記なし (2.0 以前からある)。")
L.append("- **状態**: `非推奨` は `@Deprecated`、`実験的` は `@Experimental`、`内部` は `@Internal` (利用者のスクリプトからは呼べない。実 DW は \"can not be access from `anonymous`\" で失敗する)。")
L.append("- **例**: `test/fixtures/dw/docs/<モジュール>/<関数>-<n>.dwt` の件数 (関数名単位。オーバーロードごとには数えていない)。期待値は実 DW 2.11.2 で生成済み。")
L.append("  言語ガイド・形式・cookbook 由来の例 (`guide/`、`formats/`、`cookbook/`) は関数ごとには数えていない。\n")
L.append("演算子のうち `++` と `--` は `dw::Core` の関数として定義されている。それ以外の演算子 (`+`、`-`、`as`、`is`、`default`、`update`、`match`、`do`、`if`、`and`/`or`、比較、セレクタ) は言語組み込みで、`guide/dw-operators-*`、`guide/selectors-*`、`guide/pattern-matching-*`、`guide/flow-control-*` に例がある。\n")
rows = []
detail = []
tot_n = tot_o = tot_c = 0
tot_pub = tot_pub_c = 0
for m, fs in cat.items():
    short = m.split("::")[-1].lower()
    names = []
    for f in fs:
        if f["name"] not in names: names.append(f["name"])
    covered = 0; pub = 0; pub_c = 0
    detail.append(f"## {m}\n")
    detail.append(f"doc: https://docs.mulesoft.com/dataweave/2.11/{PAGE_PREFIX(m)}\n")
    detail.append("| 関数 | シグネチャ | 導入 | 状態 | 例 |")
    detail.append("|---|---|---|---|---|")
    for n in names:
        ovs = [f for f in fs if f["name"] == n]
        cnt = len(pf.get(f"{short}::{safe(n)}", []))
        covered += cnt > 0
        internal = all(o["internal"] for o in ovs)
        if not internal:
            pub += 1; pub_c += cnt > 0
        for k, o in enumerate(ovs):
            st = []
            if o["deprecated"]:
                r = o["deprecated"]["replacement"]
                st.append(f"非推奨 ({o['deprecated']['since']}〜" + (f", 代替 `{r}`)" if r else ")"))
            if o["experimental"]: st.append("実験的")
            if o["internal"]: st.append("内部")
            sig = re.sub(r"\s+,", ",", o["sig"]).replace("|", "\\|")
            cell_n = f"`{n}`" if k == 0 else ""
            cell_c = str(cnt) if k == 0 else ""
            detail.append(f"| {cell_n} | `{sig}` | {o['since'] or ''} | {' '.join(st)} | {cell_c} |")
    detail.append("")
    rows.append(f"| `{m}` | {len(names)} | {len(fs)} | {covered} | {covered*100//max(1,len(names))}% |")
    tot_n += len(names); tot_o += len(fs); tot_c += covered; tot_pub += pub; tot_pub_c += pub_c
L.append("## 概要\n")
L.append("| モジュール | 関数 (名前) | オーバーロード | 例のある関数 | 被覆率 |")
L.append("|---|---:|---:|---:|---:|")
L += rows
L.append(f"| **合計** | **{tot_n}** | **{tot_o}** | **{tot_c}** | **{tot_c*1000//tot_n/10}%** |")
L.append("")
L.append(f"`@Internal` を除いた公開関数では {tot_pub_c}/{tot_pub} ({tot_pub_c*1000//tot_pub/10}%)。")
L.append("例の無い関数: `dw::Core` の `native` / `logInternal` (内部)、`dw::Mule` の `lookup` / `p` / `causedBy` (Mule の実行文脈が要り、単体の DW では `BindingContext was not bind as a Service` で失敗するため golden にできない)。")
L.append("`dw::Mule` のモジュール名はソース上 `Mule` (jar 直下の `Mule.dwl`) で、Mule の中では `Mule::p(...)` または自動 import で呼ぶ。ドキュメントの表記に合わせて `dw::Mule` と書いた。\n")
L += detail
open(os.path.join(ROOT, "docs/dw-stdlib-catalog.md"), "w").write("\n".join(L) + "\n")
print("total", tot_n, tot_o, tot_c, tot_pub, tot_pub_c)
