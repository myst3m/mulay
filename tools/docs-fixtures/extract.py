#!/usr/bin/env python3
"""docs-dataweave (v2.11) の adoc と、DW jar の .dwl doc コメントから例を抜いて .dwt を作る。
出力: STAGE/<dir>/<name>-<n>.dwt と STAGE/meta.json (doc の Output 等)"""
import html, json, os, re, sys, glob

S = os.path.dirname(os.path.abspath(__file__))
PAGES = f"{S}/dwdocs/modules/ROOT/pages"
PART = f"{PAGES}/_partials"
JARS = f"{S}/jars"
STAGE = f"{S}/stage"
BASEURL = "https://docs.mulesoft.com/dataweave/2.11/"

LANG_MIME = {
    "json": "application/json", "xml": "application/xml", "csv": "application/csv",
    "yaml": "application/yaml", "txt": "text/plain", "text": "text/plain",
    "dataweave": "application/dw", "dw": "application/dw", "weave": "application/dw",
    "ndjson": "application/x-ndjson", "form-urlencoded": "application/x-www-form-urlencoded",
    "properties": "text/x-java-properties", "multipart": "multipart/form-data",
}
DW_LANGS = {"dataweave", "dw", "weave", "dataweace"}
SKIP_LANGS = {"java", "console", "groovy", "protobuf", "error", "event-stream", "linenums", "bash", "shell"}

def lang_of(attr):
    m = re.match(r"\[source\s*,\s*([^,\]]*)", attr)
    return m.group(1).strip().lower() if m else ""

def is_label(text):
    t = text.lower().strip().rstrip(":")
    if len(t.split()) > 5:
        return False
    return any(k in t for k in ("input", "output", "source", "script", "result", "configuration", "transform", "payload"))

def classify_label(t):
    t = t.lower()
    if "output" in t or "result" in t:
        return "output"
    if "configuration" in t or "mule" in t or "flow" in t:
        return "config"
    if "input" in t or "payload" in t:
        return "input"
    if "source" in t or "script" in t or "transform" in t or "dataweave" in t:
        return "script"
    return None

def resolve_include(line, cur_file):
    m = re.match(r"include::([^\[]+)\[", line)
    if not m:
        return None
    p = m.group(1)
    p = re.sub(r"^(dataweave::)?partial\$", PART + "/", p)
    if p.startswith("release-notes::"):
        return None
    if not p.startswith("/"):
        p = os.path.join(os.path.dirname(cur_file), p)
    try:
        return open(p, encoding="utf-8").read().rstrip("\n").split("\n")
    except OSError:
        return None

def blocks_of(path):
    """ページを (kind, payload) の列に: ('boundary', title) / ('label', text) / ('block', lang, body)"""
    lines = open(path, encoding="utf-8").read().split("\n")
    out, i, pending_attr, last_prose = [], 0, None, None
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("//"):
            i += 1; continue
        m = re.match(r"^(=+)\s+(.*)", ln)
        if m and not ln.startswith("===="*2):
            title = html.unescape(m.group(2))
            if len(m.group(1)) >= 2 and is_label(title):
                out.append(("label", title))
            elif len(m.group(1)) >= 2 or len(m.group(1)) == 1:
                out.append(("boundary", title))
            i += 1; continue
        m = re.match(r"^\.([A-Za-z].*)", ln)
        if m:
            t = m.group(1)
            if is_label(t) or classify_label(t):
                out.append(("label", t))
            i += 1; continue
        if ln.startswith("[source"):
            pending_attr = ln; i += 1; continue
        if ln.strip() == "----" and pending_attr is not None:
            body, i = [], i + 1
            while i < len(lines) and lines[i].strip() != "----":
                inc = resolve_include(lines[i], path) if lines[i].startswith("include::") else None
                if inc is not None:
                    body.extend(inc)
                elif not lines[i].startswith("include::"):
                    body.append(lines[i])
                i += 1
            # asciidoc callouts <1> を落とす
            body = [re.sub(r"\s*(//\s*)?<\d+>\s*$", "", b) for b in body]
            out.append(("block", lang_of(pending_attr), "\n".join(body), last_prose))
            pending_attr = None; i += 1; continue
        if ln.strip() and not ln.startswith("[") and not ln.startswith("include::"):
            last_prose = ln.strip()
            pending_attr = None
        i += 1
    return out

