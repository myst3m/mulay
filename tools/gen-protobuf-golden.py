#!/usr/bin/env python3
"""test/protobuf/golden_data.clay を書く: Python の protobuf で JSON から作ったバイト列 (base64)。

  tools/gen-protobuf-golden.py

mulay の lib/protobuf で読んで書き直すと、同じバイト列に戻ることを確かめる (protobuf-java と Python は同じ規則で書く:
フィールド番号の順、proto3 の既定値は書かない、proto3 の数の repeated は packed)。
"""
import base64, os
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory, json_format

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fds = descriptor_pb2.FileDescriptorSet()
fds.ParseFromString(open(os.path.join(ROOT, 'test/fixtures/dw/protobuf_test/types.desc'), 'rb').read())
pool = descriptor_pool.DescriptorPool()
for f in fds.file:
    pool.Add(f)
fac = message_factory.MessageFactory(pool)

CASES = [
    ('t.Scalars', '{"d": 1.5, "f": 0.25, "i32": -5, "i64": "-9000000000", "u32": 4000000000, "u64": "18000000000000000000", "s32": -7, "s64": "-8000000000", "f32": 123, "f64": "12345678901", "sf32": -9, "sf64": "-12345678901", "b": true, "s": "h\\u00e9llo", "by": "AQID"}'),
    ('t.Scalars', '{"i32": -2147483648, "i64": "-9223372036854775808", "u32": 4294967295, "u64": "18446744073709551615", "s32": -2147483648, "s64": "9223372036854775807", "f64": "18446744073709551615", "sf64": "-9223372036854775808", "f": 3.4028234663852886e38, "d": 5e-324}'),
    ('t.Scalars', '{"f": "NaN", "d": "-Infinity"}'),
    ('t.Scalars', '{}'),
    ('t.Outer', '{"inner": {"name": "in", "v": 3}, "items": [{"name": "a", "v": 1}, {"name": "b"}], "nums": [1, 2, 300, -1], "unpacked": [4, 5], "strs": ["x", "y"], "counts": {"a": 1, "b": 2}, "by_id": {"7": {"name": "seven"}}, "color": "BLUE", "colors": ["GREEN", "RED", "BLUE"], "text": "hi", "maybe": 0, "ds": [1.5, -2.0], "bs": [true, false]}'),
    ('t.Outer', '{"obj": {"name": "o"}, "color": 7}'),
    ('t.Tree', '{"name": "root", "children": [{"name": "a", "children": [{"name": "a1"}]}, {"name": "b"}]}'),
    ('t.Wkt', '{"ts": "2024-01-02T03:04:05.123456789Z", "dur": "3.500s", "sv": "x", "st": {"a": 1, "b": [true, null]}, "any": {"@type": "type.googleapis.com/t.Inner", "name": "n", "v": 1}, "fm": "a.b,c"}'),
    ('t2.P2', '{"name": "n", "n": 0, "xs": [1, 2], "e": "A", "packedXs": [3, 4], "s": ""}'),
]


def main():
    lines = ['(ns protobuf-golden-data)', '', '(def CASES: Vec(Vec(Str)) [']
    for typ, js in CASES:
        m = fac.GetPrototype(pool.FindMessageTypeByName(typ))()
        json_format.Parse(js, m, descriptor_pool=pool)
        lines.append('  ["%s" "%s"]' % (typ, base64.b64encode(m.SerializeToString()).decode()))
    lines.append('])')
    open(os.path.join(ROOT, 'test/protobuf/golden_data.clay'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('wrote', len(CASES), 'case(s)')


if __name__ == '__main__':
    main()
