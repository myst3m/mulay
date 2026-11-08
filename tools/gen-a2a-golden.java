// test/a2a/a2a_spec_gold_test.clay を作る: A2A の型の JSON を a2a-java-sdk 0.3.3 (Jackson 2.17.0、実 Mule の A2A
// コネクタ 1.1.1 が使う版) で読んで書き直した結果と、読めないときの文言 (Jackson の例外の getMessage)。
//
//   M=~/.m2/repository
//   CP=$M/io/github/a2asdk/a2a-java-sdk-spec/0.3.3.Final/a2a-java-sdk-spec-0.3.3.Final.jar:$M/io/github/a2asdk/a2a-java-sdk-common/0.3.3.Final/a2a-java-sdk-common-0.3.3.Final.jar:$M/com/fasterxml/jackson/core/jackson-databind/2.17.0/jackson-databind-2.17.0.jar:$M/com/fasterxml/jackson/core/jackson-core/2.17.0/jackson-core-2.17.0.jar:$M/com/fasterxml/jackson/core/jackson-annotations/2.17.0/jackson-annotations-2.17.0.jar:$M/com/fasterxml/jackson/datatype/jackson-datatype-jsr310/2.17.0/jackson-datatype-jsr310-2.17.0.jar
//   /usr/lib/jvm/java-17-openjdk-amd64/bin/java -cp $CP tools/gen-a2a-golden.java [mulay のルート]
//
// 入力に timestamp の無い TaskStatus は現在時刻が入るので、その値は "<ts>" に置き換える (mulay 側も now に "<ts>" を渡す)。

import com.fasterxml.jackson.core.type.TypeReference;
import io.a2a.spec.*;
import io.a2a.util.Utils;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

public class GenA2aGolden {
    static final Map<String, TypeReference<?>> TYPES = new LinkedHashMap<>();
    static {
        TYPES.put("EventKind", new TypeReference<EventKind>(){});
        TYPES.put("Message", new TypeReference<Message>(){});
        TYPES.put("Task", new TypeReference<Task>(){});
        TYPES.put("TaskStatus", new TypeReference<TaskStatus>(){});
        TYPES.put("MessageSendParams", new TypeReference<MessageSendParams>(){});
        TYPES.put("AgentCard", new TypeReference<AgentCard>(){});
        TYPES.put("TaskQueryParams", new TypeReference<TaskQueryParams>(){});
        TYPES.put("TaskIdParams", new TypeReference<TaskIdParams>(){});
        TYPES.put("StreamingEventKind", new TypeReference<StreamingEventKind>(){});
        TYPES.put("TaskPushNotificationConfig", new TypeReference<TaskPushNotificationConfig>(){});
        TYPES.put("GetTaskPushNotificationConfigParams", new TypeReference<GetTaskPushNotificationConfigParams>(){});
        TYPES.put("ListTaskPushNotificationConfigParams", new TypeReference<ListTaskPushNotificationConfigParams>(){});
        TYPES.put("DeleteTaskPushNotificationConfigParams", new TypeReference<DeleteTaskPushNotificationConfigParams>(){});
    }

