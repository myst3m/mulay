import yaml, json, math, sys
cases = [
 "a: 1\nb: two\nc: 3.5\n",
 "top:\n  mid:\n    leaf: x\n  other: y\nlast: z\n",
 "- a\n- b\n- - c\n  - d\n- e: 1\n  f: 2\n",
 "key:\n- x\n- y\nk2: v\n",
 "key:\n  - x\n  -   y\nk2:\n",
 "seq: [1, 2, [3, 4], {a: b}]\nmap: {x: 1, y: [a, b], 'q': \"r\"}\nempty: []\nem: {}\n",
 "[a, b: c, {d: e}]\n",
 "s1: 'it''s'\ns2: \"tab\\there\\nnl \\\"q\\\" \\\\ \\x41\\u00e9\\U0001F600\"\ns3: \"a\\\n  b\"\n",
 "plain: this is\n  a multi line\n\n  plain scalar\nnext: v\n",
 "q: \"folded\n  quoted\n\n  text\"\nr: 'single\n  folded'\n",
 "lit: |\n  line1\n    indented\n  line3\nfold: >\n  a\n  b\n\n  c\n    more\n  d\nend: x\n",
 "strip: |-\n  text\n\n\nkeep: |+\n  text\n\n\nclip: |\n  text\n\n\nlast: 1\n",
 "fs: >-\n  one\n  two\nfk: >+\n  one\n\nz: 0\n",
 "ind: |2\n    two extra\n   one extra\nx: 1\n",
 "a: &anc\n  x: 1\n  y: [1, 2]\nb: *anc\nc: &s scalar\nd: *s\n",
 "# comment\na: 1 # trailing\n# middle\nb: [1, # in flow\n  2]\nc: 'x' # after quoted\n",
 "? complex key\n: complex value\n? [a, b]\n: seq key\n",
 "n1: ~\nn2: null\nn3:\nn4: Null\nb1: true\nb2: False\ni1: -17\ni2: 0x1F\ni3: +5\nf1: 1.5\nf2: -.inf\nf3: .NaN\nf4: 6.02e+23\ns: 12abc\n",
 "t1: !!str 123\nt2: !!int \"42\"\nt3: !!float 1\nt4: !custom value\nt5: !!bool true\n",
 "url: http://example.com:8080/path\ncolon: a:b\nhash: a#b\ndash: -x\nq: what?\nsp: a b  c\n",
 "\"quoted key\": 1\n'single key': 2\n? plain\n: 3\n",
 "- &a [1, 2]\n- *a\n- !!str 5\n",
 "k: \"\"\nk2: ''\nk3: \" lead\"\n",
 "---\na: 1\n...\n",
 "--- |\n  literal doc\n",
 "list:\n- name: a\n  vals:\n  - 1\n  - 2\n- name: b\n  vals: []\n",
 "unicode: \"\\u3042\"\njp: こんにちは\nemoji: 😀\n",
 "a:\n  b:\n    c:\n      d: deep\n  e: 1\n",
 "- - - x\n    - y\n  - z\n",
 "{a: 1, b: [x, y], c: {d: e}}\n",
 "a: 'multi word string'\nb: \"with: colon\"\nc: [\"x, y\", 'z]']\n",
 "folded_more: >\n  para one\n  continues\n\n    code block\n    code 2\n\n  para two\n",
 "flow_multiline: [a,\n  b,\n  c]\nfm: {a: 1,\n  b: 2}\n",
 "empty_flow_vals: {a: , b: 2}\n",
 "a: 1\n\n\nb: 2\n",
 "%YAML 1.2\n---\nx: 1\n",
 "anchors:\n  base: &base {x: 1}\n  use: *base\n",
 "- a\n-\n- c\n",
 "a:\n  - b\n  -\n    c: d\n",
 "nested: {a: [1, {b: [2, 3]}]}\n",
 "key with spaces: value with spaces\n",
 "'a''b': \"c\\\"d\"\n",
 "tab_in_value: \"a\\tb\"\n",
 "block_in_seq:\n- |\n  lit\n  text\n- >\n  fold\n  text\n- x\n",
 "trailing_block: |\n  a\n",
 "keep_end: |+\n  a\n\n",
 "strip_empty: |-\n\nx: 1\n",
 "- key: value\n  key2:\n  - a\n  - b\n- k: v\n",
 "a: 'x' # c\nb: \"y\" #c2\n",
 "hello\n",
 "--- >\n  folded\n  text\n",
 "a:\n  # comment\n  b: 1\n  # another\n  c: 2\n",
 "a: |\n\n  text after blank\n",
 "a: >\n\n\n  x\n",
 "s: '  spaced  '\n",
 "k: v\n...\n# trailing\n",
 "? - a\n  - b\n: v\n",
 "[a, b, ]\n",
 "{\"a\":1, \"b\":[2]}\n",
 "{a, b: c}\n",
 "- &x item\n- *x\n",
 "a: -1\nd: 1.\n",
 "k: v  \nk2: v2  \n",
 "a: b\r\nc: d\r\n",
 "\ufeffa: 1\n",
 "- - - \n",
 "seq:\n  - a\n  # comment between\n  - b\n",
 "long: >-\n  one\n   two\n  three\n",
 "lit: |1\n  x\n y\n",
 "x: \"\\u00e9\\t\\\\\"\n",
 "k1: [a,\n  b]\nk2: after\n",
 "nested:\n  - [1, 2]\n  - {a: b}\n  -\n    - deep\n",
 "q: \"line1\\nline2\"\n",
 "'k': v\n\"k2\": v2\n",
 "a: 1 # c\n# c2\n\nb:\n  c: 2\n",
 "empty_seq_items:\n-\n-\n",
 "k: &a !!str 5\nj: *a\n",
 "plain_multi:\n  first\n  second\n\n  third\n",
 "- a\n  b\n- c\n",
 "a: x\n  y\n",
 "? a\n? b\n: c\n",
 "top: {a: 1}\nbottom: [1]\n",
 "a:\n    deep: 1\n    deeper:\n        x: y\nb: 2\n",
 "key: \"quoted: colon\"\n",
 "k: 'multi\n\n  para'\n",
 "block_keep_last: |+\n  a\n",
 "- |-\n  x\n- >+\n  y\n\n- z\n",
]
docs_cases = [
 "a: 1\n---\nb: 2\n---\n- x\n",
 "--- 1\n--- two\n...\n--- [3]\n",
 "",
 "# only comment\n",
 "---\n---\n",
 "a: 1\n---\n...\n---\nb: 2\n",
 "--- # comment\nx\n--- |\n  y\n",
 "%YAML 1.2\n%TAG ! tag:example.com,2000:\n---\na: 1\n",
]
def canon(v):
    if v is None: return '~'
    if v is True: return 'true'
    if v is False: return 'false'
    if isinstance(v, int): return 'i:%d' % v
    if isinstance(v, float):
        if math.isnan(v): return 'f:nan'
        if math.isinf(v): return 'f:inf' if v > 0 else 'f:-inf'
        return 'f:%.6f' % v
    if isinstance(v, str): return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list): return '[' + ','.join(canon(x) for x in v) + ']'
    if isinstance(v, dict): return '{' + ','.join(canon(k) + ':' + canon(x) for k, x in v.items()) + '}'
    if isinstance(v, tuple): return '[' + ','.join(canon(x) for x in v) + ']'
    raise Exception(repr(v))
