// Generates test/validate/golden_test.clay: the libraries behind the Validation module (mule-validation-module 2.0.11)
// that mulay.lib.validate must reproduce:
//   email  commons-validator 1.10.1 EmailValidator.getInstance().isValid (is-email、Validation::isEmail)
//   inet   Guava 33.6.0 InetAddresses.isInetAddress (is-ip、Validation::isIp)
//   url    new java.net.URL(s) succeeds (is-url、Validation::isUrl)
// Run:
//   CP=~/.m2/repository/commons-validator/commons-validator/1.10.1/commons-validator-1.10.1.jar:~/.m2/repository/com/google/guava/guava/33.6.0-jre/guava-33.6.0-jre.jar
//   /usr/lib/jvm/java-17-openjdk-amd64/bin/java -cp "$CP" tools/gen-validation-golden.java > test/validate/golden_test.clay
import java.nio.charset.StandardCharsets;
import java.util.*;

public class GenValidationGolden {
    static String hex(String s) {
        StringBuilder b = new StringBuilder();
        for (byte x : s.getBytes(StandardCharsets.UTF_8)) b.append(String.format("%02x", x & 0xff));
        return b.toString();
    }
    static String show(String s) {
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c < 32 || c == 127) b.append(String.format("\\x%02x", (int) c)); else b.append(c);
        }
        return b.toString();
    }

    static final String[] EMAILS = {
        "a@b.com", "a@b", "not-an-email", "a.b@c.co.jp", "user+tag@example.org", "a@localhost", "", "a@@b.com",
        "x@[127.0.0.1]", ".a@b.com", "a@b.c", "a b@c.com", "a@b.com.", "\"a\"@b.com", "\"a b\"@b.com", "a\\@b@c.com",
        "a..b@c.com", "a.@b.com", "a@b..com", "a@-b.com", "a@b-.com", "a@b.co", "a@B.COM", "A@B.Com", "a@b.xn--p1ai",
        "a@b.local", "a@b.123", "a@1.2.3.4", "a@[::1]", "a@[1.2.3]", "a@[256.1.1.1]", "a@[01.2.3.4]", "a@[::ffff:1.2.3.4]",
        "a@[fe80::1%eth0]", "a@[1:2:3:4:5:6:7:8]", "a@[1:2:3:4:5:6:7:8:9]", "a@[1::2::3]", "a@[::]", "a@[]",
        "a@b.museum", "a@b.photography", "a@b.example", "a@b.test", "a@b.invalid", "a@b.arpa", "a@b.onion",
        "a\t@b.com", " a@b.com", "a@b.com ", "a@b.com\n", "ü@b.com", "a@ü.com", "a@b.ü", "a@例え.jp",
        "a'b@c.com", "a!#$%&*+/=?^_`{|}~-@b.com", "a(b)@c.com", "a<b@c.com", "a,b@c.com", "a;b@c.com", "a:b@c.com",
        "a[b]@c.com", "\"\"@b.com", "\"a\\\"b\"@c.com", "\"a\".b@c.com", "a.\"b\"@c.com", "\\a@b.com", "a\\ b@c.com",
        "a@b_c.com", "a@b.c_m", "a@1b.com", "a@b1.com", "a@b.c1m", "a@b.1com", "a@xn--bcher-kva.com",
        "a@" + "x".repeat(63) + ".com", "a@" + "x".repeat(64) + ".com", "u".repeat(64) + "@b.com", "u".repeat(65) + "@b.com",
        "a@" + ("x".repeat(61) + ".").repeat(4) + "com", "a@" + ("x".repeat(62) + ".").repeat(4) + "com",
        "a@b.com.au", "a@sub.domain.example.co.uk", "a@b.c.d.e.f.org", "a@.b.com", "a@b.com..", "@b.com", "a@",
        "a@b@c.com", "a@b. com", "a@b,com", "a@b;com", "a@-.com", "a@a-b.com", "a@a--b.com", "a@b.co-m",
        "a@b.xn--", "a@b.amazon", "a@b.google", "a@b.zz", "a@b.uk", "a@b.su", "a@b.yu", "a@b.example.com",
        "\u0001@b.com", "a@b\u0001.com", "a\u007f@b.com", "a@b.com\u0000",
    };
    static final String[] IPS = {
        "10.0.0.1", "256.1.1.1", "::1", "2001:db8::1", "abc", "1.2.3", "01.2.3.4", "1.2.3.4.5", "::ffff:1.2.3.4",
        "fe80::1%eth0", "0.0.0.0", "255.255.255.255", "1.2.3.04", "1.2.3.", ".1.2.3", "1..2.3", "1.2.3.4 ", " 1.2.3.4",
        "1.2.3.4%eth0", "::", ":", ":::", "1::", "::1::", "1:2:3:4:5:6:7:8", "1:2:3:4:5:6:7:8:9", "1:2:3:4:5:6:7::",
        "::2:3:4:5:6:7:8", "1:2:3:4:5:6:7", "12345::1", "abcd:ef01:2345:6789:abcd:ef01:2345:6789", "ABCD::EF",
        "g::1", "1:2:3:4:5:6:1.2.3.4", "1:2:3:4:5:6:7:1.2.3.4", "::1.2.3.4", "::256.1.1.1", "1.2.3.4::",
        "fe80::1%", "fe80::1%1", "fe80::1%eth0%1", "fe80::1%eth 0", "::ffff:1.2.3.4%eth0", "1:2::3:4:5:6:7:8",
        "1:2::3:4:5:6:7", ":1:2:3:4:5:6:7", "1:2:3:4:5:6:7:", "1::2:", ":1::2", "0:0:0:0:0:0:0:0", "00000::1",
        "0000::1", "1.2.3.4/24", "::1/128", "", "1", "+1.2.3.4", "1.2.3.-4", "１.２.３.４", "١.٢.٣.٤", "1.2.3.4\n",
        "::ffff:01.2.3.4", "1.2.3.256", "999.1.1.1", "1:2:3:4:5:6:7:8%x", "[::1]",
    };
    static final String[] URLS = {
        "http://x.com", "https://example.com/path?q=1", "ftp://f.org", "example.com", "http://", "mailto:a@b.com",
        "file:///tmp/x", "http://localhost:8081/a", "http://a b.com", "x:y", "HTTP://X.COM", "Http://x.com",
        "http:", "http:x", "http:/x", "https:", "file:", "file:x", "jar:file:/x!/y", "jar:file:/x", "jar:", "jrt:/java.base",
        "jmod:x", "netdoc:x", "mailto:", "mailto:x#y", "ftp:", "classpath:x", "mvn:x", "data:text/plain,hi", "urn:isbn:1",
        "http://x.com:80", "http://x.com:abc", "http://x.com:-1", "http://x.com:-5", "http://x.com:99999", "http://x.com:",
        "http://[::1]/", "http://[::1", "http://[zz]/", "http://[::1]:8080/", "http://user:pw@x.com/", "http://x.com/#frag",
        "http://x.com/a b", "http://x.com/%zz", "http://x.com/\u00fc", "  http://x.com  ", "url:http://x.com", "URL:http://x.com",
        "#x", "/x", "//x.com", "", " ", "1http://x", "h-t.t+p://x", "h_t://x", ":x", "http//x.com", "http:\\\\x.com",
        "file:C:\\x", "https://x.com?a=1&b=2", "http://x.com:8080:90/", "http://@x.com", "http://x.com\n",
        "ftp://user@f.org:21/a;type=i", "file://host/share", "http://[::1]x/", "http://1.2.3.4/", "jar:http://x/y.jar!/a",
    };

    static boolean url(String s) {
        try { new java.net.URL(s); return true; } catch (java.net.MalformedURLException e) { return false; }
    }

    public static void main(String[] args) {
        org.apache.commons.validator.routines.EmailValidator ev = org.apache.commons.validator.routines.EmailValidator.getInstance();
        StringBuilder out = new StringBuilder();
        out.append("(ns validate-golden-test (:require [validate-golden-helper :as h]))\n");
        out.append(";; GENERATED by tools/gen-validation-golden.java on Java " + System.getProperty("java.version")
                   + " (commons-validator 1.10.1, guava 33.6.0) -- do not edit.\n");
        out.append(";; (h/check kind hex) は lib/validate の判定 (\"t\" か \"f\")。\n");
        String[][] groups = {EMAILS, IPS, URLS};
        String[] kinds = {"email", "inet", "url"};
        for (int g = 0; g < groups.length; g++) {
            out.append("(deftest golden-" + kinds[g] + "\n");
            for (String s : groups[g]) {
                boolean r = g == 0 ? ev.isValid(s) : g == 1 ? com.google.common.net.InetAddresses.isInetAddress(s) : url(s);
                out.append("  ;; " + show(s) + "\n");
                out.append("  (is (= (h/check \"" + kinds[g] + "\" \"" + hex(s) + "\") \"" + (r ? "t" : "f") + "\"))\n");
            }
            out.append(")\n");
        }
        System.out.print(out);
    }
}