    static final String[][] CASES = {
        {"EventKind", "{\"kind\":\"message\",\"role\":\"agent\",\"messageId\":\"m1\",\"parts\":[{\"kind\":\"text\",\"text\":\"hi\"}]}"},
        {"EventKind", "{\"messageId\":\"m1\",\"role\":\"user\",\"parts\":[{\"text\":\"a\",\"kind\":\"text\",\"metadata\":{\"k\":1}}],\"kind\":\"message\",\"contextId\":\"c\",\"taskId\":\"t\",\"referenceTaskIds\":[\"r1\"],\"extensions\":[],\"metadata\":{\"z\":true,\"a\":[1,2.5,\"x\",null]}}"},
        {"EventKind", "{\"kind\":\"task\",\"id\":\"t1\",\"contextId\":\"c1\",\"status\":{\"state\":\"completed\"}}"},
        {"EventKind", "{\"kind\":\"task\",\"id\":\"t1\",\"contextId\":\"c1\",\"status\":{\"state\":\"working\",\"timestamp\":\"2026-01-02T03:04:05Z\"},\"artifacts\":[{\"artifactId\":\"a\",\"parts\":[{\"kind\":\"data\",\"data\":{\"x\":1}}]}],\"history\":[{\"kind\":\"message\",\"role\":\"user\",\"messageId\":\"m\",\"parts\":[{\"kind\":\"file\",\"file\":{\"uri\":\"http://x/y\",\"mimeType\":\"text/plain\"}}]}],\"metadata\":{}}"},
        {"EventKind", "{\"kind\":\"task\",\"id\":\"t1\",\"contextId\":\"c1\",\"status\":{\"state\":\"failed\",\"timestamp\":\"2026-01-02T03:04:05.120+09:00\"}}"},
        {"EventKind", "{\"kind\":\"task\",\"id\":\"t1\",\"contextId\":\"c1\",\"status\":{\"state\":\"input-required\",\"timestamp\":\"2026-01-02T03:04:00.000Z\"}}"},
        {"EventKind", "{\"kind\":\"message\",\"role\":\"agent\",\"messageId\":\"m\",\"parts\":[{\"kind\":\"file\",\"file\":{\"bytes\":\"aGk=\",\"name\":\"f.txt\"}}]}"},
        {"EventKind", "plain text, not an event"},
        {"EventKind", "{\"kind\":\"other\"}"},
        {"EventKind", "{\"role\":\"agent\"}"},
        {"EventKind", "{\"kind\":\"message\",\"role\":\"agent\",\"parts\":[{\"kind\":\"text\",\"text\":\"x\"}]}"},
        {"EventKind", "{\"kind\":\"message\",\"role\":\"agent\",\"messageId\":\"m\",\"parts\":[]}"},
        {"EventKind", "{\"kind\":\"message\",\"role\":\"robot\",\"messageId\":\"m\",\"parts\":[{\"kind\":\"text\",\"text\":\"x\"}]}"},
        {"EventKind", "{\"kind\":\"message\",\"role\":\"agent\",\"messageId\":\"m\",\"parts\":[{\"kind\":\"text\"}]}"},
        {"EventKind", "{\"kind\":\"task\",\"id\":\"t\",\"status\":{\"state\":\"completed\"}}"},
        {"EventKind", "{\"kind\":\"task\",\"id\":\"t\",\"contextId\":\"c\",\"status\":{\"state\":\"bogus\"}}"},
        {"EventKind", "{\"kind\":\"task\",\"id\":\"t\",\"contextId\":\"c\",\"status\":{}}"},
        {"EventKind", "{\"kind\":\"message\",\"role\":\"agent\",\"messageId\":\"m\",\"parts\":[{\"kind\":\"text\",\"text\":\"\\\"q\\\" \\\\ \\n\\t/ é 日本\"}]}"},
        {"EventKind", "{\"kind\":\"message\",\"role\":\"agent\",\"messageId\":\"m\",\"parts\":[{\"kind\":\"text\",\"text\":\"x\"}],\"unknown\":1}"},
        {"EventKind", "[1,2]"},
        {"EventKind", "{\"kind\":\"message\""},
        {"EventKind", ""},
        {"Message", "{\"role\":\"user\",\"messageId\":\"m\",\"parts\":[{\"kind\":\"text\",\"text\":\"x\"}]}"},
        {"MessageSendParams", "{\"message\":{\"kind\":\"message\",\"role\":\"user\",\"messageId\":\"u-1\",\"parts\":[{\"kind\":\"text\",\"text\":\"hi\"}]}}"},
        {"MessageSendParams", "{\"message\":{\"role\":\"user\",\"messageId\":\"u\",\"parts\":[{\"text\":\"a\",\"kind\":\"text\"}]},\"configuration\":{\"acceptedOutputModes\":[\"text\"],\"historyLength\":3,\"blocking\":true,\"pushNotificationConfig\":{\"url\":\"http://h/p\",\"token\":\"tk\",\"authentication\":{\"schemes\":[\"Bearer\"],\"credentials\":\"c\"}}},\"metadata\":{\"m\":1}}"},
        {"MessageSendParams", "{}"},
        {"TaskStatus", "{\"state\":\"canceled\",\"message\":{\"kind\":\"message\",\"role\":\"agent\",\"messageId\":\"m\",\"parts\":[{\"kind\":\"text\",\"text\":\"x\"}]},\"timestamp\":\"2026-03-04T05:06:07.890123Z\"}"},
        {"TaskQueryParams", "{\"id\":\"t\"}"},
        {"TaskQueryParams", "{\"id\":\"t\",\"historyLength\":2,\"metadata\":{\"a\":1}}"},
        {"TaskIdParams", "{\"id\":\"t\"}"},
        {"TaskIdParams", "{}"},
        {"GetTaskPushNotificationConfigParams", "{\"x\":1,\"pushNotificationConfigId\":\"p\",\"metadata\":{\"k\":[1]},\"id\":\"t\"}"},
        {"GetTaskPushNotificationConfigParams", "{\"id\":\"t\"}"},
        {"GetTaskPushNotificationConfigParams", "{\"pushNotificationConfigId\":\"p\"}"},
        {"ListTaskPushNotificationConfigParams", "{\"metadata\":{},\"id\":\"t\"}"},
        {"ListTaskPushNotificationConfigParams", "{}"},
        {"DeleteTaskPushNotificationConfigParams", "{\"pushNotificationConfigId\":\"p\",\"id\":\"t\"}"},
        {"DeleteTaskPushNotificationConfigParams", "{\"id\":\"t\"}"},
        {"TaskPushNotificationConfig", "{\"pushNotificationConfig\":{\"id\":\"i\",\"token\":\"k\",\"url\":\"u\"},\"taskId\":\"t\"}"},
        {"StreamingEventKind", "{\"kind\":\"status-update\",\"taskId\":\"t\",\"contextId\":\"c\",\"status\":{\"state\":\"working\",\"timestamp\":\"2026-01-01T00:00:00Z\"},\"final\":false}"},
        {"StreamingEventKind", "{\"kind\":\"status-update\",\"taskId\":\"t\",\"contextId\":\"c\",\"status\":{\"state\":\"completed\",\"timestamp\":\"2026-01-01T00:00:00Z\"},\"final\":true,\"metadata\":{}}"},
        {"StreamingEventKind", "{\"kind\":\"artifact-update\",\"taskId\":\"t\",\"contextId\":\"c\",\"artifact\":{\"artifactId\":\"a\",\"name\":\"n\",\"description\":\"d\",\"parts\":[{\"kind\":\"text\",\"text\":\"x\"}]},\"append\":true,\"lastChunk\":false}"},
        {"StreamingEventKind", "{\"kind\":\"artifact-update\",\"taskId\":\"t\",\"contextId\":\"c\",\"artifact\":{\"artifactId\":\"a\",\"parts\":[{\"kind\":\"text\",\"text\":\"x\"}]}}"},
        {"TaskPushNotificationConfig", "{\"taskId\":\"t\",\"pushNotificationConfig\":{\"url\":\"http://h/p\",\"id\":\"i\"}}"},
        {"AgentCard", "{\"name\":\"Mulay Echo Agent\",\"description\":\"Echoes the text it receives.\",\"url\":\"http://localhost:18162/agent\",\"version\":\"1.0.0\",\"protocolVersion\":\"0.3.0\",\"capabilities\":{\"streaming\":false,\"pushNotifications\":false,\"stateTransitionHistory\":false},\"defaultInputModes\":[\"text/plain\"],\"defaultOutputModes\":[\"text/plain\"],\"skills\":[{\"id\":\"echo\",\"name\":\"Echo\",\"description\":\"Echoes text\",\"tags\":[\"echo\"]}],\"provider\":{\"organization\":\"mulay\",\"url\":\"https://example.com\"}}"},
        {"AgentCard", "{\"name\":\"n\",\"description\":\"d\",\"url\":\"u\",\"version\":\"1\",\"capabilities\":{},\"defaultInputModes\":[],\"defaultOutputModes\":[],\"skills\":[{\"id\":\"s\",\"name\":\"S\",\"description\":\"x\",\"tags\":[],\"examples\":[\"e\"],\"inputModes\":[\"a\"],\"outputModes\":[\"b\"]}],\"documentationUrl\":\"http://d\",\"iconUrl\":\"http://i\",\"additionalInterfaces\":[{\"transport\":\"JSONRPC\",\"url\":\"u\"}],\"supportsAuthenticatedExtendedCard\":true,\"preferredTransport\":\"HTTP+JSON\"}"},
        {"AgentCard", "{\"name\":\"n\",\"description\":\"d\",\"url\":\"u\",\"version\":\"1\",\"defaultInputModes\":[],\"defaultOutputModes\":[],\"skills\":[]}"},
        {"AgentCard", "{\"name\":\"n\",\"description\":\"d\",\"url\":\"u\",\"version\":\"1\",\"capabilities\":{\"streaming\":true,\"extensions\":[{\"uri\":\"x\",\"required\":true}]},\"defaultInputModes\":[],\"defaultOutputModes\":[],\"skills\":[]}"},
    };