def looks_script(body):
    return bool(re.search(r"^\s*%dw\s+2", body, re.M)) or bool(re.search(r"^---\s*$", body, re.M))

def looks_mule_config(body):
    return bool(re.search(r"<(flow|mule|ee:transform|set-payload|http:listener)\b", body))

def examples_of(path):
    items = blocks_of(path)
    exs, seg_inputs, since_script_inputs, label, cur = [], [], [], None, None
    def flush():
        nonlocal cur
        if cur: exs.append(cur)
        cur = None
    for it in items:
        if it[0] == "boundary":
            flush(); seg_inputs, since_script_inputs, label = [], [], None; continue
        if it[0] == "label":
            label = it[1]; continue
        _, lang, body, prose = it
        kind = classify_label(label) if label else None
        if lang in DW_LANGS and looks_script(body):
            kind = "script"
        label = None
        if lang in SKIP_LANGS or looks_mule_config(body):
            continue
        if kind is None:
            p = (prose or "").lower()
            if lang in DW_LANGS and looks_script(body):
                kind = "script"
            elif cur is not None and cur.get("output") is None:
                kind = "output"
            elif "input" in p or "payload" in p:
                kind = "input"
            elif "output" in p or "result" in p or "produces" in p or "returns" in p:
                kind = "output"
            else:
                kind = "ignore"
        if kind in ("config", "ignore"):
            continue
        if kind == "script":
            if lang not in DW_LANGS and lang != "":
                continue
            flush()
            ins = since_script_inputs if since_script_inputs else seg_inputs
            cur = {"script": body, "inputs": list(ins), "output": None, "out_lang": None}
            since_script_inputs = []
            continue
        if kind == "input" and cur is not None and cur["output"] is None:
            cur["inputs"].append((lang, body))
            continue
        if kind == "input":
            if since_script_inputs == [] and cur is not None:
                seg_inputs = []
            since_script_inputs.append((lang, body)); seg_inputs = since_script_inputs
            continue
        if kind == "output":
            if cur is not None and cur["output"] is None:
                cur["output"] = body; cur["out_lang"] = lang
            continue
    flush()
    return exs

# ---- dwl doc コメントからの抽出 ----
def dwl_examples(path):
    """/** ... */ の直後の fun 名ごとに Example を返す: [(name, ex)]"""
    txt = open(path, encoding="utf-8").read()
    res = []
    for m in re.finditer(r"/\*\*(.*?)\*/\s*((?:@[^\n]*\n\s*)*)fun\s+([^\s(<]+)", txt, re.S):
        doc, name = m.group(1), m.group(3)
        lines = [re.sub(r"^\s*\*( |$)", "", l) for l in doc.split("\n")]
        tmp = f"{S}/tmp_doc.adoc"
        open(tmp, "w").write("= x\n" + "\n".join(lines))
        for ex in examples_of(tmp):
            res.append((name, ex))
    return res

def norm_script(script, out_lang):
    s = script.strip("\n")
    if not re.search(r"^\s*%dw\s+2", s, re.M):
        if re.search(r"^---\s*$", s, re.M):
            s = "%dw 2.0\n" + s
        else:
            s = "%dw 2.0\n---\n" + s
    if not re.search(r"^\s*output\s+\S", s.split("\n---")[0] if "\n---" in s else "", re.M):
        mime = LANG_MIME.get(out_lang or "json", "application/json")
        s = re.sub(r"^(\s*%dw\s+2\.\d+[^\n]*)", lambda m: m.group(1) + "\noutput " + mime, s, count=1, flags=re.M)
    return s

