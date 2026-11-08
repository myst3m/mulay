#!/usr/bin/env python3
"""test/fixtures/dw/protobuf_test/ に DataWeave の protobuf 形式の .dwt を書く (期待値は tools/dw-oracle/dw-oracle fill で埋める)。

  tools/gen-protobuf-dwt.py

reader の入力 (protobuf のバイト列) は Python の protobuf (json_format) で JSON から作り、base64 の文字で渡す。
.dwt の入力と出力は文字だけなので、スクリプトは read(fromBase64(payload), ..) と toBase64(write(..)) で読み書きする。
記述子は test/fixtures/dw/protobuf_test/types.desc (tools/protoc.sh で proto/ から作る)。
"""
import base64, os, sys
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory, json_format

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, 'test/fixtures/dw/protobuf_test')
DESC = 'test/fixtures/dw/protobuf_test/types.desc'

fds = descriptor_pb2.FileDescriptorSet()
fds.ParseFromString(open(os.path.join(ROOT, DESC), 'rb').read())
pool = descriptor_pool.DescriptorPool()
for f in fds.file:
    pool.Add(f)
fac = message_factory.MessageFactory(pool)


def enc(typ, js):
    m = fac.GetPrototype(pool.FindMessageTypeByName(typ))()
    json_format.Parse(js, m, descriptor_pool=pool)
    return m.SerializeToString()


def varint(n):
    out = b''
    while True:
        b = n & 0x7f
        n >>= 7
        if n:
            out += bytes([b | 0x80])
        else:
            return out + bytes([b])


def opts(typ, url=DESC):
    return '{descriptorUrl: "%s", messageType: "%s"}' % (url, typ)


def reader(name, typ, data, out='application/dw', url=DESC, expr='x'):
    b64 = base64.b64encode(data).decode()
    script = ('%%dw 2.0\nimport fromBase64 from dw::core::Binaries\noutput %s\n'
              'var x = read(fromBase64(payload), "application/x-protobuf", %s)\n---\n%s\n') % (out, opts(typ, url), expr)
    return name, script, b64


def writer(name, typ, body, url=DESC, read_back=False):
    w = 'write(%s, "application/x-protobuf", %s)' % (body, opts(typ, url))
    if read_back:
        script = ('%%dw 2.0\noutput application/dw\n---\nread(%s, "application/x-protobuf", %s)\n') % (w, opts(typ, url))
    else:
        script = ('%%dw 2.0\nimport toBase64 from dw::core::Binaries\noutput text/plain\n---\ntoBase64(%s)\n') % w
    return name, script, None


SCALARS = ('{"d": 1.5, "f": 0.25, "i32": -5, "i64": "-9000000000", "u32": 4000000000, "u64": "18000000000000000000",'
           ' "s32": -7, "s64": "-8000000000", "f32": 123, "f64": "12345678901", "sf32": -9, "sf64": "-12345678901",'
           ' "b": true, "s": "h\\u00e9llo", "by": "AQID"}')
OUTER = ('{"inner": {"name": "in", "v": 3}, "items": [{"name": "a", "v": 1}, {"name": "b"}], "nums": [1, 2, 300],'
         ' "unpacked": [4, 5], "strs": ["x", "y"], "counts": {"a": 1, "b": 2}, "by_id": {"7": {"name": "seven"}},'
         ' "color": "BLUE", "colors": ["GREEN", "RED", "BLUE"], "text": "hi", "maybe": 0, "ds": [1.5, -2.0], "bs": [true, false]}')
WKT = ('{"ts": "2024-01-02T03:04:05.123456789Z", "dur": "3.500s", "sv": "x", "iv": 5, "bv": true,'
       ' "st": {"a": 1, "b": [true, null, "s"], "c": {"d": 2.5}}, "val": "v", "lv": [1, "a", false], "em": {},'
       ' "any": {"@type": "type.googleapis.com/t.Inner", "name": "n", "v": 1}, "fm": "a.b,c", "byv": "AQI=",'
       ' "dv": 2.5, "i64v": "123", "u64v": "456", "fv": 1.5, "u32v": 7, "nv": null}')
