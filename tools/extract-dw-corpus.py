#!/usr/bin/env python3
"""mulet のテストとサンプルから DataWeave スクリプトを集め、1 ファイル 1 スクリプトで書き出す。

  tools/extract-dw-corpus.py MULET_DIR       (アーカイブした gitlab.com/myst3m/mulet を clone したもの)
  tools/extract-dw-corpus.py --docs [DOCS_DIR]
      MuleSoft 公式ドキュメント (github.com/mulesoft/docs-dataweave の v2.11 ブランチ) の
      [source,dataweave] の例を test/fixtures/dw-docs-corpus/ に書く (実 DW で読めるものだけ)。
      DOCS_DIR を省くと一時ディレクトリに clone する。

集めるもの
  1. test/**/*.clj の文字列リテラルのうち DataWeave を渡す関数 (dw, eval-dw, assert-parity, api/transform, ...)
     の引数、または `%dw` / `\\n---` を含むもの。(str ..) の断片は除く。
     Mule XML を含む文字列からは 2. と同じように取り出す。
  2. Mule XML (samples/**/*.xml と samples の jar の中の XML) の `#[...]` と
     <ee:set-payload> / <ee:set-variable> / <ee:set-attributes> の本文 (CDATA)。
  3. samples の jar の中の .dwl ファイル。`---` の無いものはモジュールとして .mod.dwl にする。

実 DataWeave (tools/dwparse/dw-parse-oracle、Mule 4.11 の DW 2.11.2) で読めたものを
test/fixtures/dw-corpus/ に、読めなかったもの (意図的に不正な例や DW 1.0 の断片) を
test/fixtures/dw-corpus-invalid/ に書く。どちらにも INDEX.tsv (ファイル名、出どころ、DW のエラー) を置く。
同じ本文は 1 つにまとめる。
"""
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_MODE = len(sys.argv) > 1 and sys.argv[1] == '--docs'
MULET = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not DOCS_MODE else '~/mule-work/dev/mulet')
OUT_OK = os.path.join(ROOT, 'test', 'fixtures', 'dw-corpus')
OUT_BAD = os.path.join(ROOT, 'test', 'fixtures', 'dw-corpus-invalid')
ORACLE = os.path.join(ROOT, 'tools', 'dwparse', 'dw-parse-oracle')

# 集めない samples のディレクトリ。exchange-examples は MuleSoft Exchange の例と DataWeave ライブラリの JAR で、
# 再配布の条件がまちまちなので写さない
SKIP_SAMPLES = {'exchange-examples'}

# mulay がまだ読めない (診断を出す) 構文。コーパスから外して数だけ報告する。ソースの一部 -> 理由
UNSUPPORTED = {
    'h#"$(': 'ns#"$(..)" namespaced selector with an interpolated name',
}

DW_FNS = {
    'dw', 'eval-dw', 'eval-dw-expr', 'assert-parity', 'assert-triple-parity', 'ast/parse-expression',
    'api/transform', 'api/parse-dw-expression', 'parse-dw', 'eval-both', 'eval-three', 'eval-three-safe',
    'eval-interp', 'eval-reg', 'run-dw', 'dw-eval', 'transform', 'parse-expression', 'compile-dw',
    'dw/parse', 'parser/parse', 'dw-parser/parse', 'eval-expr', 'check-dw', 'dw->ir',
}


# --- Clojure の文字列リテラル ---------------------------------------------

