# 壊れた記述子 (protoc では作れない) を作る: python3 -I mk.py <出力先>
# 型の参照が解けないもの (import を含めずに作った記述子)、メッセージの所に列挙型、列挙型の所にメッセージ、
# value の無い map の項目、fields の無い google.protobuf.Struct。
import os
import sys

from google.protobuf import descriptor_pb2 as d

out = sys.argv[1]


def base(s):
    f = s.file.add()
    f.name = "a.proto"
    f.package = "t"
    f.syntax = "proto3"
    return f


def field(m, name, num, label, typ, type_name=""):
    fl = m.field.add()
    fl.name = name
    fl.number = num
    fl.label = label
    fl.type = typ
    if type_name:
        fl.type_name = type_name
    return fl


def unresolved():
    s = d.FileDescriptorSet()
    f = base(s)
    f.dependency.append("b.proto")
    m = f.message_type.add()
    m.name = "A"
    field(m, "b", 1, 1, 11, ".t.B")
    field(m, "n", 2, 1, 9)
    return s


def wrong_kind(kind):
    s = d.FileDescriptorSet()
    f = base(s)
    e = f.enum_type.add()
    e.name = "E"
    v = e.value.add()
    v.name = "Z"
    v.number = 0
    m = f.message_type.add()
    m.name = "A"
    if kind == "enum-missing":
        field(m, "b", 1, 1, 14, ".t.Q")
    elif kind == "msg-is-enum":
        field(m, "b", 1, 1, 11, ".t.E")
    else:
        field(m, "b", 1, 1, 14, ".t.A")
    return s


def map_novalue():
    s = d.FileDescriptorSet()
    f = base(s)
    m = f.message_type.add()
    m.name = "A"
    e = m.nested_type.add()
    e.name = "MEntry"
    e.options.map_entry = True
    field(e, "key", 1, 1, 9)
    field(m, "m", 1, 3, 11, ".t.A.MEntry")
    return s


def struct_nofields():
    s = d.FileDescriptorSet()
    g = s.file.add()
    g.name = "google/protobuf/struct.proto"
    g.package = "google.protobuf"
    g.syntax = "proto3"
    st = g.message_type.add()
    st.name = "Struct"
    field(st, "x", 1, 1, 9)
    lv = g.message_type.add()
    lv.name = "ListValue"
    field(lv, "x", 1, 1, 9)
    f = base(s)
    f.dependency.append("google/protobuf/struct.proto")
    m = f.message_type.add()
    m.name = "A"
    field(m, "m", 1, 1, 11, ".google.protobuf.Struct")
    field(m, "l", 2, 1, 11, ".google.protobuf.ListValue")
    return s


sets = {
    "unresolved": unresolved(),
    "enum-missing": wrong_kind("enum-missing"),
    "msg-is-enum": wrong_kind("msg-is-enum"),
    "enum-is-msg": wrong_kind("enum-is-msg"),
    "map-novalue": map_novalue(),
    "struct-nofields": struct_nofields(),
}
for name, s in sets.items():
    with open(os.path.join(out, name + ".desc"), "wb") as fh:
        fh.write(s.SerializeToString())