UNKNOWN = enc('t.Inner', '{"name": "n", "v": 2}') + varint(35 << 3 | 0) + varint(111111) \
    + varint(36 << 3 | 2) + varint(3) + b'abc' + varint(37 << 3 | 5) + b'\x01\x02\x03\x04' \
    + varint(38 << 3 | 1) + b'\x01\x02\x03\x04\x05\x06\x07\x08'

CASES = [
    reader('read-scalars', 't.Scalars', enc('t.Scalars', SCALARS)),
    reader('read-scalars-json', 't.Scalars', enc('t.Scalars', SCALARS), out='application/json'),
    reader('read-scalars-defaults', 't.Scalars', b''),
    reader('read-scalars-zeros-on-wire', 't.Scalars', varint(3 << 3) + varint(0) + varint(14 << 3 | 2) + varint(0) + varint(13 << 3) + varint(0)),
    reader('read-float-precision', 't.Scalars', enc('t.Scalars', '{"f": 0.1, "d": 0.1}')),
    reader('read-float-special', 't.Scalars', enc('t.Scalars', '{"f": "NaN", "d": "-Infinity"}')),
    reader('read-int-extremes', 't.Scalars', enc('t.Scalars', '{"i32": -2147483648, "i64": "-9223372036854775808", "u32": 4294967295, "u64": "18446744073709551615", "s64": "9223372036854775807", "f64": "18446744073709551615", "sf64": "-9223372036854775808"}')),
    reader('read-outer', 't.Outer', enc('t.Outer', OUTER)),
    reader('read-outer-json', 't.Outer', enc('t.Outer', OUTER), out='application/json'),
    reader('read-outer-empty', 't.Outer', b''),
    reader('read-oneof-obj', 't.Outer', enc('t.Outer', '{"obj": {"name": "o"}}')),
    reader('read-oneof-number', 't.Outer', enc('t.Outer', '{"number": 0}')),
    reader('read-enum-unknown', 't.Outer', varint(8 << 3) + varint(7)),
    reader('read-enum-alias', 't.Outer', enc('t.Outer', '{"color": "AZURE"}')),
    reader('read-unpacked-as-packed', 't.Outer', varint(4 << 3 | 2) + varint(2) + b'\x04\x05' + varint(3 << 3) + varint(9)),
    reader('read-repeated-selector', 't.Outer', enc('t.Outer', OUTER), out='application/json', expr='{nums: x.*nums, first: x.nums, items: x.*items.name, counts: x.counts}'),
    reader('read-wkt', 't.Wkt', enc('t.Wkt', WKT)),
    reader('read-wkt-json', 't.Wkt', enc('t.Wkt', WKT), out='application/json'),
    reader('read-wkt-value-kinds', 't.Wkt', enc('t.Wkt', '{"val": {"k": [1, {"z": null}]}}')),
    reader('read-tree', 't.Tree', enc('t.Tree', '{"name": "root", "children": [{"name": "a", "children": [{"name": "a1"}]}, {"name": "b"}]}')),
    reader('read-camel', 't.Camel', enc('t.Camel', '{"first_name": "f", "lastValue": 3}')),
    reader('read-p2-required-only', 't2.P2', enc('t2.P2', '{"name": "only"}')),
    reader('read-p2-full', 't2.P2', enc('t2.P2', '{"name": "n", "n": 0, "xs": [1, 2], "e": "A", "packedXs": [3, 4], "s": ""}')),
    reader('read-p2-missing-required', 't2.P2', varint(2 << 3) + varint(5)),
    reader('read-unknown-fields', 't.Inner', UNKNOWN),
    reader('read-unknown-type', 't.Nope', enc('t.Inner', '{"name": "n"}')),
    reader('read-missing-descriptor', 't.Inner', enc('t.Inner', '{"name": "n"}'), url='test/fixtures/dw/protobuf_test/missing.desc'),
    reader('read-truncated', 't.Inner', enc('t.Inner', '{"name": "abcdef"}')[:4]),
    reader('read-bad-wire-type', 't.Inner', varint(1 << 3 | 0) + varint(5)),
    reader('read-meta', 't.Outer', enc('t.Outer', '{"color": "GREEN", "by_id": {"1": {"v": 1}}}'), out='application/json', expr='{c: x.color, cm: x.color.^, keys: keysOf(x), byid: x.by_id, t: typeOf(x.by_id) as String}'),
    writer('write-scalars', 't.Scalars', '{d: 1.5, f: 0.25, i32: -5, i64: -9000000000, u32: 4000000000, u64: 18000000000000000000, s32: -7, s64: -8000000000, f32: 123, f64: 12345678901, sf32: -9, sf64: -12345678901, b: true, s: "héllo", by: "AQID" as Binary {base: "64"}}'),
    writer('write-scalars-zeros', 't.Scalars', '{d: 0, f: 0, i32: 0, i64: 0, b: false, s: "", by: "" as Binary}'),
    writer('write-key-order', 't.Scalars', '{s: "z", i32: 1, d: 2}'),
    writer('write-float', 't.Scalars', '{f: 0.1, d: 0.1}'),
    writer('write-outer', 't.Outer', '{inner: {name: "in", v: 3}, items: {name: "a", v: 1}, items: {name: "b"}, nums: 1, nums: 2, nums: 300, unpacked: 4, unpacked: 5, strs: "x", strs: "y", counts: {a: 1, b: 2}, by_id: {"7": {name: "seven"}}, color: "BLUE", colors: "GREEN", colors: "RED", text: "hi", maybe: 0, ds: 1.5, bs: true, bs: false}'),
    writer('write-outer-read-back', 't.Outer', '{inner: {name: "in"}, nums: 1, nums: 2, counts: {a: 1}, color: "AZURE", number: 5}', read_back=True),
    writer('write-repeated-array', 't.Outer', '{nums: [1, 2, 3]}'),
    writer('write-repeated-twice-not-repeated', 't.Outer', '{color: "RED", color: "BLUE"}'),
    writer('write-enum-number', 't.Outer', '{color: 2}'),
    writer('write-enum-unknown-name', 't.Outer', '{color: "PURPLE"}'),
    writer('write-enum-with-index', 't.Outer', '{color: "-UNRECOGNIZED" as String {protobufEnumIndex: 9}}'),
    writer('write-oneof-two', 't.Outer', '{text: "a", number: 1}'),
    writer('write-unknown-field', 't.Inner', '{name: "n", nope: 1}'),
    writer('write-type-mismatch', 't.Inner', '{v: "abc"}'),
    writer('write-string-from-number', 't.Inner', '{name: 12}'),
    writer('write-int-overflow', 't.Scalars', '{i32: 3000000000}'),
    writer('write-int-fraction', 't.Scalars', '{i32: 1.5}'),
    writer('write-null-field', 't.Inner', '{name: null, v: 1}'),
    writer('write-map-int-key', 't.Outer', '{by_id: {"12": {v: 1}, "3": {v: 2}}}'),
    writer('write-map-bad-key', 't.Outer', '{by_id: {"x": {v: 1}}}'),
    writer('write-wkt', 't.Wkt', '{ts: |2024-01-02T03:04:05.123456789|, dur: |PT3.5S|, sv: "x", iv: 5, bv: true, st: {a: 1, b: [true, null, "s"]}, val: "v", lv: [1, "a"], em: {}, fm: "a.b,c", byv: "AQI=" as Binary {base: "64"}, dv: 2.5, i64v: 123, u64v: 456, fv: 1.5, u32v: 7, nv: null}'),
    writer('write-wkt-read-back', 't.Wkt', '{ts: |2024-01-02T03:04:05Z|, dur: |PT1M|, st: {a: 1}, val: [1, "a"], em: {}}', read_back=True),
    writer('write-p2-missing-required', 't2.P2', '{n: 1}'),
    writer('write-p2', 't2.P2', '{name: "n", xs: 1, xs: 2, packed_xs: 3, packed_xs: 4, e: "A"}'),
    writer('write-tree', 't.Tree', '{name: "r", children: {name: "a", children: {name: "a1"}}, children: {name: "b"}}'),
    writer('write-camel', 't.Camel', '{first_name: "f", lastValue: 3}'),
    writer('write-unknown-type', 't.Nope', '{name: "n"}'),
    writer('write-array-root', 't.Inner', '[1, 2]'),
]


def main():
    os.makedirs(DIR, exist_ok=True)
    for name, script, b64 in CASES:
        lines = ['%%% script', script.rstrip('\n')]
        if b64 is not None:
            lines += ['%%% input payload text/plain', b64]
        open(os.path.join(DIR, name + '.dwt'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('wrote', len(CASES), 'case(s) to', DIR)


if __name__ == '__main__':
    main()