def clj_unescape(s):
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            d = s[i + 1]
            if d == 'n':
                out.append('\n')
            elif d == 't':
                out.append('\t')
            elif d == 'r':
                out.append('\r')
            elif d == 'b':
                out.append('\b')
            elif d == 'f':
                out.append('\f')
            elif d == 'u' and re.match(r'[0-9a-fA-F]{4}', s[i + 2:i + 6]):
                out.append(chr(int(s[i + 2:i + 6], 16)))
                i += 6
                continue
            elif d in '0123456789' and re.match(r'[0-7]{1,3}', s[i + 1:i + 4]):
                m = re.match(r'[0-7]{1,3}', s[i + 1:i + 4])
                out.append(chr(int(m.group(0), 8)))
                i += 1 + len(m.group(0))
                continue
            else:
                out.append(d)
            i += 2
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def clj_strings(text):
    """(文字列, それを直接含む呼び出しの先頭の記号, 引数の位置) を並べる"""
    res = []
    stack = []  # [head, argc]
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == ';':
            while i < n and text[i] != '\n':
                i += 1
            continue
        if c == '\\':  # 文字リテラル \a \newline \"
            m = re.match(r'\\(newline|space|tab|return|backspace|formfeed|u[0-9a-fA-F]{4}|.)', text[i:])
            i += len(m.group(0)) if m else 2
            if stack:
                stack[-1][1] += 1
            continue
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == '\\' else 1
            raw = text[i + 1:j]
            head, argc = (stack[-1][0], stack[-1][1]) if stack else ('', 0)
            res.append((clj_unescape(raw), head, argc))
            if stack:
                stack[-1][1] += 1
            i = j + 1
            continue
        if c in '([{':
            if stack:
                stack[-1][1] += 1
            head = ''
            if c == '(':
                m = re.match(r'\(\s*([^\s()\[\]{}"]+)', text[i:])
                head = m.group(1) if m else ''
            stack.append([head if c == '(' else c, -1 if c == '(' else 0])
            i += 1
            continue
        if c in ')]}':
            if stack:
                stack.pop()
            i += 1
            continue
        if c.isspace() or c == ',':
            i += 1
            continue
        # その他のトークン
        m = re.match(r'[^\s()\[\]{}"\\;,]+', text[i:])
        tok = m.group(0) if m else text[i]
        if stack:
            stack[-1][1] += 1
        i += len(tok)
    return res


# --- Mule XML ---------------------------------------------------------------

def expr_spans(s):
    """#[ ... ] を括弧の対応で取り出す (DW の文字列の中の ] を考慮)"""
    out = []
    i = 0
    while True:
        i = s.find('#[', i)
        if i < 0:
            return out
        j = i + 2
        depth = 1
        q = None
        while j < len(s) and depth > 0:
            c = s[j]
            if q:
                if c == '\\':
                    j += 2
                    continue
                if c == q:
                    q = None
            elif c in '"\'`':
                q = c
            elif c in '[({':
                depth += 1
            elif c in '])}':
                depth -= 1
            j += 1
        if depth == 0:
            out.append(s[i + 2:j - 1])
        i = j


DW_BODY_TAGS = ('set-payload', 'set-variable', 'set-attributes')


def from_xml(text, origin):
    items = []
    try:
        root = ET.fromstring(text)
        for el in root.iter():
            tag = el.tag.split('}')[-1]
            for k, v in el.attrib.items():
                for e in expr_spans(v):
                    items.append((e, f'{origin} <{tag} {k.split("}")[-1]}>'))
            if tag in DW_BODY_TAGS and el.text and el.text.strip() and not el.attrib.get('resource'):
                items.append((el.text, f'{origin} <ee:{tag}>'))
            elif el.text and '#[' in el.text:
                for e in expr_spans(el.text):
                    items.append((e, f'{origin} <{tag}> text'))
    except ET.ParseError:
        # 断片の XML: CDATA と属性を正規表現で拾う
        for m in re.finditer(r'<ee:(set-payload|set-variable|set-attributes)[^>]*>\s*<!\[CDATA\[(.*?)\]\]>', text, re.S):
            items.append((m.group(2), f'{origin} <ee:{m.group(1)}> (raw)'))
        for m in re.finditer(r'="([^"]*)"', text):
            v = (m.group(1).replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>')
                 .replace('&apos;', "'").replace('&amp;', '&'))
            for e in expr_spans(v):
                items.append((e, f'{origin} attr (raw)'))
    return items


# --- 集める -----------------------------------------------------------------

