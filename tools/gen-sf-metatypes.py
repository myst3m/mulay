#!/usr/bin/env python3
"""Salesforce のメタデータ API の型の表 (src/mulay/conn/sf_metatypes.clay) を作る。

一次資料は実コネクタ (mule-salesforce-connector 11.3.4) が使う force-metadata-api 65.0.0 の WSC のクラスと、
コネクタの MetadataType (型の名前 → WSC のクラス)。どちらも ~/.m2 の jar を javap で読む。

実コネクタは read-metadata の結果を WSC のオブジェクトからリフレクションで Map にし (宣言したフィールドすべてと
その __is_set)、create / update / upsert-metadata の Map を BeanUtils で WSC のオブジェクトにする。mulay は
この表でフィールドの名前と型を知る。

使い方: tools/gen-sf-metatypes.py > src/mulay/conn/sf_metatypes.clay
"""
import os, re, subprocess, sys, tempfile, zipfile

M2 = os.path.expanduser('~/.m2/repository')
META_JAR = f'{M2}/com/force/api/force-metadata-api/65.0.0/force-metadata-api-65.0.0.jar'
CONN_JAR = f'{M2}/com/mulesoft/connectors/mule-salesforce-connector/11.3.4/mule-salesforce-connector-11.3.4-mule-plugin.jar'
JAVAP = '/usr/lib/jvm/java-17-openjdk-amd64/bin/javap'
PKG = 'com.sforce.soap.metadata.'


def javap(args, cp):
    return subprocess.run([JAVAP, '-cp', cp] + args, capture_output=True, text=True, check=True).stdout


def main():
    tmp = tempfile.mkdtemp()
    names = [n for n in zipfile.ZipFile(META_JAR).namelist() if n.startswith('com/sforce/soap/metadata/') and n.endswith('.class') and '$' not in n]
    classes = [n[:-6].replace('/', '.') for n in names]
    out = javap(['-p'] + classes, META_JAR)
    # クラスごとの宣言
    info = {}   # simple -> (super, [(field, javatype)], is_enum)
    cur = None
    for line in out.split('\n'):
        m = re.match(r'^(?:public |final |abstract )*(?:class|enum) (\S+)(?: extends (\S+))?', line)
        if m:
            cur = m.group(1).replace(PKG, '')
            sup = (m.group(2) or '').replace(PKG, '')
            info[cur] = [sup, [], sup.startswith('java.lang.Enum')]
            continue
        m = re.match(r'^\s+private ([\w.$\[\]<>, ]+) (\w+);$', line)
        if m and cur and 'static' not in line and 'transient' not in line:
            info[cur][1].append((m.group(2), m.group(1)))
    # 列挙の値 (XML の値が Java の名前と違うもの): static 初期化の "名前, 序数, 値"
    enums = [c for c, v in info.items() if v[2]]
    enum_vals = {}
    code = javap(['-p', '-c'] + [PKG + e for e in enums], META_JAR)
    cur = None
    pend = []
    for line in code.split('\n'):
        m = re.match(r'^(?:public |final )*(?:class|enum) (\S+)', line)
        if m:
            cur = m.group(1).replace(PKG, ''); pend = []; continue
        m = re.search(r'// String (.*)$', line)
        if m and cur:
            pend.append(m.group(1))
        if 'invokespecial' in line and '"<init>":(Ljava/lang/String;ILjava/lang/String;)V' in line and cur:
            if len(pend) >= 2:
                name, val = pend[-2], pend[-1]
                if name != val:
                    enum_vals.setdefault(cur, []).append((val, name))
            pend = []

    def kind(t):
        t = t.strip()
        if t.endswith('[]'):
            if t == 'byte[]':
                return 'y'
            return 'a' + kind(t[:-2])
        base = {'java.lang.String': 's', 'boolean': 'b', 'int': 'i', 'long': 'l', 'double': 'd',
                'java.lang.Boolean': 'B', 'java.lang.Integer': 'I', 'java.lang.Double': 'D', 'java.lang.Long': 'L',
                'java.util.Calendar': 'c', 'java.util.Date': 'c', 'com.sforce.ws.types.Time': 't',
                'java.lang.Object': 's'}
        if t in base:
            return base[t]
        s = t.replace(PKG, '')
        if s in info:
            return ('e:' if info[s][2] else 'o:') + s
        return 's'

    # MetadataType: 型の名前 → クラス (static 初期化の "名前, 序数, クラス")
    ccode = javap(['-p', '-c', 'org.mule.extension.salesforce.internal.service.soap.MetadataType'], CONN_JAR)
    types = []
    pend = []
    for line in ccode.split('\n'):
        m = re.search(r'// String (\w+)$', line)
        if m:
            pend = [m.group(1)]
            continue
        m = re.search(r'// class (?:com/sforce/soap/metadata|org/mule/extension/salesforce/internal/service/soap)/(\w+)$', line)
        if m and pend:
            types.append((pend[0], m.group(1)))
            pend = []
    # 表に入れるクラス: 型のクラスから辿れるもの
    need = set()
    stack = [c for _, c in types] + ['Metadata']
    while stack:
        c = stack.pop()
        if c in need or c not in info:
            continue
        need.add(c)
        sup = info[c][0]
        if sup and sup in info:
            stack.append(sup)
        for f, t in info[c][1]:
            if f.endswith('__is_set'):
                continue
            k = kind(t)
            if ':' in k:
                stack.append(k.split(':', 1)[1])

    def enc(c):
        sup, fs, is_enum = info[c]
        if is_enum:
            return 'E|' + ','.join(f'{v}={n}' for v, n in enum_vals.get(c, []))
        fields = [f'{f}:{kind(t)}' for f, t in fs if not f.endswith('__is_set')]
        return (sup if sup in info else '') + '|' + ','.join(fields)

    w = sys.stdout.write
    w('(ns mulay.conn.sf_metatypes)\n\n')
    w('(def TYPES: Map(Str Str)\n  {')
    w('\n   '.join(f'"{n}" "{c}"' for n, c in types))
    w('})\n\n(def CLASSES: Map(Str Str)\n  {')
    w('\n   '.join(f'"{c}" "{enc(c)}"' for c in sorted(need)))
    w('})\n')


if __name__ == '__main__':
    main()