def input_header(script, lang, idx, n, body=""):
    name = "payload"
    mime = LANG_MIME.get(lang, "application/json")
    mb = re.match(r"\s*--([^\s-][^\s]*)\s*\n.*Content-Disposition", body, re.S)
    if mb:
        return f"input payload multipart/form-data boundary={mb.group(1)}"
    m = re.search(r"^\s*input\s+(\w+)\s+([\w.+-]+/[\w.+-]+)", script, re.M)
    if m and n == 1:
        name, mime = m.group(1), m.group(2)
    elif n > 1:
        name = f"in{idx}" if idx else "payload"
    return f"input {name} {mime}"

def header_only(script):
    s = script.strip()
    if re.search(r"^---\s*$", s, re.M) or re.search(r"^\s*%dw\s+2", s, re.M):
        return False
    body = re.sub(r"(?s)/\*.*?\*/", "", s)
    body = "\n".join(l for l in body.split("\n") if not l.strip().startswith("//"))
    return bool(re.match(r"\s*(fun|var|type|ns|import|output|input)\b", body))

def write(dirname, base, n, ex, url, origin):
    if header_only(ex["script"]):
        SKIPPED.append((dirname, base, url, "ヘッダだけの断片"))
        return
    script = norm_script(ex["script"], ex.get("out_lang"))
    parts = [f"%%% note\n由来: {url} ({origin})", f"%%% script\n{script}"]
    for k, (lang, body) in enumerate(ex["inputs"]):
        hdr = input_header(script, lang, k, len(ex['inputs']), body)
        if not re.search(r"\b" + hdr.split()[1] + r"\b", script.split("\n---", 1)[-1]):
            continue
        parts.append(f"%%% {hdr}\n{body.strip(chr(10))}")
    d = f"{STAGE}/{dirname}"
    os.makedirs(d, exist_ok=True)
    fn = f"{d}/{base}-{n}.dwt"
    open(fn, "w").write("\n".join(parts) + "\n")
    META[os.path.relpath(fn, STAGE)] = {"doc_output": ex.get("output"), "out_lang": ex.get("out_lang"), "url": url, "func": base, "module": dirname}

META = {}
SKIPPED = []
SAFE = {"++": "plusplus", "--": "minusminus", "+": "plus", "-": "minus", "*": "times", "/": "divide", ">>": "gtgt"}

def safe(name):
    return SAFE.get(name, re.sub(r"[^A-Za-z0-9_]", "_", name))