def collect():
    items = []  # (src, origin, mode)
    tdir = os.path.join(MULET, 'test')
    for dp, dn, fn in os.walk(tdir):
        for f in sorted(fn):
            if not f.endswith(('.clj', '.cljc')):
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, MULET)
            text = open(p, encoding='utf-8', errors='replace').read()
            for s, head, argc in clj_strings(text):
                if head == 'str':
                    continue
                if ('<mule' in s or '<flow' in s) and ('#[' in s or 'ee:' in s):
                    for e, o in from_xml(s, rel):
                        items.append((e, o, 'e'))
                    continue
                if (head in DW_FNS and argc == 1) or '%dw' in s or '\n---' in s:
                    if head in ('testing', 'is', 'println', 'ex-info', 'format') and '%dw' not in s:
                        continue
                    items.append((s, f'{rel} ({head})', 'e'))
    sdir = os.path.join(MULET, 'samples')
    for dp, dn, fn in os.walk(sdir):
        dn[:] = [d for d in dn if d not in SKIP_SAMPLES]
        for f in sorted(fn):
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, MULET)
            if f.endswith('.xml') and '/target/' not in p:
                text = open(p, encoding='utf-8', errors='replace').read()
                for e, o in from_xml(text, rel):
                    items.append((e, o, 'e'))
            elif f.endswith('.dwl') and '/target/' not in p:
                text = open(p, encoding='utf-8', errors='replace').read()
                items.append((text, rel, 'e' if has_body(text) else 'm'))
            elif f.endswith('.jar'):
                with zipfile.ZipFile(p) as z:
                    for zi in z.namelist():
                        if zi.startswith('META-INF') or zi.endswith(('pom.xml', 'log4j2.xml', 'log4j2-test.xml')):
                            continue
                        if zi.endswith('.dwl'):
                            text = z.read(zi).decode('utf-8', errors='replace')
                            items.append((text, f'{rel}!{zi}', 'e' if has_body(text) else 'm'))
                        elif zi.endswith('.xml'):
                            text = z.read(zi).decode('utf-8', errors='replace')
                            if 'mulesoft.org/schema/mule' in text:
                                for e, o in from_xml(text, f'{rel}!{zi}'):
                                    items.append((e, o, 'e'))
    return items


def has_body(text):
    """コメントと文字列を除き、括弧の外に --- があるか (モジュールかマッピングかの判定。do { .. --- .. } は数えない)"""
    t = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    t = re.sub(r'//[^\n]*', '', t)
    t = re.sub(r'"(\\.|[^"\\])*"|\'(\\.|[^\'\\])*\'', '""', t)
    depth = 0
    i = 0
    while i < len(t):
        c = t[i]
        if c in '([{':
            depth += 1
        elif c in ')]}':
            depth -= 1
        elif depth == 0 and t.startswith('---', i):
            return True
        i += 1
    return False


def slug(origin):
    base = origin.split('!')[-1].split(' ')[0]
    base = os.path.basename(base)
    base = re.sub(r'\.(clj|xml|dwl|jar)$', '', base)
    return re.sub(r'[^A-Za-z0-9_-]+', '-', base)[:40]


def collect_docs(ddir):
    items = []
    pages = os.path.join(ddir, 'modules', 'ROOT', 'pages')
    for dp, dn, fn in os.walk(pages):
        for f in sorted(fn):
            if not f.endswith('.adoc'):
                continue
            p = os.path.join(dp, f)
            t = open(p, encoding='utf-8', errors='replace').read()
            for m in re.finditer(r'^\[source,\s*dataweave[^\]]*\]\s*\n(----+)\n(.*?)\n\1\s*$', t, re.S | re.M | re.I):
                body = re.sub(r'\s*<\d+>\s*$', '', m.group(2), flags=re.M)  # asciidoc の callout <1>
                items.append((body, os.path.relpath(p, ddir), 'e'))
    return items


def docs_main():
    ddir = sys.argv[2] if len(sys.argv) > 2 else None
    tmp = None
    if ddir is None:
        tmp = tempfile.mkdtemp()
        ddir = os.path.join(tmp, 'docs-dataweave')
        subprocess.run(['git', 'clone', '-q', '--depth', '1', '--branch', 'v2.11',
                        'https://github.com/mulesoft/docs-dataweave.git', ddir], check=True)
    items = collect_docs(ddir)
    seen = set()
    uniq = []
    for src, origin, mode in items:
        h = hashlib.sha1(src.encode()).hexdigest()
        if src.strip() and h not in seen:
            seen.add(h)
            uniq.append((src, origin, mode))
    res = run_oracle_files(uniq)
    out = os.path.join(ROOT, 'test', 'fixtures', 'dw-docs-corpus')
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.endswith('.dwl') or f == 'INDEX.tsv':
            os.remove(os.path.join(out, f))
    idx = []
    n = 0
    skipped = 0
    for (src, origin, mode), (st, msg) in zip(uniq, res):
        if st != 'OK':
            continue
        if any(k in src for k in UNSUPPORTED):
            skipped += 1
            continue
        n += 1
        name = f'{n:04d}-{slug(origin)}.dwl'
        open(os.path.join(out, name), 'w', encoding='utf-8').write(src)
        idx.append(f'{name}\t{origin}')
    open(os.path.join(out, 'INDEX.tsv'), 'w', encoding='utf-8').write(
        '# file\torigin (docs-dataweave v2.11 の [source,dataweave] の例のうち実 DW 2.11.2 で読めるもの)\n' + '\n'.join(idx) + '\n')
    print(f'{len(items)} examples, {len(uniq)} unique, {n} valid -> {out} ({skipped} valid but unsupported, excluded)')


