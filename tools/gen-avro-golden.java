// Generates test/avro/avro_golden_data.clay: Apache Avro Java 1.11.5 の GenericDatumWriter / GenericDatumReader / Schema.Parser の結果。
//   CASES   名前、スキーマ、入力の値 (Clay の式)、符号化したバイト列 (16 進)、読み戻した値の dump。
//   ECASES  符号化の失敗 (入力の値と例外の getMessage())。
//   DCASES  復号だけ (バイト列を直接与える)。err が空でなければ失敗、そうでなければ dump。
//   PCASES  スキーマの解析 (失敗なら getMessage()、成功なら Schema.toString())。
// 値の dump の書式: null / true / false / 5i (int) / 5L (long) / f<8 桁の 16 進> / d<16 桁の 16 進> / "text" (印字できる ASCII) か x:<hex> (string) / b:<hex> (bytes) / F:<hex> (fixed) / E:<symbol> / [a,b] / {k=v,k=v} (map) / {a,b} (record、スキーマの順)
// EOFException は "Unexpected end of Avro data" にそろえる (mulay の文言)。
// Run (Java 17):
//   /usr/lib/jvm/java-17-openjdk-amd64/bin/java -cp $HOME/.m2/repository/org/apache/avro/avro/1.11.5/avro-1.11.5.jar:$HOME/.m2/repository/com/fasterxml/jackson/core/jackson-core/2.18.6/jackson-core-2.18.6.jar:$HOME/.m2/repository/com/fasterxml/jackson/core/jackson-databind/2.18.6/jackson-databind-2.18.6.jar:$HOME/.m2/repository/com/fasterxml/jackson/core/jackson-annotations/2.18.6/jackson-annotations-2.18.6.jar:$HOME/.m2/repository/org/slf4j/slf4j-api/2.0.17/slf4j-api-2.0.17.jar \
//     tools/gen-avro-golden.java > test/avro/avro_golden_data.clay
import org.apache.avro.*;
import org.apache.avro.generic.*;
import org.apache.avro.io.*;
import org.apache.avro.util.Utf8;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.*;

public class GenAvroGolden {
    static class V {
        final String clay; final Object j;
        V(String clay, Object j) { this.clay = clay; this.j = j; }
    }

    static Map<String, Schema> reg = new HashMap<>();

    static void collect(Schema s, Map<String, Schema> m) {
        switch (s.getType()) {
            case RECORD:
                if (m.containsKey(s.getFullName())) return;
                m.put(s.getFullName(), s);
                for (Schema.Field f : s.getFields()) collect(f.schema(), m);
                break;
            case ENUM: case FIXED: m.put(s.getFullName(), s); break;
            case ARRAY: collect(s.getElementType(), m); break;
            case MAP: collect(s.getValueType(), m); break;
            case UNION: for (Schema t : s.getTypes()) collect(t, m); break;
            default:
        }
    }

