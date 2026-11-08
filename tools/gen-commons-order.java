// Prints the expectations of test/schema/commons_order_test.clay: the iteration order of commons-collections4 4.4
// CaseInsensitiveMap (AbstractHashedMap) after putting the keys in order (mulay.lib.jhash/commons-order).
// The SOAP engine of the Web Service Consumer keeps the HTTP request headers in this map.
// Run: /usr/lib/jvm/java-17-openjdk-amd64/bin/java -cp ~/.m2/repository/org/apache/commons/commons-collections4/4.4/commons-collections4-4.4.jar tools/gen-commons-order.java
import java.util.*;
import org.apache.commons.collections4.map.CaseInsensitiveMap;

public class GenCommonsOrder {
    public static void main(String[] a) {
        String[][] sets = {
            {"content-type", "soapaction"},
            {"content-type", "soapaction", "x-static", "soapaction"},
            {"content-type", "soapaction", "x-expr", "content-type"},
            {"Content-Type", "SOAPAction", "X-Static"},
            {"a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r"},
            {"authorization", "x-correlation-id", "accept-language", "cache-control", "x-api-key", "cookie", "if-none-match",
             "user-agent", "x-forwarded-for", "origin", "referer", "content-length", "x-request-id", "pragma"},
        };
        for (String[] s : sets) {
            CaseInsensitiveMap<String, String> m = new CaseInsensitiveMap<>();
            for (String k : s) m.put(k, "v");
            StringBuilder in = new StringBuilder(), out = new StringBuilder();
            for (String k : s) in.append(" \"").append(k).append("\"");
            for (String k : m.keySet()) out.append(" \"").append(k).append("\"");
            System.out.println("  (is (= (jh/commons-order [" + in.toString().trim() + "]) [" + out.toString().trim() + "]))");
        }
    }
}