def run_oracle_files(uniq):
    with tempfile.TemporaryDirectory() as td:
        paths = []
        for i, (src, origin, mode) in enumerate(uniq):
            p = os.path.join(td, f'{i:05d}' + ('.mod.dwl' if mode == 'm' else '.dwl'))
            open(p, 'w', encoding='utf-8').write(src)
            paths.append(p)
        out = subprocess.run([ORACLE, '-files'], input='\n'.join(paths).encode(), capture_output=True,
                             check=True).stdout.decode()
        status = {}
        for line in out.splitlines():
            parts = line.split('\t')
            status[parts[1]] = (parts[0], parts[2] if len(parts) > 2 else '')
        return [status[p] for p in paths]


def main():
    if DOCS_MODE:
        return docs_main()
    items = collect()
    seen = set()
    uniq = []
    for src, origin, mode in items:
        if not src.strip():
            continue
        h = hashlib.sha1((mode + src).encode()).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        uniq.append((src, origin, mode))
    # 実 DW で分類する
    with tempfile.TemporaryDirectory() as td:
        paths = []
        for i, (src, origin, mode) in enumerate(uniq):
            p = os.path.join(td, f'{i:05d}' + ('.mod.dwl' if mode == 'm' else '.dwl'))
            open(p, 'w', encoding='utf-8').write(src)
            paths.append(p)
        out = subprocess.run([ORACLE, '-files'], input='\n'.join(paths).encode(), capture_output=True,
                             check=True).stdout.decode()
        status = {}
        for line in out.splitlines():
            parts = line.split('\t')
            status[parts[1]] = (parts[0], parts[2] if len(parts) > 2 else '')
    for d in (OUT_OK, OUT_BAD):
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(d):
            if f.endswith('.dwl') or f == 'INDEX.tsv':
                os.remove(os.path.join(d, f))
    idx_ok = []
    idx_bad = []
    n_ok = n_bad = 0
    for i, (src, origin, mode) in enumerate(uniq):
        tmp = os.path.join(td, f'{i:05d}' + ('.mod.dwl' if mode == 'm' else '.dwl'))
        st, msg = status[tmp]
        ext = '.mod.dwl' if mode == 'm' else '.dwl'
        if st == 'OK':
            n_ok += 1
            name = f'{n_ok:04d}-{slug(origin)}{ext}'
            open(os.path.join(OUT_OK, name), 'w', encoding='utf-8').write(src)
            idx_ok.append(f'{name}\t{origin}')
        else:
            n_bad += 1
            name = f'{n_bad:04d}-{slug(origin)}{ext}'
            open(os.path.join(OUT_BAD, name), 'w', encoding='utf-8').write(src)
            idx_bad.append(f'{name}\t{origin}\t{msg}')
    open(os.path.join(OUT_OK, 'INDEX.tsv'), 'w', encoding='utf-8').write(
        '# file\torigin (tools/extract-dw-corpus.py が生成。実 DW 2.11.2 で読める)\n' + '\n'.join(idx_ok) + '\n')
    open(os.path.join(OUT_BAD, 'INDEX.tsv'), 'w', encoding='utf-8').write(
        '# file\torigin\tDW 2.11.2 のエラー (実 DW が拒否するもの)\n' + '\n'.join(idx_bad) + '\n')
    print(f'{len(items)} found, {len(uniq)} unique: {n_ok} valid -> {OUT_OK}, {n_bad} invalid -> {OUT_BAD}')


if __name__ == '__main__':
    main()