    static String q(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '"') b.append("\\\""); else if (c == '\\') b.append("\\\\");
            else if (c == '\n') b.append("\\n"); else if (c == '\t') b.append("\\t"); else if (c == '\r') b.append("\\r");
            else b.append(c);
        }
        return b.append('"').toString();
    }

    static String hex(byte[] bs) {
        StringBuilder b = new StringBuilder();
        for (byte x : bs) b.append(String.format("%02x", x & 0xff));
        return b.toString();
    }

    static boolean plain(byte[] bs) {
        for (byte x : bs) { int c = x & 0xff; if (c < 0x20 || c > 0x7e || c == '"' || c == '\\') return false; }
        return true;
    }

    static String clayStr(String s) {
        byte[] bs = s.getBytes(StandardCharsets.UTF_8);
        return plain(bs) ? "\"" + s + "\"" : "(bx \"" + hex(bs) + "\")";
    }

    static String longLit(long n) { return n == Long.MIN_VALUE ? "(- -9223372036854775807 1)" : Long.toString(n); }

    static V nul() { return new V("(a/->ANull)", null); }
    static V bool(boolean b) { return new V("(a/->ABool " + b + ")", b); }
    static V i(int n) { return new V("(a/->AInt " + n + ")", n); }
    static V l(long n) { return new V("(a/->ALong " + longLit(n) + ")", n); }
    static V f(float x) { return new V("(a/->AFloat (bits->float " + longLit(Double.doubleToRawLongBits((double) x)) + "))", x); }
    static V d(double x) { return new V("(a/->ADouble (bits->float " + longLit(Double.doubleToRawLongBits(x)) + "))", x); }
    static V dbits(long bits) { return d(Double.longBitsToDouble(bits)); }
    static V s(String x) { return new V("(a/->AStr " + clayStr(x) + ")", x); }
    static V by(int... xs) {
        byte[] bs = new byte[xs.length]; for (int k = 0; k < xs.length; k++) bs[k] = (byte) xs[k];
        return new V("(a/->ABytes (bx \"" + hex(bs) + "\"))", ByteBuffer.wrap(bs));
    }
    static V en(String full, String sym) {
        return new V("(a/->AEnum " + q(full) + " " + q(sym) + ")", new GenericData.EnumSymbol(reg.get(full), sym));
    }
    static V fx(String full, int... xs) {
        byte[] bs = new byte[xs.length]; for (int k = 0; k < xs.length; k++) bs[k] = (byte) xs[k];
        return new V("(a/->AFixed " + q(full) + " (bx \"" + hex(bs) + "\"))", new GenericData.Fixed(reg.get(full), bs));
    }
    static V arr(V... vs) {
        List<Object> js = new ArrayList<>(); StringBuilder c = new StringBuilder("(a/->AArr [");
        for (int k = 0; k < vs.length; k++) { js.add(vs[k].j); c.append(k == 0 ? "" : " ").append(vs[k].clay); }
        return new V(c.append("])").toString(), js);
    }
    static V map(Object... kv) {
        Map<String, Object> m = new LinkedHashMap<>(); StringBuilder ks = new StringBuilder(), vs = new StringBuilder();
        for (int k = 0; k < kv.length; k += 2) {
            V v = (V) kv[k + 1];
            m.put((String) kv[k], v.j);
            ks.append(k == 0 ? "" : " ").append(clayStr((String) kv[k])); vs.append(k == 0 ? "" : " ").append(v.clay);
        }
        return new V("(a/->AMap [" + ks + "] [" + vs + "])", m);
    }
    static V rec(String full, Object... kv) {
        GenericData.Record r = new GenericData.Record(reg.get(full));
        StringBuilder ks = new StringBuilder(), vs = new StringBuilder();
        for (int k = 0; k < kv.length; k += 2) {
            V v = (V) kv[k + 1];
            r.put((String) kv[k], v.j);
            ks.append(k == 0 ? "" : " ").append(q((String) kv[k])); vs.append(k == 0 ? "" : " ").append(v.clay);
        }
        return new V("(a/->ARec " + q(full) + " [" + ks + "] [" + vs + "])", r);
    }
    static V raw(String clay, Object j) { return new V(clay, j); }

    static String dumpStr(byte[] bs) { return plain(bs) ? "\"" + new String(bs, StandardCharsets.ISO_8859_1) + "\"" : "x:" + hex(bs); }

    static String dump(Schema s, Object o) {
        switch (s.getType()) {
            case NULL: return "null";
            case BOOLEAN: return o.toString();
            case INT: return o + "i";
            case LONG: return o + "L";
            case FLOAT: return String.format("f%08x", Float.floatToRawIntBits((Float) o));
            case DOUBLE: return String.format("d%016x", Double.doubleToRawLongBits((Double) o));
            case STRING: return dumpStr(o instanceof Utf8 ? Arrays.copyOf(((Utf8) o).getBytes(), ((Utf8) o).getByteLength()) : o.toString().getBytes(StandardCharsets.UTF_8));
            case BYTES: { ByteBuffer b = ((ByteBuffer) o).duplicate(); byte[] bs = new byte[b.remaining()]; b.get(bs); return "b:" + hex(bs); }
            case FIXED: return "F:" + hex(((GenericFixed) o).bytes());
            case ENUM: return "E:" + o;
            case UNION: { int ix = GenericData.get().resolveUnion(s, o); return dump(s.getTypes().get(ix), o); }
            case ARRAY: {
                StringBuilder b = new StringBuilder("[");
                boolean first = true;
                for (Object e : (Collection<?>) o) { b.append(first ? "" : ",").append(dump(s.getElementType(), e)); first = false; }
                return b.append("]").toString();
            }
            case MAP: {
                StringBuilder b = new StringBuilder("{");
                boolean first = true;
                for (Map.Entry<?, ?> e : ((Map<?, ?>) o).entrySet()) {
                    b.append(first ? "" : ",").append(dump(Schema.create(Schema.Type.STRING), e.getKey())).append("=").append(dump(s.getValueType(), e.getValue()));
                    first = false;
                }
                return b.append("}").toString();
            }
            default: {
                GenericRecord r = (GenericRecord) o;
                StringBuilder b = new StringBuilder("{");
                boolean first = true;
                for (Schema.Field fl : s.getFields()) { b.append(first ? "" : ",").append(dump(fl.schema(), r.get(fl.pos()))); first = false; }
                return b.append("}").toString();
            }
        }
    }

    static byte[] unhex(String h) {
        byte[] bs = new byte[h.length() / 2];
        for (int k = 0; k < bs.length; k++) bs[k] = (byte) Integer.parseInt(h.substring(2 * k, 2 * k + 2), 16);
        return bs;
    }

    static Object read(Schema s, byte[] bs) throws IOException {
        GenericDatumReader<Object> r = new GenericDatumReader<Object>(s) {
            @Override protected Object newMap(Object old, int size) { return new LinkedHashMap<Object, Object>(size); }
        };
        return r.read(null, DecoderFactory.get().binaryDecoder(bs, null));
    }

    static byte[] write(Schema s, Object v) throws IOException {
        ByteArrayOutputStream o = new ByteArrayOutputStream();
        BinaryEncoder e = EncoderFactory.get().binaryEncoder(o, null);
        new GenericDatumWriter<Object>(s).write(v, e);
        e.flush();
        return o.toByteArray();
    }

    static StringBuilder cases = new StringBuilder(), ecases = new StringBuilder(), dcases = new StringBuilder(), pcases = new StringBuilder();

    static Schema begin(String sj) {
        Schema s = new Schema.Parser().parse(sj);
        reg = new HashMap<>();
        collect(s, reg);
        return s;
    }

    static void ok(String name, String sj, V v) throws IOException {
        Schema s = begin(sj);
        byte[] bs = write(s, v.j);
        String back = dump(s, read(s, bs));
        cases.append("  (->GCase ").append(q(name)).append(" ").append(q(sj)).append(" ").append(v.clay).append(" ").append(q(hex(bs))).append(" ").append(q(back)).append(")\n");
    }

    static void ok(String name, String sj, java.util.function.Supplier<V> mk) throws IOException {
        Schema s = begin(sj);
        ok(name, sj, mk.get());
    }

    static void err(String name, String sj, java.util.function.Supplier<V> mk) {
        Schema s = begin(sj);
        V v = mk.get();
        String msg;
        try { byte[] bs = write(s, v.j); msg = "!!UNEXPECTED SUCCESS " + hex(bs); }
        catch (Throwable e) { msg = e.getMessage(); }
        ecases.append("  (->ECase ").append(q(name)).append(" ").append(q(sj)).append(" ").append(v.clay).append(" ").append(q(msg)).append(")\n");
    }

    static void dec(String name, String sj, String h) {
        Schema s = begin(sj);
        String res, err = "";
        try { res = dump(s, read(s, unhex(h))); }
        catch (EOFException e) { res = ""; err = "Unexpected end of Avro data"; }
        catch (Throwable e) { res = ""; err = e.getMessage(); }
        dcases.append("  [").append(q(name)).append(" ").append(q(sj)).append(" ").append(q(h)).append(" ").append(q(err)).append(" ").append(q(res)).append("]\n");
    }

    static void parse(String sj) {
        String err = "", json = "";
        try { json = new Schema.Parser().parse(sj).toString(); } catch (Throwable e) { err = e.getMessage(); }
        pcases.append("  [").append(q(sj)).append(" ").append(q(err)).append(" ").append(q(json)).append("]\n");
    }

    static String p(String t) { return "\"" + t + "\""; }
    static String sch(String t) { return t; }

    static final String R_ABC = "{\"type\":\"record\",\"name\":\"R\",\"namespace\":\"n\",\"fields\":[{\"name\":\"a\",\"type\":\"string\"},{\"name\":\"b\",\"type\":[\"null\",\"int\"]},{\"name\":\"c\",\"type\":{\"type\":\"array\",\"items\":\"string\"}},{\"name\":\"d\",\"type\":{\"type\":\"map\",\"values\":\"long\"}}]}";
    static final String OUTER = "{\"type\":\"record\",\"name\":\"Outer\",\"namespace\":\"x.y\",\"fields\":[{\"name\":\"inner\",\"type\":{\"type\":\"record\",\"name\":\"Inner\",\"fields\":[{\"name\":\"s\",\"type\":\"string\"},{\"name\":\"e\",\"type\":{\"type\":\"enum\",\"name\":\"E\",\"symbols\":[\"A\",\"B\"]}},{\"name\":\"u\",\"type\":[\"null\",\"int\"]},{\"name\":\"xs\",\"type\":{\"type\":\"array\",\"items\":[\"null\",\"int\"]}},{\"name\":\"f\",\"type\":{\"type\":\"fixed\",\"name\":\"F\",\"size\":2}},{\"name\":\"fl\",\"type\":\"float\"}]}},{\"name\":\"list\",\"type\":{\"type\":\"array\",\"items\":\"Inner\"}},{\"name\":\"m\",\"type\":{\"type\":\"map\",\"values\":[\"null\",\"Inner\"]}},{\"name\":\"ou\",\"type\":[\"null\",\"Inner\"]}]}";
    static final String CDC = "{\"type\":\"record\",\"name\":\"AccountChangeEvent\",\"namespace\":\"com.sforce.eventbus\",\"fields\":[{\"name\":\"ChangeEventHeader\",\"type\":{\"type\":\"record\",\"name\":\"ChangeEventHeader\",\"fields\":[{\"name\":\"entityName\",\"type\":\"string\"},{\"name\":\"recordIds\",\"type\":{\"type\":\"array\",\"items\":\"string\"}},{\"name\":\"changeType\",\"type\":{\"type\":\"enum\",\"name\":\"ChangeType\",\"symbols\":[\"CREATE\",\"UPDATE\",\"DELETE\",\"UNDELETE\",\"GAP_CREATE\",\"GAP_UPDATE\",\"GAP_DELETE\",\"GAP_UNDELETE\",\"GAP_OVERFLOW\"]}},{\"name\":\"changedFields\",\"type\":{\"type\":\"array\",\"items\":\"string\"}},{\"name\":\"nulledFields\",\"type\":{\"type\":\"array\",\"items\":\"string\"}},{\"name\":\"diffFields\",\"type\":{\"type\":\"array\",\"items\":\"string\"}},{\"name\":\"transactionKey\",\"type\":\"string\"},{\"name\":\"sequenceNumber\",\"type\":\"int\"},{\"name\":\"commitTimestamp\",\"type\":\"long\"},{\"name\":\"commitNumber\",\"type\":\"long\"},{\"name\":\"commitUser\",\"type\":\"string\"}]}},{\"name\":\"Id\",\"type\":[\"null\",\"string\"],\"default\":null},{\"name\":\"Name\",\"type\":[\"null\",\"string\"],\"default\":null},{\"name\":\"NumberOfEmployees\",\"type\":[\"null\",\"int\"],\"default\":null},{\"name\":\"AnnualRevenue\",\"type\":[\"null\",\"double\"],\"default\":null},{\"name\":\"BillingAddress\",\"type\":[\"null\",{\"type\":\"record\",\"name\":\"Address\",\"fields\":[{\"name\":\"City\",\"type\":[\"null\",\"string\"],\"default\":null},{\"name\":\"Country\",\"type\":[\"null\",\"string\"],\"default\":null}]}],\"default\":null},{\"name\":\"LastModifiedDate\",\"type\":[\"null\",{\"type\":\"long\",\"logicalType\":\"timestamp-millis\"}],\"default\":null}]}";
    static final String EVT = "{\"type\":\"record\",\"name\":\"Order_Event__e\",\"namespace\":\"com.sforce.eventbus\",\"doc\":\"Platform event\",\"fields\":[{\"name\":\"CreatedDate\",\"type\":\"long\"},{\"name\":\"CreatedById\",\"type\":\"string\"},{\"name\":\"Order_Number__c\",\"type\":[\"null\",\"string\"],\"default\":null,\"doc\":\"order\"},{\"name\":\"Amount__c\",\"type\":[\"null\",\"double\"],\"default\":null}]}";
    static final String LIST = "{\"type\":\"record\",\"name\":\"Node\",\"fields\":[{\"name\":\"v\",\"type\":\"int\"},{\"name\":\"next\",\"type\":[\"null\",\"Node\"]}]}";
    static final String ENUM_E = "{\"type\":\"enum\",\"name\":\"E\",\"namespace\":\"n\",\"symbols\":[\"A\",\"B\",\"C\"]}";
    static final String FIXED_F = "{\"type\":\"fixed\",\"name\":\"F\",\"size\":4}";
    static final String UNION_ALL = "[\"null\",\"boolean\",\"int\",\"long\",\"float\",\"double\",\"string\",\"bytes\"]";
    static final String UNION_NAMED = "[\"null\",{\"type\":\"array\",\"items\":\"int\"},{\"type\":\"map\",\"values\":\"int\"},{\"type\":\"enum\",\"name\":\"E\",\"symbols\":[\"A\",\"B\"]},{\"type\":\"fixed\",\"name\":\"F\",\"size\":2},{\"type\":\"record\",\"name\":\"P\",\"fields\":[{\"name\":\"x\",\"type\":\"int\"}]},{\"type\":\"record\",\"name\":\"Q\",\"namespace\":\"z\",\"fields\":[{\"name\":\"x\",\"type\":\"int\"}]}]";

    public static void main(String[] args) throws Exception {
        ok("null", p("null"), nul());
        ok("bool-true", p("boolean"), bool(true));
        ok("bool-false", p("boolean"), bool(false));
        int[] ints = {0, 1, -1, 2, -2, 63, 64, -64, -65, 8191, 8192, 65535, 1048576, 2147483647, -2147483648, -2147483647};
        for (int n : ints) ok("int-" + n, p("int"), i(n));
        long[] longs = {0, 1, -1, 63, 64, -64, -65, 2147483647L, 2147483648L, -2147483648L, -2147483649L, 4294967296L, 1L << 40, 1L << 62, Long.MAX_VALUE, Long.MIN_VALUE, Long.MIN_VALUE + 1, 1700000000000L};
        for (long n : longs) ok("long-" + n, p("long"), l(n));
        float[] floats = {0f, -0f, 1f, -1f, 1.5f, 0.1f, 3.4028235E38f, Float.MIN_VALUE, Float.MIN_NORMAL, Float.NaN, Float.POSITIVE_INFINITY, Float.NEGATIVE_INFINITY, 123456.789f};
        for (float x : floats) ok("float-" + Float.floatToRawIntBits(x), p("float"), f(x));
        double[] doubles = {0.0, -0.0, 1.0, -1.0, 1.5, 0.1, Double.MAX_VALUE, Double.MIN_VALUE, Double.MIN_NORMAL, Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY, 3.141592653589793, 1e300};
        for (double x : doubles) ok("double-" + Long.toHexString(Double.doubleToRawLongBits(x)), p("double"), d(x));
        ok("double-nan-payload", p("double"), dbits(0x7ff8000000000123L));
        ok("double-neg-nan", p("double"), dbits(0xfff8000000000000L));
        String[] strs = {"", "a", "hello", "\u3042\u3044\u3046", "caf\u00e9", "\ud83d\ude00 emoji", "a\"b\\c\nd\te", "\u0000", "tab\there"};
        for (int k = 0; k < strs.length; k++) ok("string-" + k, p("string"), s(strs[k]));
        ok("string-300", p("string"), s("x".repeat(300)));
        ok("string-70000", p("string"), s("0123456789".repeat(7000)));
        ok("bytes-empty", p("bytes"), by());
        ok("bytes-4", p("bytes"), by(0, 1, 2, 255));
        int[] big = new int[200]; for (int k = 0; k < 200; k++) big[k] = k;
        ok("bytes-200", p("bytes"), by(big));
        ok("enum-A", ENUM_E, () -> en("n.E", "A"));
        ok("enum-C", ENUM_E, () -> en("n.E", "C"));
        ok("fixed", FIXED_F, () -> fx("F", 1, 2, 3, 255));
        ok("fixed-0", "{\"type\":\"fixed\",\"name\":\"Z\",\"size\":0}", () -> fx("Z"));
        String AI = "{\"type\":\"array\",\"items\":\"int\"}";
        ok("array-empty", AI, arr());
        ok("array-ints", AI, arr(i(1), i(2), i(3), i(-4)));
        Object[] many = new V[100]; V[] manyv = new V[100]; for (int k = 0; k < 100; k++) manyv[k] = i(k * 1000);
        ok("array-100", AI, arr(manyv));
        ok("array-strings", "{\"type\":\"array\",\"items\":\"string\"}", arr(s("a"), s(""), s("\u3042")));
        ok("array-nested", "{\"type\":\"array\",\"items\":{\"type\":\"array\",\"items\":\"long\"}}", arr(arr(l(1), l(2)), arr(), arr(l(Long.MIN_VALUE))));
        String MI = "{\"type\":\"map\",\"values\":\"long\"}";
        ok("map-empty", MI, map());
        ok("map-two", MI, map("a", l(1), "b", l(-2)));
        ok("map-order", MI, map("zeta", l(1), "alpha", l(2), "mid", l(3), "\u3042", l(4)));
        ok("map-arrays", "{\"type\":\"map\",\"values\":{\"type\":\"array\",\"items\":\"int\"}}", map("k", arr(i(1)), "e", arr()));
        ok("map-union", "{\"type\":\"map\",\"values\":[\"null\",\"string\"]}", map("a", nul(), "b", s("x")));
        ok("union-nl-null", "[\"null\",\"string\"]", nul());
        ok("union-nl-str", "[\"null\",\"string\"]", s("x"));
        ok("union-ln-null", "[\"string\",\"null\"]", nul());
        ok("union-ln-str", "[\"string\",\"null\"]", s("x"));
        ok("union-all-null", UNION_ALL, nul());
        ok("union-all-bool", UNION_ALL, bool(true));
        ok("union-all-int", UNION_ALL, i(5));
        ok("union-all-long", UNION_ALL, l(5));
        ok("union-all-float", UNION_ALL, f(1.5f));
        ok("union-all-double", UNION_ALL, d(2.5));
        ok("union-all-string", UNION_ALL, s("s"));
        ok("union-all-bytes", UNION_ALL, by(9, 8));
        ok("union-named-null", UNION_NAMED, nul());
        ok("union-named-array", UNION_NAMED, arr(i(1), i(2)));
        ok("union-named-map", UNION_NAMED, map("k", i(1)));
        ok("union-named-enum", UNION_NAMED, () -> en("E", "B"));
        ok("union-named-fixed", UNION_NAMED, () -> fx("F", 7, 8));
        ok("union-named-rec-p", UNION_NAMED, () -> rec("P", "x", i(1)));
        ok("union-named-rec-q", UNION_NAMED, () -> rec("z.Q", "x", i(2)));
        ok("record-abc", R_ABC, () -> rec("n.R", "a", s("x"), "b", nul(), "c", arr(s("p"), s("q")), "d", map("k", l(7))));
        ok("record-abc-b", R_ABC, () -> rec("n.R", "a", s(""), "b", i(-9), "c", arr(), "d", map()));
        ok("list-3", LIST, () -> rec("Node", "v", i(1), "next", rec("Node", "v", i(2), "next", rec("Node", "v", i(3), "next", nul()))));
        ok("list-1", LIST, () -> rec("Node", "v", i(1), "next", nul()));
        ok("outer-full", OUTER, () -> rec("x.y.Outer",
            "inner", rec("x.y.Inner", "s", s("x"), "e", en("x.y.E", "A"), "u", i(3), "xs", arr(i(1), nul(), i(2)), "f", fx("x.y.F", 1, 2), "fl", f(1.5f)),
            "list", arr(rec("x.y.Inner", "s", s("l"), "e", en("x.y.E", "B"), "u", nul(), "xs", arr(), "f", fx("x.y.F", 3, 4), "fl", f(-2f))),
            "m", map("k", rec("x.y.Inner", "s", s("m"), "e", en("x.y.E", "A"), "u", nul(), "xs", arr(), "f", fx("x.y.F", 5, 6), "fl", f(0f)), "n", nul()),
            "ou", nul()));
        ok("cdc", CDC, () -> rec("com.sforce.eventbus.AccountChangeEvent",
            "ChangeEventHeader", rec("com.sforce.eventbus.ChangeEventHeader",
                "entityName", s("Account"), "recordIds", arr(s("001xx000003DGb2AAG"), s("001xx000003DGb3AAG")),
                "changeType", en("com.sforce.eventbus.ChangeType", "UPDATE"),
                "changedFields", arr(s("0x00000002"), s("Name")), "nulledFields", arr(), "diffFields", arr(),
                "transactionKey", s("000d3a8f-6f14-1cc4-d23b-bf7ac4e2e1c1"), "sequenceNumber", i(1),
                "commitTimestamp", l(1700000000123L), "commitNumber", l(1234567890123456L), "commitUser", s("005xx000001X8UzAAK")),
            "Id", s("001xx000003DGb2AAG"), "Name", s("\u30c6\u30b9\u30c8 Inc."), "NumberOfEmployees", i(250), "AnnualRevenue", d(1.25e6),
            "BillingAddress", rec("com.sforce.eventbus.Address", "City", s("Tokyo"), "Country", nul()),
            "LastModifiedDate", l(1700000000123L)));
        ok("cdc-gap", CDC, () -> rec("com.sforce.eventbus.AccountChangeEvent",
            "ChangeEventHeader", rec("com.sforce.eventbus.ChangeEventHeader",
                "entityName", s("Account"), "recordIds", arr(s("001xx000003DGb2AAG")),
                "changeType", en("com.sforce.eventbus.ChangeType", "GAP_OVERFLOW"),
                "changedFields", arr(), "nulledFields", arr(), "diffFields", arr(),
                "transactionKey", s(""), "sequenceNumber", i(0),
                "commitTimestamp", l(0), "commitNumber", l(0), "commitUser", s("")),
            "Id", nul(), "Name", nul(), "NumberOfEmployees", nul(), "AnnualRevenue", nul(), "BillingAddress", nul(), "LastModifiedDate", nul()));
        ok("event", EVT, () -> rec("com.sforce.eventbus.Order_Event__e", "CreatedDate", l(1700000000000L), "CreatedById", s("005xx000001X8UzAAK"), "Order_Number__c", s("ORD-1"), "Amount__c", d(99.5)));
        ok("event-nulls", EVT, () -> rec("com.sforce.eventbus.Order_Event__e", "CreatedDate", l(1), "CreatedById", s("u"), "Order_Number__c", nul(), "Amount__c", nul()));
        ok("coerce-long-in-int", p("int"), () -> raw("(a/->ALong 4294967297)", 4294967297L));
        ok("coerce-int-in-long", p("long"), () -> raw("(a/->AInt 5)", 5));
        ok("coerce-double-in-int", p("int"), () -> raw("(a/->ADouble 1e20)", 1e20));
        ok("coerce-nan-in-int", p("int"), () -> raw("(a/->ADouble (bits->float 9221120237041090560))", Double.NaN));
        ok("coerce-double-in-long", p("long"), () -> raw("(a/->ADouble -1e30)", -1e30));
        ok("coerce-float-in-long", p("long"), () -> raw("(a/->AFloat 2.5)", 2.5f));
        ok("coerce-double-in-float", p("float"), () -> raw("(a/->ADouble 0.1)", 0.1));
        ok("coerce-long-in-float", p("float"), () -> raw("(a/->ALong 16777217)", 16777217L));
        ok("coerce-int-in-double", p("double"), () -> raw("(a/->AInt 7)", 7));
        ok("coerce-float-in-double", p("double"), () -> raw("(a/->AFloat 0.5)", 0.5f));
        ok("null-schema-any", p("null"), () -> raw("(a/->AInt 1)", 1));
        ok("fixed-longer", FIXED_F, () -> raw("(a/->AFixed \"F\" (bx \"0102030405\"))", new GenericData.Fixed(reg.get("F"), new byte[]{1, 2, 3, 4, 5})));
        ok("enum-name-ignored", ENUM_E, () -> raw("(a/->AEnum \"other\" \"B\")", new GenericData.EnumSymbol(reg.get("n.E"), "B")));
        ok("record-by-name", R_ABC, () -> raw("(a/->ARec \"n.R\" [\"d\" \"c\" \"b\" \"a\"] [(a/->AMap [] []) (a/->AArr []) (a/->ANull) (a/->AStr \"z\")])",
            rec("n.R", "a", s("z"), "b", nul(), "c", arr(), "d", map()).j));
        ok("record-missing-nullable", "{\"type\":\"record\",\"name\":\"M\",\"fields\":[{\"name\":\"a\",\"type\":[\"null\",\"int\"]},{\"name\":\"b\",\"type\":\"int\"}]}",
            () -> raw("(a/->ARec \"M\" [\"b\"] [(a/->AInt 4)])", rec("M", "b", i(4)).j));

        err("union-int-in-nl-string", "[\"null\",\"string\"]", () -> i(5));
        err("union-int-in-nl-long", "[\"null\",\"long\"]", () -> i(5));
        err("union-float-in-double", "[\"null\",\"double\"]", () -> f(5f));
        err("union-double-in-float", "[\"null\",\"float\"]", () -> d(5.5));
        err("union-null-missing", "[\"int\",\"string\"]", () -> nul());
        err("union-rec-unknown", UNION_NAMED, () -> { GenericData.Record r2 = new GenericData.Record(new Schema.Parser().parse("{\"type\":\"record\",\"name\":\"R2\",\"fields\":[{\"name\":\"a\",\"type\":\"string\"}]}")); r2.put("a", "x"); return raw("(a/->ARec \"R2\" [\"a\"] [(a/->AStr \"x\")])", r2); });
        err("union-str-in-complex", UNION_NAMED, () -> s("x"));
        err("union-array-bad", "[\"null\",{\"type\":\"array\",\"items\":\"int\"}]", () -> arr(i(1), s("s")));
        err("union-in-array-bad", "{\"type\":\"array\",\"items\":[\"null\",\"int\"]}", () -> arr(i(1), s("z")));
        err("union-in-map-bad", "{\"type\":\"map\",\"values\":[\"null\",\"int\"]}", () -> map("k", s("z")));
        err("str-null", p("string"), () -> nul());
        err("int-null", p("int"), () -> nul());
        err("long-null", p("long"), () -> nul());
        err("float-null", p("float"), () -> nul());
        err("double-null", p("double"), () -> nul());
        err("bool-null", p("boolean"), () -> nul());
        err("bytes-null", p("bytes"), () -> nul());
        err("int-str", p("int"), () -> s("x"));
        err("long-bool", p("long"), () -> bool(true));
        err("float-str", p("float"), () -> s("s"));
        err("double-bytes", p("double"), () -> by(1));
        err("str-int", p("string"), () -> i(5));
        err("str-bytes", p("string"), () -> by(1));
        err("bool-int", p("boolean"), () -> i(1));
        err("bytes-str", p("bytes"), () -> s("x"));
        err("array-int", AI, () -> i(5));
        err("array-null", AI, () -> nul());
        err("array-null-elem", AI, () -> arr(i(1), nul()));
        err("array-union-null-array", "{\"type\":\"array\",\"items\":[\"null\",\"int\"]}", () -> nul());
        err("map-int", MI, () -> i(5));
        err("map-null", MI, () -> nul());
        err("map-null-value", MI, () -> map("k", nul()));
        err("enum-null", ENUM_E, () -> nul());
        err("enum-str", ENUM_E, () -> s("B"));
        err("enum-int", ENUM_E, () -> i(5));
        err("enum-unknown", ENUM_E, () -> new V("(a/->AEnum \"n.E\" \"Z\")", new GenericData.EnumSymbol(reg.get("n.E"), "Z")));
        err("fixed-null", FIXED_F, () -> nul());
        err("fixed-int", FIXED_F, () -> i(5));
        err("fixed-short", FIXED_F, () -> fx("F", 1, 2));
        err("fixed-bytes", FIXED_F, () -> raw("(a/->ABytes (bx \"01020304\"))", ByteBuffer.wrap(new byte[]{1, 2, 3, 4})));
        err("record-str", R_ABC, () -> s("str"));
        err("record-null", R_ABC, () -> nul());
        err("record-all-null", R_ABC, () -> rec("n.R", "a", nul(), "b", nul(), "c", nul(), "d", nul()));
        err("record-a-int", R_ABC, () -> rec("n.R", "a", i(5), "b", nul(), "c", arr(), "d", map()));
        err("record-b-str", R_ABC, () -> rec("n.R", "a", s("x"), "b", s("str"), "c", arr(), "d", map()));
        err("record-c-null-elem", R_ABC, () -> rec("n.R", "a", s("x"), "b", nul(), "c", arr(s("p"), nul()), "d", map()));
        err("record-c-int-elem", R_ABC, () -> rec("n.R", "a", s("x"), "b", nul(), "c", arr(i(1)), "d", map()));
        err("record-c-str", R_ABC, () -> rec("n.R", "a", s("x"), "b", nul(), "c", s("notlist"), "d", map()));
        err("record-d-str", R_ABC, () -> rec("n.R", "a", s("x"), "b", nul(), "c", arr(), "d", s("notmap")));
        err("record-d-str-val", R_ABC, () -> rec("n.R", "a", s("x"), "b", nul(), "c", arr(), "d", map("k", s("v"))));
        err("record-d-null-val", R_ABC, () -> rec("n.R", "a", s("x"), "b", nul(), "c", arr(), "d", map("k", nul())));
        err("outer-inner-s-null", OUTER, () -> rec("x.y.Outer", "inner", rec("x.y.Inner", "s", nul(), "e", nul(), "u", nul(), "xs", nul(), "f", nul(), "fl", nul()), "list", arr(), "m", map(), "ou", nul()));
        err("outer-inner-e-null", OUTER, () -> rec("x.y.Outer", "inner", rec("x.y.Inner", "s", s("x"), "e", nul(), "u", nul(), "xs", nul(), "f", nul(), "fl", nul()), "list", arr(), "m", map(), "ou", nul()));
        err("outer-inner-e-str", OUTER, () -> rec("x.y.Outer", "inner", rec("x.y.Inner", "s", s("x"), "e", s("A"), "u", nul(), "xs", nul(), "f", nul(), "fl", nul()), "list", arr(), "m", map(), "ou", nul()));
        err("outer-inner-xs-null", OUTER, () -> rec("x.y.Outer", "inner", rec("x.y.Inner", "s", s("x"), "e", en("x.y.E", "A"), "u", nul(), "xs", nul(), "f", nul(), "fl", nul()), "list", arr(), "m", map(), "ou", nul()));
        err("outer-inner-u-str", OUTER, () -> rec("x.y.Outer", "inner", rec("x.y.Inner", "s", s("x"), "e", en("x.y.E", "A"), "u", s("q"), "xs", arr(), "f", fx("x.y.F", 1, 2), "fl", f(1f)), "list", arr(), "m", map(), "ou", nul()));
        err("outer-inner-xs-str", OUTER, () -> rec("x.y.Outer", "inner", rec("x.y.Inner", "s", s("x"), "e", en("x.y.E", "A"), "u", nul(), "xs", arr(i(1), s("z")), "f", fx("x.y.F", 1, 2), "fl", f(1f)), "list", arr(), "m", map(), "ou", nul()));
        err("outer-inner-f-null", OUTER, () -> rec("x.y.Outer", "inner", rec("x.y.Inner", "s", s("x"), "e", en("x.y.E", "A"), "u", nul(), "xs", arr(), "f", nul(), "fl", nul()), "list", arr(), "m", map(), "ou", nul()));
        err("outer-inner-f-short", OUTER, () -> rec("x.y.Outer", "inner", rec("x.y.Inner", "s", s("x"), "e", en("x.y.E", "A"), "u", nul(), "xs", arr(), "f", fx("x.y.F", 1), "fl", nul()), "list", arr(), "m", map(), "ou", nul()));
        err("outer-inner-fl-null", OUTER, () -> rec("x.y.Outer", "inner", rec("x.y.Inner", "s", s("x"), "e", en("x.y.E", "A"), "u", nul(), "xs", arr(), "f", fx("x.y.F", 1, 2), "fl", nul()), "list", arr(), "m", map(), "ou", nul()));
        String goodInner = "rec(\"x.y.Inner\", \"s\", s(\"y\"), \"e\", en(\"x.y.E\", \"A\"), \"u\", nul(), \"xs\", arr(), \"f\", fx(\"x.y.F\", 1, 2), \"fl\", f(1f))";
        err("outer-ou-str", OUTER, () -> rec("x.y.Outer", "inner", rec("x.y.Inner", "s", s("y"), "e", en("x.y.E", "A"), "u", nul(), "xs", arr(), "f", fx("x.y.F", 1, 2), "fl", f(1f)), "list", arr(), "m", map(), "ou", s("str")));
        err("outer-ou-inner-s-null", OUTER, () -> rec("x.y.Outer", "inner", rec("x.y.Inner", "s", s("y"), "e", en("x.y.E", "A"), "u", nul(), "xs", arr(), "f", fx("x.y.F", 1, 2), "fl", f(1f)), "list", arr(), "m", map(),
            "ou", rec("x.y.Inner", "s", nul(), "e", en("x.y.E", "A"), "u", nul(), "xs", arr(), "f", fx("x.y.F", 1, 2), "fl", f(1f))));
        err("outer-list-bad-elem", OUTER, () -> rec("x.y.Outer", "inner", rec("x.y.Inner", "s", s("y"), "e", en("x.y.E", "A"), "u", nul(), "xs", arr(), "f", fx("x.y.F", 1, 2), "fl", f(1f)), "list", arr(s("bad")), "m", map(), "ou", nul()));
        err("outer-list-s-null", OUTER, () -> rec("x.y.Outer", "inner", rec("x.y.Inner", "s", s("y"), "e", en("x.y.E", "A"), "u", nul(), "xs", arr(), "f", fx("x.y.F", 1, 2), "fl", f(1f)),
            "list", arr(rec("x.y.Inner", "s", s("y"), "e", en("x.y.E", "A"), "u", nul(), "xs", arr(), "f", fx("x.y.F", 1, 2), "fl", f(1f)), rec("x.y.Inner", "s", nul(), "e", en("x.y.E", "A"), "u", nul(), "xs", arr(), "f", fx("x.y.F", 1, 2), "fl", f(1f))), "m", map(), "ou", nul()));
        err("outer-m-bad", OUTER, () -> rec("x.y.Outer", "inner", rec("x.y.Inner", "s", s("y"), "e", en("x.y.E", "A"), "u", nul(), "xs", arr(), "f", fx("x.y.F", 1, 2), "fl", f(1f)), "list", arr(), "m", map("k", s("zz")), "ou", nul()));
        err("outer-m-s-null", OUTER, () -> rec("x.y.Outer", "inner", rec("x.y.Inner", "s", s("y"), "e", en("x.y.E", "A"), "u", nul(), "xs", arr(), "f", fx("x.y.F", 1, 2), "fl", f(1f)), "list", arr(),
            "m", map("k", rec("x.y.Inner", "s", nul(), "e", en("x.y.E", "A"), "u", nul(), "xs", arr(), "f", fx("x.y.F", 1, 2), "fl", f(1f))), "ou", nul()));
        err("nested-arrays-bad", "{\"type\":\"array\",\"items\":{\"type\":\"array\",\"items\":\"int\"}}", () -> arr(arr(i(1), s("s"))));
        err("nested-arrays-bad-inner", "{\"type\":\"array\",\"items\":{\"type\":\"array\",\"items\":\"int\"}}", () -> arr(s("s")));
        err("nested-maps-bad", "{\"type\":\"map\",\"values\":{\"type\":\"map\",\"values\":\"int\"}}", () -> map("k", map("j", s("x"))));
        err("array-of-rec-null-field", "{\"type\":\"array\",\"items\":{\"type\":\"record\",\"name\":\"Q\",\"fields\":[{\"name\":\"a\",\"type\":\"int\"}]}}", () -> arr(rec("Q", "a", nul())));
        err("array-of-rec-null-elem", "{\"type\":\"array\",\"items\":{\"type\":\"record\",\"name\":\"Q\",\"fields\":[{\"name\":\"a\",\"type\":\"int\"}]}}", () -> arr(nul()));
        String UR = "[\"null\",{\"type\":\"record\",\"name\":\"Q\",\"namespace\":\"n\",\"fields\":[{\"name\":\"a\",\"type\":\"string\"}]}]";
        err("root-union-rec-null-field", UR, () -> rec("n.Q", "a", nul()));
        err("root-union-array-null-elem", "[\"null\",{\"type\":\"array\",\"items\":\"int\"}]", () -> arr(nul()));
        err("field-union-array-null-elem", "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"x\",\"type\":[\"null\",{\"type\":\"array\",\"items\":\"int\"}]}]}", () -> rec("R", "x", arr(nul())));
        err("field-union-map-null", "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"y\",\"type\":[\"null\",{\"type\":\"map\",\"values\":\"int\"}]}]}", () -> rec("R", "y", map("k", nul())));
        err("field-union-rec-null", "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"z\",\"type\":[\"null\",{\"type\":\"record\",\"name\":\"Q\",\"fields\":[{\"name\":\"a\",\"type\":\"string\"}]},{\"type\":\"fixed\",\"name\":\"F\",\"size\":1}]}]}", () -> rec("R", "z", rec("Q", "a", nul())));
        err("root-union-enum-unknown", "[\"null\",{\"type\":\"enum\",\"name\":\"E\",\"symbols\":[\"A\"]}]", () -> new V("(a/->AEnum \"E\" \"Z\")", new GenericData.EnumSymbol(reg.get("E"), "Z")));
        err("root-union-fixed-short", "[\"null\",{\"type\":\"fixed\",\"name\":\"F\",\"size\":1}]", () -> fx("F"));
        err("cdc-sequence-str", CDC, () -> rec("com.sforce.eventbus.AccountChangeEvent",
            "ChangeEventHeader", rec("com.sforce.eventbus.ChangeEventHeader",
                "entityName", s("Account"), "recordIds", arr(s("001")), "changeType", en("com.sforce.eventbus.ChangeType", "UPDATE"),
                "changedFields", arr(), "nulledFields", arr(), "diffFields", arr(), "transactionKey", s("k"), "sequenceNumber", s("1"),
                "commitTimestamp", l(1), "commitNumber", l(1), "commitUser", s("u")),
            "Id", nul(), "Name", nul(), "NumberOfEmployees", nul(), "AnnualRevenue", nul(), "BillingAddress", nul(), "LastModifiedDate", nul()));
        err("cdc-employees-long", CDC, () -> rec("com.sforce.eventbus.AccountChangeEvent",
            "ChangeEventHeader", rec("com.sforce.eventbus.ChangeEventHeader",
                "entityName", s("Account"), "recordIds", arr(s("001")), "changeType", en("com.sforce.eventbus.ChangeType", "UPDATE"),
                "changedFields", arr(), "nulledFields", arr(), "diffFields", arr(), "transactionKey", s("k"), "sequenceNumber", i(1),
                "commitTimestamp", l(1), "commitNumber", l(1), "commitUser", s("u")),
            "Id", nul(), "Name", nul(), "NumberOfEmployees", l(5), "AnnualRevenue", nul(), "BillingAddress", nul(), "LastModifiedDate", nul()));
        err("union-datum-bytes", "{\"type\":\"record\",\"name\":\"B\",\"fields\":[{\"name\":\"u\",\"type\":[\"null\",\"int\"]}]}", () -> rec("B", "u", by(1, 2)));
        err("union-datum-fixed", "{\"type\":\"record\",\"name\":\"B\",\"fields\":[{\"name\":\"u\",\"type\":[\"null\",\"int\"]}]}", () -> raw("(a/->ARec \"B\" [\"u\"] [(a/->AFixed \"F\" (bx \"01ff\"))])",
            rec("B", "u", new V("", new GenericData.Fixed(new Schema.Parser().parse("{\"type\":\"fixed\",\"name\":\"F\",\"size\":2}"), new byte[]{1, -1}))).j));
        err("union-datum-str-escapes", "{\"type\":\"record\",\"name\":\"Out\",\"fields\":[{\"name\":\"in\",\"type\":{\"type\":\"record\",\"name\":\"B\",\"fields\":[{\"name\":\"s\",\"type\":\"string\"},{\"name\":\"u\",\"type\":[\"null\",\"int\"]}]}}]}", () -> rec("Out", "in", rec("B", "s", s("q\"\\\n\u00e9\u0001\u0085\u2028\u2000"), "u", s("x"))));
        err("union-datum-record-with-bytes", "{\"type\":\"record\",\"name\":\"Out\",\"fields\":[{\"name\":\"in\",\"type\":{\"type\":\"record\",\"name\":\"B\",\"fields\":[{\"name\":\"b\",\"type\":\"bytes\"},{\"name\":\"d\",\"type\":\"double\"},{\"name\":\"m\",\"type\":{\"type\":\"map\",\"values\":\"int\"}},{\"name\":\"e\",\"type\":{\"type\":\"enum\",\"name\":\"EE\",\"symbols\":[\"A\"]}},{\"name\":\"u\",\"type\":[\"null\",\"int\"]}]}}]}",
            () -> rec("Out", "in", rec("B", "b", by(1, 2, 200), "d", d(1e10), "m", map("k", i(1)), "e", en("EE", "A"), "u", s("x"))));

        dec("long-empty", p("long"), "");
        dec("long-cont", p("long"), "80");
        dec("long-10b", p("long"), "ffffffffffffffff01");
        dec("long-11b", p("long"), "ffffffffffffffffffff01");
        dec("long-10b-big", p("long"), "ffffffffffffffffff7f");
        dec("int-5b", p("int"), "ffffffff0f");
        dec("int-5b-big", p("int"), "808080807f");
        dec("int-6b", p("int"), "ffffffffff0f");
        dec("int-noncanonical", p("int"), "8200");
        dec("string-trunc", p("string"), "0a61");
        dec("string-neg", p("string"), "01");
        dec("string-neg2", p("string"), "0161");
        dec("string-ok-nonutf8", p("string"), "02ff");
        dec("bytes-trunc", p("bytes"), "0a61");
        dec("bool-2", p("boolean"), "02");
        dec("bool-1", p("boolean"), "01");
        dec("bool-empty", p("boolean"), "");
        dec("float-trunc", p("float"), "0102");
        dec("double-trunc", p("double"), "0102");
        dec("union-idx-2", "[\"null\",\"string\"]", "04");
        dec("union-idx-neg", "[\"null\",\"string\"]", "03");
        dec("union-idx-neg1", "[\"null\",\"string\"]", "01");
        dec("union-idx-128", "[\"null\",\"string\"]", "ff01");
        dec("union-empty", "[\"null\",\"string\"]", "");
        dec("enum-idx-2", "{\"type\":\"enum\",\"name\":\"E\",\"symbols\":[\"A\",\"B\"]}", "04");
        dec("enum-idx-neg", "{\"type\":\"enum\",\"name\":\"E\",\"symbols\":[\"A\",\"B\"]}", "03");
        dec("enum-empty", "{\"type\":\"enum\",\"name\":\"E\",\"symbols\":[\"A\",\"B\"]}", "");
        dec("fixed-trunc", FIXED_F, "010203");
        dec("array-ok", AI, "0402040 0".replace(" ", ""));
        dec("array-neg-count", AI, "0304020400");
        dec("array-neg-count-trunc", AI, "03040204");
        dec("array-count-too-big", AI, "0202");
        dec("array-trunc-item", AI, "010200");
        dec("array-two-blocks", AI, "0202" + "0204" + "00");
        dec("array-huge-count", AI, "80808080808080808001");
        dec("array-empty-input", AI, "");
        dec("array-no-terminator", AI, "0202");
        dec("array-neg-size-trunc", AI, "03");
        dec("map-ok", MI, "0202" + "6b" + "0200");
        dec("map-trunc", MI, "02026b02");
        dec("map-neg-count", MI, "01" + "04" + "026b" + "0200");
        dec("map-two-blocks", MI, "0201" + "6102" + "0201" + "6204" + "00");
        dec("map-dup-key", MI, "04" + "026b02" + "026b04" + "00");
        dec("array-of-null", "{\"type\":\"array\",\"items\":\"null\"}", "0600");
        dec("record-ok", R_ABC, "027800" + "0000");
        dec("record-b-3", R_ABC, "0278" + "0206" + "0000");
        dec("record-b-bad", R_ABC, "0278" + "0406" + "0000");
        dec("record-trunc", R_ABC, "0278");
        dec("list-trunc", LIST, "0202");
        dec("float-nan-canon", p("float"), "0000c07f");
        dec("double-nan-payload", p("double"), "230100000000f87f");

        String[] schemas = {
            "\"foo\"", "{\"type\":\"foo\"}", "[\"string\",\"string\"]", "[\"null\",[\"null\"]]", "{\"type\":\"fixed\",\"name\":\"f\"}",
            "{\"type\":\"record\",\"name\":\"r\"}", "{\"type\":\"record\",\"name\":\"1r\",\"fields\":[]}", "{\"type\":\"record\",\"name\":\"r-x\",\"fields\":[]}",
            "{\"type\":\"enum\",\"name\":\"e\",\"symbols\":[\"A\",\"A\"]}", "{\"type\":\"enum\",\"name\":\"e\",\"symbols\":[\"1\"]}", "{\"type\":\"enum\",\"name\":\"e\"}",
            "[{\"type\":\"fixed\",\"name\":\"f\",\"size\":1},{\"type\":\"fixed\",\"name\":\"f\",\"size\":1}]",
            "{\"type\":\"record\",\"name\":\"r\",\"fields\":[{\"name\":\"a\",\"type\":\"int\"},{\"name\":\"a\",\"type\":\"int\"}]}",
            "{\"type\":\"record\",\"name\":\"r\",\"fields\":[{\"name\":\"a\"}]}", "{\"type\":\"record\",\"name\":\"r\",\"fields\":[{\"type\":\"int\"}]}",
            "{\"type\":\"record\",\"fields\":[]}", "{\"type\":\"array\"}", "{\"type\":\"map\"}", "{\"name\":\"x\"}", "5", "{\"type\":5}", "null",
            "{\"type\":\"fixed\",\"name\":\"f\",\"size\":\"x\"}", "[]",
            "{\"type\":\"record\",\"name\":\"r\",\"fields\":[{\"name\":\"a\",\"type\":\"int\",\"default\":\"x\"}]}",
            "{\"type\":\"record\",\"name\":\"r\",\"fields\":5}",
            "{\"type\":\"record\",\"name\":\"r\",\"fields\":[{\"name\":\"a\",\"type\":\"int\",\"default\":1}],\"x\":1}",
            "{\"type\":\"record\",\"name\":\"a.b.r\",\"namespace\":\"zz\",\"fields\":[{\"name\":\"x\",\"type\":\"r\"}]}",
            "{\"type\":\"record\",\"name\":\"a.b.r\",\"fields\":[{\"name\":\"x\",\"type\":[\"null\",\"a.b.r\"]}]}",
            "{\"type\":\"enum\",\"name\":\"e\",\"symbols\":[\"A\"],\"default\":\"B\"}",
            "{\"type\":\"record\",\"name\":\"r\",\"namespace\":\"n\",\"fields\":[{\"name\":\"x\",\"type\":{\"type\":\"enum\",\"name\":\"e\",\"symbols\":[\"A\"]}},{\"name\":\"y\",\"type\":\"e\"},{\"name\":\"z\",\"type\":\"n.e\"}]}",
            "{\"type\":\"record\",\"name\":\"r\",\"namespace\":\"n\",\"fields\":[{\"name\":\"x\",\"type\":{\"type\":\"enum\",\"name\":\"e\",\"namespace\":\"q\",\"symbols\":[\"A\"]}},{\"name\":\"y\",\"type\":\"e\"}]}",
            "{\"type\":\"record\",\"name\":\"string\",\"fields\":[]}",
            "\"string\" ",
            "{\"type\":\"array\",\"items\":\"foo\"}", "{\"type\":\"map\",\"values\":\"foo\"}", "[\"null\",\"foo\"]",
            "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"a\",\"type\":\"foo\"}]}",
            "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"a\",\"type\":[\"null\",\"string\"],\"default\":null}]}",
            "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"a\",\"type\":[\"string\",\"null\"],\"default\":null}]}",
            "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"a\",\"type\":[\"null\",\"string\"],\"default\":\"x\"}]}",
            "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"a\",\"type\":\"long\",\"default\":1}]}",
            "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"a\",\"type\":{\"type\":\"array\",\"items\":\"int\"},\"default\":[]}]}",
            "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"a\",\"type\":\"R\"}]}",
            "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"a\",\"type\":[\"R\"]}]}",
            "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"a\",\"type\":[\"null\",\"R\",\"R\"]}]}",
            "[\"null\",{\"type\":\"array\",\"items\":\"int\"},{\"type\":\"array\",\"items\":\"string\"}]",
            "[\"null\",{\"type\":\"map\",\"values\":\"int\"},{\"type\":\"map\",\"values\":\"string\"}]",
            "[{\"type\":\"string\"},\"string\"]", "{\"type\":[\"null\",\"int\"]}",
            "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"a\",\"type\":{\"type\":\"record\",\"name\":\"R\",\"fields\":[]}}]}",
            "{\"type\":\"record\",\"name\":\"R\",\"namespace\":\"\",\"fields\":[]}", "{\"type\":\"enum\",\"name\":\"E\",\"symbols\":[]}",
            "{\"type\":\"record\",\"name\":\"a.b\",\"fields\":[{\"name\":\"x\",\"type\":{\"type\":\"enum\",\"name\":\"c\",\"symbols\":[\"A\"]}},{\"name\":\"y\",\"type\":\"a.c\"}]}",
            "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"a\",\"type\":\"int\"},{\"name\":\"b\",\"type\":{\"type\":\"int\"}}]}",
            "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"x-y\",\"type\":\"int\"}]}",
            "{\"type\":\"record\",\"name\":\"\",\"fields\":[]}", "{\"type\":\"enum\",\"name\":\"E\",\"symbols\":[\"A\",5]}",
            "{\"type\":\"fixed\",\"name\":\"F\",\"size\":0}", "{\"type\":\"fixed\",\"name\":\"F\",\"size\":1.5}",
            "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"a\",\"type\":\"int\",\"default\":null}]}",
            "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"a\",\"type\":\"string\",\"default\":null}]}",
            "{\"type\":\"record\",\"name\":\"R\",\"namespace\":\"n\",\"doc\":\"d\",\"aliases\":[\"zz\"],\"x\":{\"y\":1},\"fields\":[{\"name\":\"a\",\"aliases\":[\"b\"],\"type\":\"string\",\"doc\":\"dd\",\"default\":\"q\",\"order\":\"ignore\",\"p\":1.50},{\"name\":\"l\",\"type\":{\"type\":\"long\",\"logicalType\":\"timestamp-millis\"}},{\"name\":\"e\",\"type\":{\"type\":\"enum\",\"name\":\"E\",\"symbols\":[\"A\"],\"default\":\"A\",\"doc\":\"edoc\"}},{\"name\":\"f\",\"type\":{\"type\":\"fixed\",\"name\":\"F\",\"size\":2,\"namespace\":\"\"}},{\"name\":\"g\",\"type\":\"n.E\"},{\"name\":\"h\",\"type\":[\"null\",{\"type\":\"map\",\"values\":\"F\",\"k\":2}]}]}",
            "{\"type\":\"record\",\"name\":\"n.R\",\"namespace\":\"zz\",\"fields\":[{\"name\":\"a\",\"type\":{\"type\":\"record\",\"name\":\"Z\",\"fields\":[]}},{\"name\":\"b\",\"type\":{\"type\":\"record\",\"name\":\"Y\",\"namespace\":\"\",\"fields\":[]}},{\"name\":\"c\",\"type\":\"Z\"},{\"name\":\"d\",\"type\":\"n.Z\"}]}",
            "{\"type\":\"string\"}", "{\"type\":\"string\",\"x\":1}", "{\"type\":\"array\",\"items\":{\"type\":\"int\"}}",
            "{\"type\":\"error\",\"name\":\"Err\",\"fields\":[{\"name\":\"m\",\"type\":\"string\"}]}",
            "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"a\",\"type\":{\"type\":\"enum\",\"name\":\"E\",\"namespace\":\"q\",\"symbols\":[\"X\"]}},{\"name\":\"b\",\"type\":{\"type\":\"record\",\"name\":\"S\",\"fields\":[{\"name\":\"e\",\"type\":\"q.E\"}]}}]}",
            "{\"type\":\"record\",\"name\":\"R\",\"fields\":[{\"name\":\"a\",\"type\":\"double\",\"default\":1.0},{\"name\":\"b\",\"type\":\"float\",\"default\":2},{\"name\":\"c\",\"type\":\"bytes\",\"default\":\"\\u00ff\"},{\"name\":\"d\",\"type\":{\"type\":\"map\",\"values\":\"int\"},\"default\":{\"k\":1}}]}",
            CDC, EVT, LIST, OUTER, UNION_NAMED, UNION_ALL, R_ABC,
        };
        for (String sj : schemas) parse(sj);

        StringBuilder out = new StringBuilder();
        out.append("(ns avro-golden-data (:require [mulay.lib.avro :as a]))\n");
        out.append(";; GENERATED by tools/gen-avro-golden.java (Apache Avro ").append(Schema.class.getPackage().getImplementationVersion()).append(", Java ").append(System.getProperty("java.version")).append(") -- do not edit.\n");
        out.append("(defrecord GCase [name: Str schema: Str value: a/AVal hex: Str dump: Str])\n");
        out.append("(defrecord ECase [name: Str schema: Str value: a/AVal err: Str])\n\n");
        out.append("(defn- hv Int [c: Int] (if (< c 58) (- c 48) (- c 87)))\n\n(defn bx Str [h: Str]\n  (loop [i 0 o \"\"]\n    (if (>= i (count h)) o\n      (recur (+ i 2) (str o (chr (+ (* 16 (hv (nth h i))) (hv (nth h (+ i 1))))))))))\n\n");
        out.append("(def CASES: Vec(GCase) [\n").append(cases).append("])\n\n");
        out.append("(def ECASES: Vec(ECase) [\n").append(ecases).append("])\n\n");
        out.append("(def DCASES: Vec(Vec(Str)) [\n").append(dcases).append("])\n\n");
        out.append("(def PCASES: Vec(Vec(Str)) [\n").append(pcases).append("])\n");
        new PrintStream(System.out, true, "UTF-8").print(out);
    }
}