def main():
    import shutil
    shutil.rmtree(STAGE, ignore_errors=True)
    covered = set()
    # 1. 関数ページ
    for p in sorted(glob.glob(f"{PAGES}/dw-*-functions-*.adoc")):
        slug = os.path.basename(p)[:-5]
        mod = slug.split("-functions-")[0][3:]
        title = html.unescape(open(p).readline()[2:].strip())
        exs = examples_of(p)
        for n, ex in enumerate(exs, 1):
            write(mod, safe(title), n, ex, BASEURL + slug, "関数ページ")
        if exs:
            covered.add((mod, title))
    # 2. 言語ガイド・フォーマット・演算子
    for p in sorted(glob.glob(f"{PAGES}/dataweave-*.adoc") + [f"{PAGES}/dw-operators.adoc"]):
        slug = os.path.basename(p)[:-5]
        if any(x in slug for x in ("release-notes", "maven-plugin", "extension", "testing-framework", "cookbook", "logging-configuration")):
            continue
        if slug.startswith("dataweave-formats"):
            d, base = "formats", slug.replace("dataweave-formats-", "").replace("dataweave-formats", "overview")
        else:
            d, base = "guide", slug.replace("dataweave-", "")
        for n, ex in enumerate(examples_of(p), 1):
            write(d, base, n, ex, BASEURL + slug, "言語ガイド")
    # 3. cookbook (transform.dwl + inputs/ + out.*)
    for cdir in sorted(glob.glob(f"{PART}/cookbook-dw/*/")):
        name = os.path.basename(cdir.rstrip("/"))
        tf = f"{cdir}transform.dwl"
        if not os.path.exists(tf):
            continue
        ins = []
        for f in sorted(glob.glob(f"{cdir}inputs/**/*", recursive=True)):
            if os.path.isfile(f):
                rel = os.path.relpath(f, f"{cdir}inputs")
                nm = rel.rsplit(".", 1)[0].replace("/", ".")
                ins.append((nm, f.rsplit(".", 1)[1], open(f).read()))
        outs = glob.glob(f"{cdir}out.*")
        script = open(tf).read()
        slug_page = [q for q in glob.glob(f"{PAGES}/dataweave-cookbook-*.adoc") if f"cookbook-dw/{name}/" in open(q).read()]
        url = BASEURL + (os.path.basename(slug_page[0])[:-5] if slug_page else "dataweave-cookbook")
        ex = {"script": script, "inputs": [], "output": open(outs[0]).read() if outs else None,
              "out_lang": outs[0].rsplit(".", 1)[1] if outs else None}
        d = f"{STAGE}/cookbook"; os.makedirs(d, exist_ok=True)
        s = norm_script(script, ex["out_lang"])
        parts = [f"%%% note\n由来: {url} (cookbook partial {name})", f"%%% script\n{s}"]
        vars_ = [x for x in ins if x[0].startswith("vars.")]
        for nm, ext, body in ins:
            if nm.startswith("vars."):
                continue
            parts.append(f"%%% input {nm} {LANG_MIME.get(ext, 'application/json')}\n{body.strip(chr(10))}")
        if vars_:
            obj = "{" + ",".join(f'"{nm[5:]}": {body.strip()}' for nm, ext, body in vars_ if ext == "json") + "}"
            parts.append(f"%%% input vars application/json\n{obj}")
        fn = f"{d}/{name}-1.dwt"
        open(fn, "w").write("\n".join(parts) + "\n")
        META[os.path.relpath(fn, STAGE)] = {"doc_output": ex["output"], "out_lang": ex["out_lang"], "url": url, "func": name, "module": "cookbook"}
    # 4. doc ページの無い関数は dwl の doc コメントから
    modmap = {}
    for f in glob.glob(f"{JARS}/wlang-2.11.2/dw/**/*.dwl", recursive=True) + [f"{JARS}/mule-service-weave-2.11.2/Mule.dwl"]:
        base = os.path.basename(f)[:-4].lower()
        modmap[f] = base
    for f, mod in modmap.items():
        cnt = {}
        for name, ex in dwl_examples(f):
            if (mod, name) in covered:
                continue
            cnt[name] = cnt.get(name, 0) + 1
            write(mod, safe(name), 100 + cnt[name], ex, f"jar:{os.path.relpath(f, JARS)}", "dwl doc コメント (doc ページに例なし)")
    # 5. 自作 (doc の例が無い・doc の例が環境依存で評価できない関数)
    for f in sorted(glob.glob(f"{S}/custom/*/*.dwt")):
        d = os.path.basename(os.path.dirname(f))
        base = re.sub(r"-\d+\.dwt$", "", os.path.basename(f))
        os.makedirs(f"{STAGE}/{d}", exist_ok=True)
        k = 200
        while os.path.exists(f"{STAGE}/{d}/{base}-{k}.dwt"): k += 1
        out = f"{STAGE}/{d}/{base}-{k}.dwt"
        open(out, "w").write("%%% note\n由来: 自作 (doc に実行できる例が無いため補った)\n" + open(f).read())
        META[os.path.relpath(out, STAGE)] = {"doc_output": None, "out_lang": None, "url": None, "func": base, "module": d, "custom": True}
    json.dump(SKIPPED, open(f"{STAGE}/skipped.json", "w"), ensure_ascii=False, indent=1)
    json.dump(META, open(f"{STAGE}/meta.json", "w"), ensure_ascii=False, indent=1)
    print(len(META), "files")

if __name__ == "__main__":
    main()
