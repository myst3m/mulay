#!/usr/bin/env python3
"""実 DataWeave パーサの AST (dw-parse-oracle -json の出力) を mulay.dw.astdump と同じ S 式にする。

mulay の AST と DW の AST は作りが違う (NullSafeNode で包む、++ を関数呼び出しにする、x..a を
Descendants の後の ValueSelector にする、など)。ここで mulay の表記へ正規化してから比べる。
DW の AST で区別できない綴りの違い (キーを引用したか、`!` と `not`) はソースの文字を見て決める。
対応していない形に出会ったら Unsupported を投げる (その例は golden にしない)。

使い方 (モジュールとして): run_oracle(list of (mode, src)) -> list of dict, convert(src, ast) -> str
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))


class Unsupported(Exception):
    pass


def run_oracle(items):
    """items: [(mode 'e'|'m', src)] -> [{'ast': ...} | {'err': msg}]"""
    payload = "".join(f"{m}\n{src}\x01\n" for m, src in items)
    out = subprocess.run([os.path.join(HERE, "dw-parse-oracle"), "-json"], input=payload.encode(),
                         capture_output=True, check=True).stdout.decode()
    res = [json.loads(line) for line in out.splitlines() if line.strip()]
    assert len(res) == len(items), (len(res), len(items))
    return res


def quote(s):
    out = ['"']
    for ch in s:
        o = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == '\\':
            out.append('\\\\')
        elif ch == '\n':
            out.append('\\n')
        elif ch == '\t':
            out.append('\\t')
        elif ch == '\r':
            out.append('\\r')
        elif o < 32:
            out.append('\\u00%02x' % o)
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def unescape(raw):
    """DW の文字列エスケープ (mulay.dw.parse/unescape と同じ規則)"""
    out = []
    i = 0
    n = len(raw)
    simple = {'n': '\n', 't': '\t', 'r': '\r', 'b': '\b', 'f': '\f', '\\': '\\', '/': '/', '"': '"',
              "'": "'", '`': '`', '$': '$'}
    while i < n:
        c = raw[i]
        if c == '\\' and i + 1 < n:
            d = raw[i + 1]
            if d in simple:
                out.append(simple[d])
                i += 2
                continue
            if d == 'u':
                h = raw[i + 2:i + 6]
                try:
                    cp = int(h, 16) if len(h) == 4 else -1
                except ValueError:
                    cp = -1
                if cp < 0:
                    out.append(raw[i:i + 2])
                    i += 2
                    continue
                if 0xD800 <= cp <= 0xDBFF and raw[i + 6:i + 8] == '\\u':
                    try:
                        lo = int(raw[i + 8:i + 12], 16)
                    except ValueError:
                        lo = -1
                    if 0xDC00 <= lo <= 0xDFFF:
                        out.append(chr(0x10000 + (cp - 0xD800) * 1024 + (lo - 0xDC00)))
                        i += 12
                        continue
                out.append(chr(cp) if not (0xD800 <= cp <= 0xDFFF) else '�')
                i += 6
                continue
            out.append(raw[i:i + 2])
            i += 2
            continue
        if c == '\\':
            out.append('\\')
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def ident_ok(s):
    if not s:
        return False
    c0 = s[0]
    if not (c0.isascii() and (c0.isalpha() or c0 == '_')) and ord(c0) < 128:
        return False
    for ch in s[1:]:
        if ord(ch) < 128 and not (ch.isalnum() or ch == '_'):
            return False
    return True


def qname(ns, nm):
    n = nm if ident_ok(nm) else quote(nm)
    return n if not ns else f"{ns}#{n}"


OPS = {
    'AdditionOpId': '+', 'SubtractionOpId': '-', 'MultiplicationOpId': '*', 'DivisionOpId': '/',
    'RightShiftOpId': '>>', 'LeftShiftOpId': '<<', 'LessThanOpId': '<', 'GreaterThanOpId': '>',
    'LessOrEqualThanOpId': '<=', 'GreaterOrEqualThanOpId': '>=', 'EqOpId': '==', 'NotEqOpId': '!=',
    'SimilarOpId': '~=',
}
TEMPORAL = {
    'LocalDateNode': 'date', 'DateTimeNode': 'datetime', 'LocalDateTimeNode': 'localdatetime',
    'TimeNode': 'time', 'LocalTimeNode': 'localtime', 'TimeZoneNode': 'timezone', 'PeriodNode': 'period',
}


class Conv:
    def __init__(self, src):
        # DW の位置は Java の文字 (UTF-16) 単位
        self.src = src

    def ch(self, n):
        s = n.get('s')
        if s is None or s < 0 or s >= len(self.src):
            return ''
        return self.src[s]

    # --- 名前 ---
    def name(self, n):
        if n is None:
            return ''
        t = n['t']
        if t == 'NameIdentifier':
            if len(n['c']) > 1 and n['c'][1] is not None:  # loader!name
                return n['c'][1] + '!' + n['c'][0]
            return n['c'][0]
        if t == 'VariableReferenceNode':
            return self.name(n['c'][0])
        if t == 'StringNode':
            return unescape(n['c'][0])
        raise Unsupported('name ' + t)

    def bind(self, n):
        nm = self.name(n)
        return '_' if nm in ('$', '$$') else nm

    def ns(self, n):
        if n is None:
            return ''
        if n['t'] == 'NamespaceNode':
            return self.name(n['c'][0])
        raise Unsupported('ns ' + n['t'])

    # --- 文字列 ---
    def strnode(self, n):
        t = n['t']
        if t == 'StringNode':
            return quote(unescape(n['c'][0]))
        if t == 'StringInterpolationNode':
            parts = n['c'][0]
            if len(parts) == 0:
                return '""'
            if len(parts) == 1 and parts[0]['t'] == 'StringNode':
                return quote(unescape(parts[0]['c'][0]))
            out = []
            for p in parts:
                if p['t'] == 'StringNode':
                    txt = unescape(p['c'][0])
                    if txt == '':
                        continue
                    out.append(quote(txt))
                else:
                    out.append(self.expr(p))
            return '(str ' + ' '.join(out) + ')'
        raise Unsupported('str ' + t)

    def is_plain_str(self, n):
        return n['t'] == 'StringNode' or (n['t'] == 'StringInterpolationNode' and all(p['t'] == 'StringNode' for p in n['c'][0]))

    def plain_text(self, n):
        if n['t'] == 'StringNode':
            return unescape(n['c'][0])
        return ''.join(unescape(p['c'][0]) for p in n['c'][0])

    # --- 選択子の名前 NameNode(StringNode|Interp, ns) ---
    def selname(self, nn, prefix):
        """(形, 動的か)"""
        key = nn['c'][0]
        ns = self.ns(nn['c'][1])
        if self.is_plain_str(key):
            return prefix + qname(ns, self.plain_text(key)), False
        return '[' + self.strnode(key) + ']', True

    # --- 式 ---
    def exprs(self, ns):
        return ' '.join(self.expr(x) for x in ns)

    def expr(self, n):
        t = n['t']
        c = n['c']
        if t == 'NullSafeNode':
            return self.expr(c[0])
        if t == 'NullUnSafeNode':
            return '(assert ' + self.expr(c[0]) + ')'
        if t == 'ExistsSelectorNode':
            return '(exists ' + self.expr(c[0]) + ')'
        if t == 'NumberNode':
            return c[0]
        if t == 'BooleanNode':
            return c[0]
        if t == 'NullNode':
            return 'null'
        if t in ('StringNode', 'StringInterpolationNode'):
            return self.strnode(n)
        if t == 'RegexNode':
            return '(regex ' + quote(c[0]) + ')'
        if t in TEMPORAL:
            return '(' + TEMPORAL[t] + ' ' + quote(c[0]) + ')'
        if t == 'VariableReferenceNode':
            return self.name(c[0])
        if t == 'ArrayNode':
            els = []
            for e in c[0]:
                if e['t'] == 'ConditionalNode':
                    els.append('(when ' + self.expr(e['c'][0]) + ' ' + self.expr(e['c'][1]) + ')')
                else:
                    els.append(self.expr(e))
            return '(arr ' + ' '.join(els) + ')' if els else '(arr)'
        if t == 'ObjectNode':
            es = [self.entry(e) for e in c[0]]
            return '(obj ' + ' '.join(es) + ')' if es else '(obj)'
        if t == 'AndNode':
            return '(and ' + self.expr(c[0]) + ' ' + self.expr(c[1]) + ')'
        if t == 'OrNode':
            return '(or ' + self.expr(c[0]) + ' ' + self.expr(c[1]) + ')'
        if t == 'DefaultNode':
            return '(default ' + self.expr(c[0]) + ' ' + self.expr(c[1]) + ')'
        if t == 'UnaryOpNode':
            op = c[0]['t']
            if op == 'NotOpId':
                return ('(! ' if self.ch(n) == '!' else '(not ') + self.expr(c[1]) + ')'
            if op == 'MinusOpId':
                return '(- ' + self.expr(c[1]) + ')'
            if op == 'DescendantsSelectorOpId':
                return '(sel ' + self.expr(c[1]) + ' ..)'
            if op == 'AllAttributesSelectorOpId':
                return '(sel ' + self.expr(c[1]) + ' .@)'
            if op == 'NamespaceSelectorOpId':
                return '(sel ' + self.expr(c[1]) + ' .#)'
            if op == 'AllSchemaSelectorOpId':
                return '(sel ' + self.expr(c[1]) + ' .^)'
            raise Unsupported('unary ' + op)
        if t == 'BinaryOpNode':
            return self.binop(n)
        if t == 'FunctionCallNode':
            f = c[0]
            args = c[1]['c'][0] if c[1]['c'] else []
            if f['t'] == 'VariableReferenceNode' and self.name(f) in ('++', '--') and len(args) == 2:
                return '(' + self.name(f) + ' ' + self.expr(args[0]) + ' ' + self.expr(args[1]) + ')'
            if not args:
                return '(call ' + self.expr(f) + ')'
            return '(call ' + self.expr(f) + ' ' + self.exprs(args) + ')'
        if t == 'IfNode':
            return '(if ' + self.expr(c[1]) + ' ' + self.expr(c[0]) + ' ' + self.expr(c[2]) + ')'
        if t == 'UnlessNode':
            return '(if (not ' + self.expr(c[1]) + ') ' + self.expr(c[0]) + ' ' + self.expr(c[2]) + ')'
        if t == 'FunctionNode':
            return self.lam(n)
        if t == 'PatternMatcherNode':
            cases = [self.case(x) for x in c[1]['c'][0]]
            return '(match ' + self.expr(c[0]) + ''.join(' ' + x for x in cases) + ')'
        if t == 'UpdateNode':
            cases = [self.updcase(x) for x in c[1]['c'][0]]
            return '(update ' + self.expr(c[0]) + ''.join(' ' + x for x in cases) + ')'
        if t == 'DoBlockNode':
            ds = [self.decl(d) for d in c[0]['c'][0]]
            return '(do (' + ' '.join(ds) + ') ' + self.expr(c[1]) + ')'
        if t == 'UsingNode':
            ds = ['(var ' + self.name(a['c'][0]) + ' ' + self.expr(a['c'][1]) + ')' for a in c[0]['c'][0]]
            return '(using (' + ' '.join(ds) + ') ' + self.expr(c[1]) + ')'
        raise Unsupported('expr ' + t)

    def binop(self, n):
        c = n['c']
        op = c[0]['t']
        tgt = c[1]
        if op in OPS:
            return '(' + OPS[op] + ' ' + self.expr(tgt) + ' ' + self.expr(c[2]) + ')'
        if op == 'AsOpId':
            return '(as ' + self.expr(tgt) + ' ' + self.ty(c[2]) + ')'
        if op == 'IsOpId':
            return '(is ' + self.expr(tgt) + ' ' + self.ty(c[2]) + ')'
        if op == 'MetadataInjectorOpId':
            return '(<~ ' + self.expr(tgt) + ' ' + self.expr(c[2]) + ')'
        # 選択子。x..a は DW では Descendants(x) の後の ValueSelector
        desc = tgt['t'] == 'UnaryOpNode' and tgt['c'][0]['t'] == 'DescendantsSelectorOpId'
        if op == 'ValueSelectorOpId':
            if desc:
                form, dyn = self.selname(c[2], '..')
                if dyn:
                    raise Unsupported('dynamic descendant')
                return '(sel ' + self.expr(tgt['c'][1]) + ' ' + form + ')'
            form, dyn = self.selname(c[2], '.')
            return '(sel ' + self.expr(tgt) + ' ' + form + ')'
        if op == 'MultiValueSelectorOpId':
            form, dyn = self.selname(c[2], '..*' if desc else '.*')
            if dyn:
                raise Unsupported('dynamic multi')
            base = tgt['c'][1] if desc else tgt
            return '(sel ' + self.expr(base) + ' ' + form + ')'
        if op == 'AttributeValueSelectorOpId':
            key = c[2]['c'][0]
            if not self.is_plain_str(key):
                raise Unsupported('dyn attr')
            return '(sel ' + self.expr(tgt) + ' .@' + qname(self.ns(c[2]['c'][1]), self.plain_text(key)) + ')'
        if op == 'MultiAttributeValueSelectorOpId':
            key = c[2]['c'][0]
            if not self.is_plain_str(key):
                raise Unsupported('dyn attr')
            return '(sel ' + self.expr(tgt) + ' .*@' + qname(self.ns(c[2]['c'][1]), self.plain_text(key)) + ')'
        if op == 'ObjectKeyValueSelectorOpId':
            return '(sel ' + self.expr(tgt) + ' .&' + qname('', self.plain_text(c[2]['c'][0])) + ')'
        if op == 'SchemaValueSelectorOpId':
            return '(sel ' + self.expr(tgt) + ' .^' + qname('', self.plain_text(c[2]['c'][0])) + ')'
        if op == 'DynamicSelectorOpId':
            ix = c[2]
            if ix['t'] == 'FunctionCallNode' and ix['c'][0]['t'] == 'VariableReferenceNode' \
                    and self.name(ix['c'][0]) == 'to' and len(ix['c'][1]['c'][0]) == 2:
                a, b = ix['c'][1]['c'][0]
                return '(sel ' + self.expr(tgt) + ' [' + self.expr(a) + ' to ' + self.expr(b) + '])'
            return '(sel ' + self.expr(tgt) + ' [' + self.expr(ix) + '])'
        if op == 'FilterSelectorOpId':
            fn = c[2]
            if fn['t'] != 'FunctionNode':
                raise Unsupported('filter')
            return '(sel ' + self.expr(tgt) + ' [?' + self.expr(fn['c'][1]) + '])'
        raise Unsupported('binop ' + op)

    def key(self, kn):
        """KeyNode / DynamicKeyNode -> (表記, attrs)"""
        t = kn['t']
        if t == 'KeyNode':
            k = kn['c'][0]
            ns = self.ns(kn['c'][1])
            attrs = kn['c'][2]
            if self.is_plain_str(k) and self.ch(k) not in ('"', "'", '`'):
                ks = qname(ns, self.plain_text(k))
            else:
                if ns:
                    raise Unsupported('ns quoted key')
                ks = self.strnode(k) if k['t'] == 'StringInterpolationNode' or self.plain_text(k) != '' else '""'
            return ks, attrs
        if t == 'DynamicKeyNode':
            return '(dyn ' + self.expr(kn['c'][0]) + ')', kn['c'][1]
        raise Unsupported('key ' + t)

    def attrs(self, an):
        if an is None:
            return ''
        out = []
        for nv in an['c'][0]:
            if nv['t'] != 'NameValuePairNode':
                out.append('(spread ' + self.expr(nv) + ')')
                continue
            nm = nv['c'][0]
            k = nm['c'][0]
            if not self.is_plain_str(k):
                raise Unsupported('dyn attr name')
            s = '(' + qname(self.ns(nm['c'][1]), self.plain_text(k)) + ' ' + self.expr(nv['c'][1])
            if nv['c'][2] is not None:
                s += ' :if ' + self.expr(nv['c'][2])
            out.append(s + ')')
        return ' :attrs (' + ' '.join(out) + ')' if out else ''

    def entry(self, e):
        if e['t'] == 'KeyValuePairNode':
            ks, attrs = self.key(e['c'][0])
            s = '(' + ks + self.attrs(attrs) + ' ' + self.expr(e['c'][1])
            if e['c'][2] is not None:
                s += ' :if ' + self.expr(e['c'][2])
            return s + ')'
        return '(spread ' + self.expr(e) + ')'

    def param(self, p):
        nm = self.name(p['c'][0])
        dflt = p['c'][1]
        ty = p['c'][2]
        if dflt is None and ty is None:
            return nm
        s = '(' + nm
        if ty is not None:
            s += ' :type ' + self.ty(ty)
        if dflt is not None:
            s += ' :default ' + self.expr(dflt)
        return s + ')'

    def params(self, fp):
        ps = fp['c'][0] if fp['c'] else []
        return '(' + ' '.join(self.param(p) for p in ps) + ')'

    def lam(self, n):
        c = n['c']
        s = '(fn ' + self.params(c[0])
        if c[2] is not None:
            s += ' :ret ' + self.ty(c[2])
        return s + ' ' + self.expr(c[1]) + ')'

    def case(self, x):
        t = x['t']
        c = x['c']
        if t == 'LiteralPatternNode':
            return '(case ' + self.bind(c[1]) + ' (lit ' + self.expr(c[0]) + ') ' + self.expr(c[2]) + ')'
        if t == 'ExpressionPatternNode':
            return '(case ' + self.bind(c[1]) + ' (guard ' + self.expr(c[0]) + ') ' + self.expr(c[2]) + ')'
        if t == 'TypePatternNode':
            return '(case ' + self.bind(c[1]) + ' (is ' + self.ty(c[0]) + ') ' + self.expr(c[2]) + ')'
        if t == 'RegexPatternNode':
            return '(case ' + self.bind(c[1]) + ' (matches ' + self.expr(c[0]) + ') ' + self.expr(c[2]) + ')'
        if t == 'DeconstructArrayPatternNode':
            return '(case _ (arr ' + self.name(c[0]) + ' ' + self.name(c[1]) + ') ' + self.expr(c[2]) + ')'
        if t == 'DeconstructObjectPatternNode':
            return '(case _ (obj ' + self.name(c[0]) + ' ' + self.name(c[1]) + ' ' + self.name(c[2]) + ') ' + self.expr(c[3]) + ')'
        if t == 'DefaultPatternNode':
            return '(case ' + self.bind(c[1]) + ' else ' + self.expr(c[0]) + ')'
        if t == 'EmptyArrayPatternNode':
            return '(case _ (lit (arr)) ' + self.expr(c[0]) + ')'
        if t == 'EmptyObjectPatternNode':
            return '(case _ (lit (obj)) ' + self.expr(c[0]) + ')'
        raise Unsupported('pattern ' + t)

    def updsel(self, s, acc):
        while s is not None:
            t = s['t']
            c = s['c']
            if t == 'FieldNameUpdateSelectorNode':
                form, dyn = self.selname(c[0], '.')
                acc.append(form)
            elif t == 'MultiFieldNameUpdateSelectorNode':
                form, dyn = self.selname(c[0], '.*')
                acc.append(form)
            elif t == 'AttributeNameUpdateSelectorNode':
                form, dyn = self.selname(c[0], '.@')
                acc.append(form)
            elif t == 'ArrayIndexUpdateSelectorNode':
                acc.append('[' + self.expr(c[0]) + ']')
            else:
                raise Unsupported('updsel ' + t)
            s = c[1]
        return acc

    def updcase(self, x):
        c = x['c']
        path = self.updsel(c[2], [])
        s = '(case ' + self.bind(c[0]) + ' ' + self.bind(c[1]) + ' (' + ' '.join(path) + ')'
        if c[3]:
            s += ' !'
        if c[4] is not None:
            s += ' :if ' + self.expr(c[4])
        return s + ' ' + self.expr(c[5]) + ')'

    # --- 型 ---
    def tys(self, ts):
        return ' '.join(self.ty(t) for t in ts)

    def schema_obj(self, sn):
        es = []
        for p in sn['c'][0]:
            k = p['c'][0]
            if p['c'][2] is not None:
                raise Unsupported('schema cond')
            if k['t'] == 'StringNode' and self.ch(k) not in ('"', "'", '`'):
                ks = qname('', unescape(k['c'][0]))
            else:
                ks = self.strnode(k)
            es.append('(' + ks + ' ' + self.expr(p['c'][1]) + ')')
        return '(obj ' + ' '.join(es) + ')' if es else '(obj)'

    def with_schema(self, base, sn, meta=None):
        # T {..} (schema) と T <~ {..} (metadata)。mulay はどちらも TMeta にする
        if sn is not None:
            base = '(tmeta ' + base + ' ' + self.schema_obj(sn) + ')'
        if meta is not None:
            base = '(tmeta ' + base + ' ' + self.schema_obj(meta) + ')'
        return base

    def ty(self, n):
        t = n['t']
        c = n['c']
        if t == 'TypeReferenceNode':
            nm = self.name(c[0])
            args = c[1]
            base = nm if not args else '(' + nm + ' ' + self.tys(args) + ')'
            return self.with_schema(base, c[2], c[3] if len(c) > 3 and isinstance(c[3], dict) and c[3].get('t') == 'SchemaNode' else None)
        if t == 'UnionTypeNode':
            return self.with_schema('(| ' + self.tys(c[0]) + ')', c[1])
        if t == 'IntersectionTypeNode':
            return self.with_schema('(& ' + self.tys(c[0]) + ')', c[1])
        if t == 'LiteralTypeNode':
            return self.with_schema('(tlit ' + self.expr(c[0]) + ')', c[1])
        if t == 'FunctionTypeNode':
            ps = [p['c'][1] for p in c[0]]
            return self.with_schema('(-> (' + self.tys(ps) + ') ' + self.ty(c[1]) + ')', c[2])
        if t == 'TypeSelectorNode':
            nn = c[0]
            if not self.is_plain_str(nn['c'][0]):
                raise Unsupported('dyn type selector')
            return self.with_schema('(tsel ' + self.ty(c[1]) + ' ' + qname(self.ns(nn['c'][1]), self.plain_text(nn['c'][0])) + ')', c[2] if len(c) > 2 and isinstance(c[2], dict) and c[2].get('t') == 'SchemaNode' else None)
        if t == 'ObjectTypeNode':
            fs = []
            for f in c[0]:
                kt = f['c'][0]
                if kt['t'] == 'KeyTypeNode':
                    nt = kt['c'][0]
                    nm = nt['c'][0]
                    ns = self.ns(nt['c'][1])
                    k = '_' if nm is None else qname(ns, nm)
                else:
                    k = '_'
                rep, opt = f['c'][2], f['c'][3]
                fs.append('(' + k + ('?' if opt else '') + ('*' if rep else '') + ' ' + self.ty(f['c'][1]) + ')')
            base = '(tobj' + (' :closed' if c[3] else '') + (' :ordered' if c[4] else '') + ''.join(' ' + x for x in fs) + ')'
            return self.with_schema(base, c[1])
        raise Unsupported('type ' + t)

    # --- 宣言 ---
    def annots(self, lst):
        out = []
        for a in lst or []:
            nm = self.name(a['c'][0])
            args = a['c'][1]
            if args is None or not args['c'][0]:
                out.append('@' + nm)
            else:
                xs = ['(obj (' + self.name(x['c'][0]) + ' ' + self.expr(x['c'][1]) + '))' for x in args['c'][0]]
                out.append('(@' + nm + ' ' + ' '.join(xs) + ')')
        return out

    def generics(self, tp):
        if tp is None:
            return ''
        names = [self.name(x['c'][0]) for x in tp['c'][0]]
        return ' :generics (' + ' '.join(names) + ')' if names else ''

    def decl(self, d):
        t = d['t']
        c = d['c']
        if t == 'VarDirective':
            return '(var ' + self.name(c[0]) + ('' if c[2] is None else ' :type ' + self.ty(c[2])) + ' ' + self.expr(c[1]) + ')'
        if t == 'FunctionDirectiveNode':
            fn = c[1]
            if fn['t'] != 'FunctionNode':
                raise Unsupported('fundir ' + fn['t'])
            fc = fn['c']
            ans = self.annots(c[2] if len(c) > 2 else [])
            s = '(fun ' + self.name(c[0]) + self.generics(fc[3])
            if ans:
                s += ' :annots (' + ' '.join(ans) + ')'
            s += ' ' + self.params(fc[0])
            if fc[2] is not None:
                s += ' :ret ' + self.ty(fc[2])
            return s + ' ' + self.expr(fc[1]) + ')'
        if t == 'TypeDirective':
            return '(type ' + self.name(c[0]) + self.generics(c[1]) + ' ' + self.ty(c[2]) + ')'
        if t == 'NamespaceDirective':
            return '(ns ' + self.name(c[0]) + ' ' + quote(c[1]['c'][0]) + ')'
        if t == 'ImportDirective':
            mid = c[0]['c'][0]
            mod = self.name(mid)
            alias = c[0]['c'][1]
            els = c[1]['c'][0] if c[1]['c'] else []
            star = any(self.name(e['c'][0]) == '*' for e in els)
            names = [e for e in els if self.name(e['c'][0]) != '*']
            s = '(import ' + mod + (' :star' if star else '')
            if names:
                ns = []
                for e in names:
                    a = e['c'][1]
                    ns.append(self.name(e['c'][0]) if a is None else '(' + self.name(e['c'][0]) + ' :as ' + self.name(a) + ')')
                s += ' :names (' + ' '.join(ns) + ')'
            if alias is not None:
                s += ' :as ' + self.name(alias)
            return s + ')'
        if t == 'AnnotationDirectiveNode':
            ps = []
            for p in c[1]['c'][0]:
                nm = self.name(p['c'][0])
                ty = p['c'][1]
                dflt = p['c'][2] if len(p['c']) > 2 else None
                if ty is None and dflt is None:
                    ps.append(nm)
                else:
                    s = '(' + nm + ('' if ty is None else ' :type ' + self.ty(ty)) + ('' if dflt is None else ' :default ' + self.expr(dflt)) + ')'
                    ps.append(s)
            return '(annotation ' + self.name(c[0]) + ' (' + ' '.join(ps) + '))'
        raise Unsupported('decl ' + t)

    def directive(self, d):
        t = d['t']
        c = d['c']
        if t == 'OutputDirective':
            fmt, ct, opts = c[0], c[1], c[2]
            name, ty = '', None
        else:
            name = self.name(c[0])
            fmt, ct, opts, ty = c[1], c[2], c[3], c[4]
        if ct is not None:
            mime = ct['c'][0]
            with_ = '' if fmt is None else ' :with ' + fmt['c'][0]
        else:
            mime = fmt['c'][0] if fmt is not None else ''
            with_ = ''
        s = '(' + ('output' if t == 'OutputDirective' else 'input') + ('' if not name else ' ' + name)
        if ty is not None:
            s += ' :type ' + self.ty(ty)
        s += ' ' + quote(mime) + with_
        if opts:
            es = ['(' + o['c'][0]['c'][0] + ' ' + self.expr(o['c'][1]) + ')' for o in opts]
            s += ' (obj ' + ' '.join(es) + ')'
        return s + ')'

    def script(self, ast, module=False):
        if ast['t'] == 'ModuleNode':
            dirs_nodes = ast['c'][1]
            body = 'null'
        else:
            dirs_nodes = ast['c'][0]['c'][0]
            body = self.expr(ast['c'][1])
        version = ''
        dirs, decls = [], []
        for d in dirs_nodes:
            t = d['t']
            if t == 'VersionDirective':
                version = d['c'][0]['c'][0] + '.' + d['c'][1]['c'][0]
            elif t in ('OutputDirective', 'InputDirective'):
                dirs.append(self.directive(d))
            else:
                decls.append(self.decl(d))
        if '%dw' not in self.src:
            version = ''
        s = '(script'
        if version:
            s += ' :version ' + quote(version)
        if dirs:
            s += ' (dirs ' + ' '.join(dirs) + ')'
        if decls:
            s += ' (decls ' + ' '.join(decls) + ')'
        return s + ' ' + body + ')'


def convert(src, ast):
    try:
        return Conv(src).script(ast)
    except Unsupported:
        raise
    except Exception as e:  # 想定外の形: その例は比べない
        raise Unsupported(f'{type(e).__name__}: {e}')


if __name__ == '__main__':
    import sys
    src = sys.stdin.read()
    mode = 'm' if len(sys.argv) > 1 and sys.argv[1] == '-m' else 'e'
    r = run_oracle([(mode, src)])[0]
    if 'err' in r:
        print('ERR', r['err'])
    else:
        try:
            print(convert(src, r['ast']))
        except Unsupported as e:
            print('UNSUPPORTED', e)