    static String clayStr(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            switch (c) {
                case '"': b.append("\\\""); break;
                case '\\': b.append("\\\\"); break;
                case '\n': b.append("\\n"); break;
                case '\t': b.append("\\t"); break;
                case '\r': b.append("\\r"); break;
                default: b.append(c);
            }
        }
        return b.append('"').toString();
    }

    public static void main(String[] args) throws Exception {
        Path root = Paths.get(args.length > 0 ? args[0] : ".").toAbsolutePath().normalize();
        StringBuilder b = new StringBuilder();
        b.append("(ns a2a-spec-gold-test (:require [mulay.conn.a2a_spec :as spec]))\n\n");
        b.append(";; 生成物: tools/gen-a2a-golden.java (手で編集しない)。期待値は a2a-java-sdk 0.3.3 と Jackson 2.17.0 が\n");
        b.append(";; 読んで書き直した JSON、または読めないときの例外の文言 (\"ERR \" を前に付ける)。\n\n");
        b.append("(defn- run Str [t: Str j: Str] (let [[o e] (spec/canon t j \"<ts>\")] (if (= e \"\") o (str \"ERR \" e))))\n\n");
        b.append("(deftest sdk-canonical\n");
        for (String[] c : CASES) {
            String out;
            try {
                Object v = Utils.OBJECT_MAPPER.readValue(c[1], TYPES.get(c[0]));
                out = Utils.OBJECT_MAPPER.writeValueAsString(v);
                if (!c[1].contains("\"timestamp\"")) out = out.replaceAll("\"timestamp\":\"[^\"]*\"", "\"timestamp\":\"<ts>\"");
            } catch (Exception e) {
                out = "ERR " + e.getMessage();
            }
            b.append("  (is (= (run ").append(clayStr(c[0])).append(" ").append(clayStr(c[1])).append(")\n         ").append(clayStr(out)).append("))\n");
        }
        b.setLength(b.length() - 1);
        b.append(")\n");
        Files.write(root.resolve("test/a2a/a2a_spec_gold_test.clay"), b.toString().getBytes(StandardCharsets.UTF_8));
    }
}