class L(yaml.SafeLoader): pass
def cstr(s):
    out = '"'
    for ch in s:
        o = ord(ch)
        if ch == '"': out += '\\"'
        elif ch == '\\': out += '\\\\'
        elif ch == '\n': out += '\\n'
        elif ch == '\t': out += '\\t'
        elif o < 32: out += '" (chr %d) "' % o
        else: out += ch
    out += '"'
    return ('(str ' + out + ')') if '(chr ' in out else out
# PyYAML maps complex (list) keys to tuples; custom tags need a constructor
L.add_constructor('!custom', lambda l, n: l.construct_scalar(n))
def pairs_ctor(loader, node):
    loader.flatten_mapping(node)
    return dict((tuple(loader.construct_object(k, deep=True)) if isinstance(k, yaml.SequenceNode) else loader.construct_object(k, deep=True), loader.construct_object(v, deep=True)) for k, v in node.value)
L.add_constructor('tag:yaml.org,2002:map', pairs_ctor)
out = []
out.append('(ns yaml-cases-test (:require [mulay.lib.yaml :as y] [clay.string :as str]))')
out.append(open(sys.argv[1]).read())
out.append('(deftest pyyaml-cases')
for c in cases:
    try:
        exp = canon(yaml.load(c, Loader=L))
        out.append('  (is (= (canon-doc %s) %s))' % (cstr(c), cstr(exp)))
    except yaml.YAMLError:
        out.append('  (is (str/starts-with? (canon-doc %s) "ERR"))' % cstr(c))
for c in docs_cases:
    exp = '|'.join(canon(d) for d in yaml.load_all(c, Loader=L))
    out.append('  (is (= (canon-docs %s) %s))' % (cstr(c), cstr(exp)))
out[-1] += ')'
print('\n'.join(out))
