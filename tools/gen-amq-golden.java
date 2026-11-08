// test/amq/amq_gold_test.clay を作る: Anypoint MQ コネクタ (anypoint-mq-connector 4.0.23 と、それが使う
// anypoint-mq-rest-client 5.1.500、Gson 2.12.0。実 Mule のアプリに入る版) の純粋な部分の答え。
//   - ackToken の作り方 (AckToken.getEncodedAckToken: Gson の JSON を Base64) と読み方 (decodeAckToken。失敗の文言)
//   - URL のパスに入れる messageId / lockId (URLEncoder.encode(.., "UTF-8"))
//   - publish の本文の JSON (AnypointMQMessageBuilder と JsonUtils.toJson。headers と properties は HashMap の順)
//   - receive の応答の読み方 (JsonUtils.fromJson と convertToAnypointMQMessage。HashMap の順と値の型)
//   - messageGroupId の検査 (AnypointMQOperations の正規表現)
//
//   M=~/.m2/repository
//   CP=$M/com/mulesoft/muleesb/modules/anypoint-mq-rest-client/5.1.500/anypoint-mq-rest-client-5.1.500.jar:$M/com/mulesoft/connectors/anypoint-mq-connector/4.0.23/anypoint-mq-connector-4.0.23-mule-plugin.jar:$M/com/google/code/gson/gson/2.12.0/gson-2.12.0.jar:$M/com/google/guava/guava/32.0.1-jre/guava-32.0.1-jre.jar:$M/commons-io/commons-io/2.20.0/commons-io-2.20.0.jar:$M/org/slf4j/slf4j-api/2.0.9/slf4j-api-2.0.9.jar
//   /usr/lib/jvm/java-17-openjdk-amd64/bin/java -cp $CP tools/gen-amq-golden.java [mulay のルート]

import com.google.gson.reflect.TypeToken;
import com.mulesoft.extension.mq.internal.model.AckToken;
import com.mulesoft.mq.restclient.client.mq.domain.*;
import com.mulesoft.mq.restclient.utils.JsonUtils;
import java.io.ByteArrayInputStream;
import java.lang.reflect.Type;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.regex.Pattern;

public class GenAmqGolden {
    static String clayStr(String s) {
        StringBuilder b = new StringBuilder();
        List<String> parts = new ArrayList<>();
        for (char c : s.toCharArray()) {
            if (c < 0x20 && c != '\n' && c != '\t' && c != '\r') {
                parts.add("\"" + b + "\"");
                parts.add("(chr " + (int) c + ")");
                b.setLength(0);
                continue;
            }
            switch (c) {
                case '"': b.append("\\\""); break;
                case '\\': b.append("\\\\"); break;
                case '\n': b.append("\\n"); break;
                case '\t': b.append("\\t"); break;
                case '\r': b.append("\\r"); break;
                default: b.append(c);
            }
        }
        if (parts.isEmpty()) return "\"" + b + "\"";
        parts.add("\"" + b + "\"");
        return "(str " + String.join(" ", parts) + ")";
    }

    static String b64(String s) { return Base64.getEncoder().encodeToString(s.getBytes(StandardCharsets.UTF_8)); }

    static String nz(String s) { return s == null ? "null" : s; }

