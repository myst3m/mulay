#!/usr/bin/env python3
"""stage/ の fill 済み .dwt を検査して test/fixtures/dw/docs/ に書き出す。
- 環境依存で意味の無いもの (外部モジュール・ファイル・ネットワーク・入力の無い payload) は捨てる
- 2 回の実行で結果が変わるもの・日付/環境依存は note に「非決定的」
- doc の Output と実 DW の結果が食い違うものは note に「doc と相違」"""
import json, os, re, sys, glob, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
S = os.path.dirname(os.path.abspath(__file__))
STAGE, STAGE2 = f"{S}/stage", f"{S}/stage2"
DEST = os.path.join(ROOT, "test/fixtures/dw/docs")
META = json.load(open(f"{STAGE}/meta.json"))

ENV_ERR = [r"Unable to resolve module", r"Unable to find resource", r"Unable to find class",
           r"Schema could not be found", r"Missing Mapping Expression",
           r"Unable to resolve reference of: `(payload|vars|attributes|flowVars|message)`",
           r"There is no variable named '(payload|vars|attributes)'", r"Unable to resolve reference of: `(lookup|p|causedBy|app|mule|server|error|correlationId|authentication)`"]

def sections(txt):
    out, cur = [], None
    txt = txt[:-1] if txt.endswith("\n") else txt
    for line in txt.split("\n"):
        if line.startswith("%%% "):
            cur = [line[4:], []]; out.append(cur)
        elif cur is not None:
            cur[1].append(line)
    return [(h, "\n".join(b)) for h, b in out]

def render(secs):
    return "".join(f"%%% {h}\n{b}\n" for h, b in secs)

def strip_json_comments(s):
    s = re.sub(r"(?m)^\s*//.*$", "", s)
    s = re.sub(r"(?m)(?<![:\"'])\s//[^\"\n]*$", "", s)
    s = re.sub(r",(\s*[}\]])", r"\1", s)
    return s

def norm_ws(s):
    return re.sub(r"\s+", "", s)

def norm_xml(s):
    s = re.sub(r"<\?xml[^>]*\?>", "", s)
    s = re.sub(r">\s+<", "><", s.strip())
    return norm_ws(s.replace("'", '"'))

def same(doc, got, mime):
    if doc is None:
        return None
    d, g = doc.strip(), got.strip()
    if d == g:
        return True
    if "json" in mime:
        try:
            return json.loads(strip_json_comments(d)) == json.loads(g)
        except Exception:
            return norm_ws(strip_json_comments(d)) == norm_ws(g)
    if "xml" in mime:
        return norm_xml(d) == norm_xml(g)
    return norm_ws(d) == norm_ws(g)

def relaxed(d, g):
    def sort_attrs(x):
        return re.sub(r"<([\w:.-]+)((?:\s+[\w:.-]+\s*=\s*(?:\"[^\"]*\"|'[^']*'))+)\s*(/?)>",
                      lambda m: "<" + m.group(1) + " " + " ".join(sorted(re.findall(r"[\w:.-]+\s*=\s*(?:\"[^\"]*\"|'[^']*')", m.group(2)))) + m.group(3) + ">", x)
    def n(x):
        x = strip_json_comments(x)
        x = re.sub(r"<\?xml[^>]*\?>", "", x)
        x = sort_attrs(x)
        x = re.sub(r"[\s\"',\\]", "", x)
        x = re.sub(r"as[A-Z]\w*\{[^{}]*\}", "", x)
        return x.lstrip("{").rstrip("}")
    return n(d) == n(g)

NONDET_RE = r"\b(now|uuid|random|randomInt|today|tomorrow|yesterday|currentMilliseconds|envVar|envVars|props?)\s*\(|\bduration\s*\(\s*\(\)|\btime\s*\(\s*\(\)"

