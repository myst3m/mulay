#!/usr/bin/env python3
"""実コネクタの XSD にあって、mulay の src に名前が出てこない属性の表 (src/mulay/mule/ignored.clay) を作る・確かめる。

  tools/ignored-attrs.py gen     Anypoint Studio のキャッシュの XSD から表を作り直す (名前空間ごと)
  tools/ignored-attrs.py check   表の属性が src のどこかで使われていないか確かめる (XSD は要らない。tools/test.sh が呼ぶ)

mulay validate / run が、アプリの XML にこの属性が書かれていると「対応していないので無視する」と警告する (mule/lint)。
属性を実装したら gen し直す (check が、実装済みなのに表に残っているものを見つける)。
"""
import glob, os, re, sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUDIO = os.path.expanduser('~/AnypointStudio/')
OUT = os.path.join(ROOT, 'src/mulay/mule/ignored.clay')
XS = '{http://www.w3.org/2001/XMLSchema}'

# (名前空間の XSD、版は実 Mule 4.11.3 の fixture に合わせる)
XSDS = [
    'com/mulesoft/connectors/mule-salesforce-connector/11.3.3/mule-salesforce.xsd',
    'org/mule/connectors/mule-file-connector/1.5.6/mule-file.xsd',
    'org/mule/connectors/mule-sftp-connector/2.7.2/mule-sftp.xsd',
    'org/mule/connectors/mule-db-connector/1.16.3/mule-db.xsd',
    'org/mule/connectors/mule-vm-connector/2.0.2/mule-vm.xsd',
    'com/mulesoft/connectors/mule4-a2a-connector/1.1.1/mule-a2a.xsd',
    'com/mulesoft/connectors/mule-mcp-connector/1.4.0/mule-mcp.xsd',
    'org/mule/connectors/mule-http-connector/1.11.3/mule-http.xsd',
    'org/mule/connectors/mule-objectstore-connector/1.3.1/*.xsd',
    'com/mulesoft/modules/mule-secure-configuration-property-module/1.2.5/*.xsd',
    'org/mule/modules/mule-validation-module/2.0.8/mule-validation.xsd',   # 2.0.11 の XSD は無い (属性は同じ)
    'com/mulesoft/connectors/mule4-vectors-connector/1.0.0/mule-ms-vectors.xsd',
    'org/mule/connectors/mule-wsc-connector/2.2.2/mule-wsc-connector-2.2.2-mule-plugin.xsd',
]
# どの要素にもある・副作用の無い属性は警告しない
HARMLESS = {'name', 'config-ref', 'target', 'targetValue', 'primaryNodeOnly', 'transactionalAction',
            'driverClassName'}   # driverClassName: mulay は url でドライバを選ぶ


# XSD を表に持たないコネクタのファイル。そこの文字列は表のどの名前空間の属性も実装しない
# (conn/grpc の子要素 "request-headers" を http の requestHeaders と取り違えないため)
NO_XSD = {'conn/grpc.clay'}


def src_text():
    out = []
    for g in glob.glob(os.path.join(ROOT, 'src/**/*.clay'), recursive=True):
        # ignored.clay は表そのもの。lib と db は mule の層に依存せず XML の属性を読まないので、そこの文字列
        # (lib/tlds の "origins"、lib/sqlexec の "table" など) を属性の実装と取り違えないよう見ない
        rel = os.path.relpath(g, os.path.join(ROOT, 'src/mulay'))
        if rel == 'mule/ignored.clay' or rel.split(os.sep)[0] in ('lib', 'db') or rel in NO_XSD:
            continue
        out.append(open(g, encoding='utf-8').read())
    return '\n'.join(out)


def kebab(a):
    return re.sub(r'([A-Z])', lambda m: '-' + m.group(1).lower(), a)


# 属性の形 (大域の要素の名前を指す) は読まないが、同じ名前の子要素 (kebab の形) は読むもの。kebab の一致で実装とみなさない
CHILD_ONLY = {'pollingRequestHeaders', 'pollingRequestUriParams', 'pollingRequestQueryParams', 'responseValidator'}


def used(a, text):
    if a in CHILD_ONLY:
        return ('"%s"' % a) in text
    return ('"%s"' % a) in text or ('"%s"' % kebab(a)) in text


def table():
    text = src_text()
    rows = {}
    for pat in XSDS:
        fs = sorted(glob.glob(STUDIO + '**/' + pat, recursive=True, include_hidden=True))
        if not fs:
            print('XSD が無い:', pat, file=sys.stderr)
            continue
        t = ET.parse(fs[-1]).getroot()
        ns = t.get('targetNamespace')
        names = set()
        for a in t.iter(XS + 'attribute'):
            n = a.get('name')
            if n and ':' not in n and n not in HARMLESS:
                names.add(n)
        rows.setdefault(ns, set()).update(n for n in names if not used(n, text))
    return rows


def gen():
    rows = table()
    lines = [
        '(ns mulay.mule.ignored)', '',
        '(def TABLE: Vec(Vec(Str)) [']
    for ns in sorted(rows):
        if rows[ns]:
            lines.append('  ["%s" ",%s,"]' % (ns, ','.join(sorted(rows[ns]))))
    lines.append('])')
    open(OUT, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('wrote', OUT, sum(len(v) for v in rows.values()), 'attribute(s)')


def check():
    text = src_text()
    bad = []
    for m in re.finditer(r'\["([^"]+)" ",([^"]*),"\]', open(OUT, encoding='utf-8').read()):
        for a in m.group(2).split(','):
            if a and used(a, text):
                bad.append((m.group(1), a))
    for ns, a in bad:
        print('実装済みなのに ignored.clay に残っている:', ns, a, '(tools/ignored-attrs.py gen)', file=sys.stderr)
    return 1 if bad else 0


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('gen', 'check'):
        print(__doc__)
        sys.exit(2)
    if sys.argv[1] == 'gen':
        gen()
    else:
        sys.exit(check())