    public static void main(String[] args) throws Exception {
        Path root = Paths.get(args.length > 0 ? args[0] : ".").toAbsolutePath().normalize();
        StringBuilder b = new StringBuilder();
        b.append("(ns amq-gold-test (:require [mulay.conn.amq_wire :as w] [mulay.dw.val :as v] [clay.string :as str]))\n\n");
        b.append(";; 生成物: tools/gen-amq-golden.java (手で編集しない)。期待値は anypoint-mq-connector 4.0.23、\n");
        b.append(";; anypoint-mq-rest-client 5.1.500、Gson 2.12.0 を Java 17 で直接呼んで得たもの。\n\n");
        b.append("(defn- tok-str Str [t: Str] (let [[x e] (w/ack-token-decode t)] (if (not= e \"\") (str \"ERR \" e) (w/token-str x))))\n");
        b.append("(defn- recv-str Str [j: Str] (let [[ms e] (w/parse-receive j)] (if (not= e \"\") (str \"ERR \" e) (w/msgs-str ms))))\n\n");

        // --- ackToken を作る
        String[][] enc = {
            {"mulay-test-q", "m1", "2_AQEBuE5y+/x9Ab=="},
            {"q", "<a&b>'\"\\", "l\u0001 é"},
            {"キュー", "日本語", "x\ty\n"},
            {"q", "id-1", "AQEB/abc+def="},
        };
        b.append("(deftest ack-token-encode\n");
        for (String[] c : enc) {
            String t = new AckToken(c[0], c[1], c[2]).getEncodedAckToken();
            b.append("  (is (= (w/ack-token ").append(clayStr(c[0])).append(" ").append(clayStr(c[1])).append(" ").append(clayStr(c[2])).append(")\n         ").append(clayStr(t)).append("))\n");
        }
        b.append(")\n\n");

        // --- ackToken を読む
        String[] dec = {
            new AckToken("mulay-test-q", "m1", "2_AQEBuE5y+/x9Ab==").getEncodedAckToken(),
            new AckToken("q", "<a&b>'\"\\", "l\u0001 é").getEncodedAckToken(),
            "not-a-token", "aGVsbG8=", "e30=", "W10=", "MTIz", "dHJ1ZQ==", "a", "ab", "abc", "abcde", "ab=c", "ab==c", " e30=", "e30", "e3=0",
            "é", "YWJj\n", "@@@@",
            b64("{\"destination\":\"d\",\"messageId\":5,\"lockId\":\"l\"}"),
            b64("{\"x\":1,\"messageId\":\"m\"}"),
            b64("{'destination':'d','lockId':'l'}"),
            b64("{destination:d,lockId:l}"),
            b64("{\"destination\":\"d\""),
            b64("{\"destination\":\"d\",}"),
            b64("{\"destination\":\"d\" \"lockId\":\"l\"}"),
            b64("{\"destination\":\"d\\u0041\\n\"}"),
            b64("null"),
            b64(""),
            b64("   "),
            b64("{\"destination\":null,\"messageId\":\"m\"}"),
            b64("{\"destination\":\"d\",\"destination\":\"e\"}"),
            b64("{\"lockId\":true}"),
            b64("{\"lockId\":{}}"),
            b64("{\"lockId\":[]}"),
            b64("{} trailing"),
            b64("[1]"),
        };
        b.append("(deftest ack-token-decode\n");
        for (String t : dec) {
            String out;
            try {
                AckToken k = AckToken.decodeAckToken(t);
                out = k == null ? "NULL" : nz(k.getDestination()) + "|" + nz(k.getMessageId()) + "|" + nz(k.getLockId());
            } catch (Exception e) {
                out = "ERR " + e.getMessage();
            }
            b.append("  (is (= (tok-str ").append(clayStr(t)).append(") ").append(clayStr(out)).append("))\n");
        }
        b.append(")\n\n");

        // --- URLEncoder
        String[] urls = {"m1", "a b+c/d=e&f?g#h", "日本", "~*._-", "%41", "2_AQEBuE5y+/x9Ab==", "é\u0001"};
        b.append("(deftest url-encode\n");
        for (String u : urls) {
            b.append("  (is (= (w/url-encode ").append(clayStr(u)).append(") ").append(clayStr(URLEncoder.encode(u, "UTF-8"))).append("))\n");
        }
        b.append(")\n\n");

        // --- publish の本文 (AnypointMQServiceClient.createMessage と同じ組み立て)
        b.append("(deftest publish-json\n");
        Object[][] pubs = {
            // body, messageId, delay, group, contentType, encoding, props (k, v, ...)
            {"hello", "m1", null, null, "text/plain; charset=UTF-8", "UTF-8", new Object[]{}},
            {"{\"a\": 1}\n", "id-2", 2000L, "g1", "application/json; charset=UTF-8", "UTF-8", new Object[]{"s", "x", "n", 1, "big", 12345678901234L, "d", 1.5, "b", "true"}},
            {"<x>&'=</x>", "m3", null, null, null, null, new Object[]{"contentType", "app/override", "k=v", "<&>"}},
            {"é\u0001 ", "m4", 0L, null, "*/*", null, new Object[]{"zz", "1", "aa", "2", "MULE_ENCODING", "x"}},
        };
        for (Object[] p : pubs) {
            AnypointMQMessageBuilder mb = new AnypointMQMessageBuilder();
            mb.withBody(new ByteArrayInputStream(((String) p[0]).getBytes(StandardCharsets.UTF_8)));
            mb.withMessageId((String) p[1]);
            mb.withDeliveryDelay(Optional.ofNullable((Long) p[2]));
            mb.withMessageGroupId(Optional.ofNullable((String) p[3]));
            if (p[4] != null) {
                mb.addProperty("contentType", p[4]);
                if (p[5] != null) mb.addProperty("MULE_ENCODING", p[5]);
            }
            Object[] kv = (Object[]) p[6];
            Map<String, Object> props = new LinkedHashMap<>();
            for (int i = 0; i < kv.length; i += 2) props.put((String) kv[i], kv[i + 1]);
            mb.withProperties(props);
            String json = JsonUtils.toJson(mb.build());
            // mulay 側の引数: headers と properties は (名前 値の JSON) の Vec。足した順
            StringBuilder hs = new StringBuilder("[(w/->Kv \"messageId\" (w/->JStr " + clayStr((String) p[1]) + "))");
            if (p[2] != null) hs.append(" (w/->Kv \"deliveryDelay\" (w/->JStr \"").append(((Long) p[2]).intValue()).append("\"))");
            if (p[3] != null) hs.append(" (w/->Kv \"messageGroupId\" (w/->JStr ").append(clayStr((String) p[3])).append("))");
            hs.append("]");
            StringBuilder ps = new StringBuilder("[");
            if (p[4] != null) {
                ps.append("(w/->Kv \"contentType\" (w/->JStr ").append(clayStr((String) p[4])).append("))");
                if (p[5] != null) ps.append(" (w/->Kv \"MULE_ENCODING\" (w/->JStr ").append(clayStr((String) p[5])).append("))");
            }
            for (int i = 0; i < kv.length; i += 2) {
                Object x = kv[i + 1];
                String jv = x instanceof String ? "(w/->JStr " + clayStr((String) x) + ")" : "(w/->JNum \"" + x + "\")";
                ps.append(" (w/->Kv ").append(clayStr((String) kv[i])).append(" ").append(jv).append(")");
            }
            ps.append("]");
            b.append("  (is (= (w/publish-json ").append(clayStr((String) p[0])).append("\n                         ").append(hs).append("\n                         ").append(ps).append(")\n         ").append(clayStr(json)).append("))\n");
        }
        b.append(")\n\n");

        // --- receive の応答
        Type listType = new TypeToken<List<AnypointMQReceiveBatchResponse>>(){}.getType();
        String[] recvs = {
            "[ {\n  \"properties\" : {\n    \"b\" : \"true\",\n    \"contentType\" : \"text/plain; charset=UTF-8\",\n    \"MULE_ENCODING\" : \"UTF-8\",\n    \"n\" : 5\n  },\n  \"headers\" : {\n    \"messageId\" : \"test-1\",\n    \"lockId\" : \"2_AQEB+/x=\",\n    \"ttl\" : \"10000\",\n    \"created\" : \"Mon, 12 Oct 2026 03:45:16 GMT\",\n    \"deliveryCount\" : \"1\"\n  },\n  \"body\" : \"hello\"\n} ]",
            "[{\"properties\":{\"big\":12345678901234,\"d\":1.5,\"e\":1.0,\"f\":1e3,\"s\":\"x\",\"t\":true,\"neg\":-7,\"huge\":99999999999999999999},\"headers\":{\"messageId\":\"m\",\"lockId\":\"l\",\"ttl\":\"120000\",\"messageGroupId\":\"g\",\"created\":\"c\",\"deliveryCount\":\"2\",\"deliveryDelay\":\"2000\"},\"body\":\"line1\\nline2 \\u00e9 \\\"q\\\"\"},{\"properties\":{},\"headers\":{\"messageId\":\"m2\",\"lockId\":\"l2\"},\"body\":\"\"}]",
            "[]",
        };
        b.append("(deftest parse-receive\n");
        for (String r : recvs) {
            List<AnypointMQReceiveBatchResponse> rs = JsonUtils.fromJson(r, listType);
            StringBuilder o = new StringBuilder();
            for (AnypointMQReceiveBatchResponse x : rs) {
                AnypointMQMessage m = x.convertToAnypointMQMessage();
                o.append("H");
                for (Map.Entry<String, Object> e : m.getHeaders().entrySet()) o.append(" ").append(e.getKey()).append("=").append(e.getValue());
                o.append(" P");
                for (Map.Entry<String, Object> e : m.getProperties().entrySet())
                    o.append(" ").append(e.getKey()).append("=").append(e.getValue().getClass().getSimpleName()).append(":").append(e.getValue());
                o.append(" B ").append(m.getBodyAsString()).append(";");
            }
            b.append("  (is (= (recv-str ").append(clayStr(r)).append(")\n         ").append(clayStr(o.toString())).append("))\n");
        }
        b.append(")\n\n");

        // --- messageGroupId
        Pattern gp = Pattern.compile("^[a-zA-Z0-9\\p{Punct}]{1,128}$");
        String[] groups = {"g1", "has space", "", "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~", "日本", "a".repeat(128), "a".repeat(129), "tab\t"};
        b.append("(deftest group-id\n");
        for (String g : groups) {
            b.append("  (is (= (w/group-id-ok? ").append(clayStr(g)).append(") ").append(gp.matcher(g).matches()).append("))\n");
        }
        b.append(")\n");

        Path out = root.resolve("test/amq/amq_gold_test.clay");
        Files.write(out, b.toString().getBytes(StandardCharsets.UTF_8));
        System.out.println("wrote " + out);
    }
}