def main():
    shutil.rmtree(DEST, ignore_errors=True)
    stats = {"kept": 0, "dropped": [], "differ": [], "nondet": [], "error": 0, "output": 0, "doc_unknown": 0}
    per_func = {}
    seq = {}
    for rel in sorted(META, key=lambda r: (os.path.dirname(r), re.sub(r"-\d+\.dwt$", "", os.path.basename(r)), int(re.search(r"-(\d+)\.dwt$", r).group(1)))):
        m = META[rel]
        p = f"{STAGE}/{rel}"
        if not os.path.exists(p):
            stats["dropped"].append((rel, "巨大計算・ネットワーク (runtime run の例)")); continue
        secs = sections(open(p, newline="").read())
        script = next(b for h, b in secs if h == "script")
        exp = [(h, b) for h, b in secs if h.startswith("output") or h == "error"]
        if not exp:
            stats["dropped"].append((rel, "未評価")); continue
        eh, eb = exp[0]
        if re.search(r"(readUrl|runUrl|evalUrl)\s*\(\s*(log\()?\s*[\"'`]https?:", script):
            stats["dropped"].append((rel, "ネットワーク依存")); continue
        if eh == "error" and not m.get("custom") and any(re.search(r, eb) for r in ENV_ERR):
            stats["dropped"].append((rel, "環境依存エラー: " + eb[:80])); continue
        flags = []
        p2 = f"{STAGE2}/{rel}"
        if (os.path.exists(p2) and open(p2, newline="").read() != open(p, newline="").read()) or re.search(NONDET_RE, script):
            flags.append("非決定的 (時刻・乱数・環境・境界文字列に依存。出力の完全一致は期待できない)")
            stats["nondet"].append(rel)
        doc = m.get("doc_output")
        if eh == "error":
            stats["error"] += 1
            if doc is not None and eb.strip()[:20] in doc:
                pass
            elif doc is not None and re.search(r"(?i)error|exception|cannot|unable", doc):
                flags.append("doc と相違 (doc もエラーだが文言が違う)")
                stats["differ"].append((rel, "errmsg", eb[:100]))
            elif doc is not None:
                flags.append("doc と相違 (doc には出力があるが、実 DW はエラー)")
                stats["differ"].append((rel, "error", eb[:100]))
        else:
            stats["output"] += 1
            r = same(doc, eb, eh)
            if r is None:
                stats["doc_unknown"] += 1
            elif not r and "非決定的" not in " ".join(flags):
                if relaxed(doc, eb):
                    flags.append("doc と相違 (表記のみ: 引用符・括弧・書式の違いで、値は同じ)")
                    stats["differ"].append((rel, "notation", ""))
                else:
                    flags.append("doc と相違 (doc の Output と実 DW の出力の値が一致しない)")
                    stats["differ"].append((rel, "output", ""))
        d = os.path.dirname(rel)
        base = re.sub(r"-\d+\.dwt$", "", os.path.basename(rel))
        seq[(d, base)] = seq.get((d, base), 0) + 1
        n = seq[(d, base)]
        note = next(b for h, b in secs if h == "note")
        note_lines = [note]
        if doc is None and "cookbook" not in rel and not m.get("custom"):
            note_lines.append("doc に Output の記載なし")
        note_lines += flags
        if flags and any("doc と相違" in f for f in flags) and doc is not None:
            note_lines.append("doc の Output:")
            note_lines += ["  " + l for l in doc.strip("\n").split("\n")]
        new = [("note", "\n".join(note_lines))] + [(h, b) for h, b in secs if h != "note"]
        os.makedirs(f"{DEST}/{d}", exist_ok=True)
        out_rel = f"{d}/{base}-{n}.dwt"
        open(f"{DEST}/{out_rel}", "w", newline="").write(render(new))
        stats["kept"] += 1
        key = (m["module"], m["func"])
        per_func.setdefault(f"{key[0]}::{key[1]}", []).append(out_rel)
    json.dump({"stats": stats, "per_func": per_func}, open(f"{S}/post.json", "w"), ensure_ascii=False, indent=1)
    print("kept", stats["kept"], "output", stats["output"], "error", stats["error"], "dropped", len(stats["dropped"]),
          "differ", len(stats["differ"]), "nondet", len(stats["nondet"]), "doc_unknown", stats["doc_unknown"])

main()
