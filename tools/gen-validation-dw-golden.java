// Generates test/validation/golden_test.clay: what mulay.dw.lib.validation must reproduce for the Validation module
// (mule-validation-module 2.0.11) in a Mule JVM (-Djava.locale.providers=COMPAT,CLDR,SPI, default locale en):
//   number  commons-validator 1.10.1 Integer/Long/Short/Double/FloatValidator.validate(v, pattern, new Locale(l))
//           (is-number、Validation::isNumber)。結果は null か "型:MessageFormat の {0}" (文言に出る形)
//   time    DateTimeFormatter.ofPattern(p).withLocale(new Locale(l)).parse(t) (is-time、Validation::isTime)
//   int     MessageFormat.format("{0}", Integer) (validate-size の文言の大きさ)
// Run:
//   CV=~/.m2/repository/commons-validator/commons-validator/1.10.1/commons-validator-1.10.1.jar
//   /usr/lib/jvm/java-17-openjdk-amd64/bin/java -Djava.locale.providers=COMPAT,CLDR,SPI -Duser.language=en -Duser.country=US \
//     -cp "$CV" tools/gen-validation-dw-golden.java > test/validation/golden_test.clay
import java.nio.charset.StandardCharsets;
import java.text.MessageFormat;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.*;
import org.apache.commons.validator.routines.*;

public class GenValidationDwGolden {
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
    static String esc(String s) { return s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n"); }

    // type value pattern locale (pattern "" は無し、locale "" は既定 = en)
    static final String[][] NUMBERS = {
        {"INTEGER", "42", "", ""}, {"INTEGER", "4.5", "", ""}, {"INTEGER", "abc", "", ""}, {"INTEGER", "99999999999", "", ""},
        {"INTEGER", "1,234", "#,##0", "en"}, {"INTEGER", "-7", "", ""}, {"INTEGER", "+7", "", ""}, {"INTEGER", " 42", "", ""},
        {"INTEGER", "42 ", "", ""}, {"INTEGER", "42abc", "", ""}, {"INTEGER", "", "", ""}, {"INTEGER", "1,234", "", ""},
        {"INTEGER", "1234567", "", ""}, {"INTEGER", "12,34", "", ""}, {"INTEGER", "1,2,3", "", ""}, {"INTEGER", ",123", "", ""},
        {"INTEGER", "123,", "", ""}, {"INTEGER", "2147483647", "", ""}, {"INTEGER", "2147483648", "", ""}, {"INTEGER", "-2147483648", "", ""},
        {"INTEGER", "-0", "", ""}, {"INTEGER", "0", "", ""}, {"INTEGER", "007", "", ""}, {"INTEGER", "1E3", "", ""}, {"INTEGER", "1.0", "", ""},
        {"INTEGER", "١٢٣", "", ""}, {"INTEGER", "1.234", "", "de"}, {"INTEGER", "1,234", "", "de"}, {"INTEGER", "1 234", "", "fr"},
        {"INTEGER", "1 234", "", "fr"}, {"INTEGER", "50%", "#%", ""}, {"INTEGER", "(5)", "#;(#)", ""}, {"INTEGER", "12", "00", ""},
        {"INTEGER", "\t42\n", "", ""}, {"INTEGER", "x", "#,##0", ""}, {"INTEGER", "1.5", "#.#", ""},
        {"LONG", "99999999999", "", ""}, {"LONG", "9223372036854775807", "", ""}, {"LONG", "9223372036854775808", "", ""},
        {"LONG", "-9223372036854775808", "", ""}, {"LONG", "-9223372036854775809", "", ""}, {"LONG", "-0", "", ""}, {"LONG", "1.0", "", ""},
        {"LONG", "1,000,000", "", ""}, {"LONG", "12.5", "", ""},
        {"SHORT", "123", "", ""}, {"SHORT", "40000", "", ""}, {"SHORT", "-32768", "", ""}, {"SHORT", "32767", "", ""}, {"SHORT", "32768", "", ""},
        {"SHORT", "-32769", "", ""}, {"SHORT", "1,000", "", ""},
        {"DOUBLE", "3.14", "", ""}, {"DOUBLE", "1e3", "", ""}, {"DOUBLE", "1E3", "", ""}, {"DOUBLE", "abc", "", ""}, {"DOUBLE", "1,5", "", "de"},
        {"DOUBLE", "1.0", "", ""}, {"DOUBLE", "1.5", "", ""}, {"DOUBLE", "2.5", "", ""}, {"DOUBLE", "2.4", "", ""}, {"DOUBLE", "NaN", "", ""},
        {"DOUBLE", "�", "", ""}, {"DOUBLE", "∞", "", ""}, {"DOUBLE", "-∞", "", ""}, {"DOUBLE", ".5", "", ""}, {"DOUBLE", "1.", "", ""},
        {"DOUBLE", "1,000.5", "", ""}, {"DOUBLE", "-0", "", ""}, {"DOUBLE", "-0.0", "", ""}, {"DOUBLE", "1.23456", "", ""}, {"DOUBLE", "1.2345", "", ""},
        {"DOUBLE", "1.2355", "", ""}, {"DOUBLE", "0.0005", "", ""}, {"DOUBLE", "123456789.987", "", ""}, {"DOUBLE", "99999999999999999999", "", ""},
        {"DOUBLE", "1.2E-5", "", ""}, {"DOUBLE", "1.2.3", "", ""}, {"DOUBLE", "1,234.5", "", "de"}, {"DOUBLE", "1.234,5", "", "de"},
        {"DOUBLE", "1.234,5", "#,##0.0", "de"}, {"DOUBLE", "3,5", "#,##0.0", "fr"}, {"DOUBLE", "1.2E3", "0.###E0", ""}, {"DOUBLE", "12%", "#%", ""},
        {"DOUBLE", "0.1", "", ""}, {"DOUBLE", "100", "", ""},
        {"FLOAT", "3.4e39", "", ""}, {"FLOAT", "3.4E39", "", ""}, {"FLOAT", "1.5", "", ""}, {"FLOAT", "1e-50", "", ""}, {"FLOAT", "1E-50", "", ""},
        {"FLOAT", "0", "", ""}, {"FLOAT", "-0", "", ""}, {"FLOAT", "1E-45", "", ""}, {"FLOAT", "-2.5", "", ""}, {"FLOAT", "3.4028235E38", "", ""},
        {"FLOAT", "3.4028236E38", "", ""},
    };
    // value pattern locale ("" の locale は既定 = en)
    static final String[][] TIMES = {
        {"2024-01-15", "yyyy-MM-dd", ""}, {"2024-13-45", "yyyy-MM-dd", ""}, {"15/01/2024", "yyyy-MM-dd", ""}, {"Jan 15, 2024", "MMM dd, yyyy", "en"},
        {"2024-01-15xyz", "yyyy-MM-dd", ""}, {"abc", "[", ""}, {"", "[", ""}, {"2023-02-30", "yyyy-MM-dd", ""}, {"2024-02-29", "yyyy-MM-dd", ""},
        {"2023-02-29", "yyyy-MM-dd", ""}, {"2023-04-31", "yyyy-MM-dd", ""}, {"2023-02-32", "yyyy-MM-dd", ""}, {"10:30", "HH:mm", ""}, {"25:00", "HH:mm", ""},
        {"24:00", "HH:mm", ""}, {"10:30 PM", "hh:mm a", "en"}, {"10:30", "hh:mm", ""}, {"15 janvier 2024", "dd MMMM yyyy", "fr"},
        {"15. Januar 2024", "dd. MMMM yyyy", "de"}, {"Mon, 15 Jan 2024", "EEE, dd MMM yyyy", "en"}, {"Tue, 15 Jan 2024", "EEE, dd MMM yyyy", "en"},
        {"2024-01-15T10:00:00", "yyyy-MM-dd'T'HH:mm:ss", ""}, {"2024-01-15T10:00:00Z", "yyyy-MM-dd'T'HH:mm:ssX", ""}, {"2024-01-15", "yyyy-MM-ddb", ""},
        {"2024-01-15", "yyyy-MM-dd'", ""}, {"2024-01-15", "{yyyy}", ""}, {"1/15/24", "M/d/yy", ""}, {"2024", "yyyy", ""}, {"20240115", "yyyyMMdd", ""},
        {"2024-1-5", "yyyy-M-d", ""}, {"2024-01-05", "yyyy-M-d", ""}, {"JAN 15, 2024", "MMM dd, yyyy", "en"}, {"15 Jan 2024", "dd MMM yyyy", "ja"},
        {"2024-01-15 ", "yyyy-MM-dd", ""}, {"2024-01-15", "uuuu-MM-dd", ""}, {"0000-01-15", "yyyy-MM-dd", ""}, {"0000-01-15", "uuuu-MM-dd", ""},
    };
    static final int[] INTS = {0, 1, 5, 999, 1000, 1234567, 150};

    static Number num(String type, String v, String p, Locale l) {
        String pat = p.isEmpty() ? null : p;
        switch (type) {
            case "INTEGER": return pat != null ? IntegerValidator.getInstance().validate(v, pat, l) : IntegerValidator.getInstance().validate(v, l);
            case "LONG": return pat != null ? LongValidator.getInstance().validate(v, pat, l) : LongValidator.getInstance().validate(v, l);
            case "SHORT": return pat != null ? ShortValidator.getInstance().validate(v, pat, l) : ShortValidator.getInstance().validate(v, l);
            case "DOUBLE": return pat != null ? DoubleValidator.getInstance().validate(v, pat, l) : DoubleValidator.getInstance().validate(v, l);
            default: return pat != null ? FloatValidator.getInstance().validate(v, pat, l) : FloatValidator.getInstance().validate(v, l);
        }
    }

    public static void main(String[] args) {
        StringBuilder out = new StringBuilder();
        out.append("(ns validation-golden-test (:require [validation-golden-helper :as h]))\n");
        out.append(";; GENERATED by tools/gen-validation-dw-golden.java on Java " + System.getProperty("java.version")
                   + " (commons-validator 1.10.1, java.locale.providers=COMPAT,CLDR,SPI) -- do not edit.\n");
        out.append("(deftest golden-number\n");
        for (String[] c : NUMBERS) {
            Locale l = new Locale(c[3].isBlank() ? "en" : c[3]);
            Number n = num(c[0], c[1], c[2], l);
            String r = n == null ? "N" : n.getClass().getSimpleName() + ":" + MessageFormat.format("{0}", n);
            out.append("  ;; " + c[0] + " " + show(c[1]) + " " + c[2] + " " + c[3] + "\n");
            out.append("  (is (= (h/number \"" + c[0] + "\" \"" + hex(c[1]) + "\" \"" + hex(c[2]) + "\" \"" + c[3] + "\") \"" + esc(r) + "\"))\n");
        }
        out.append(")\n(deftest golden-time\n");
        for (String[] c : TIMES) {
            String r;
            try {
                DateTimeFormatter.ofPattern(c[1]).withLocale(new Locale(c[2].isEmpty() ? "en" : c[2])).parse(c[0]);
                r = "ok";
            } catch (DateTimeParseException e) {
                r = "fail";
            } catch (IllegalArgumentException e) {
                r = "err:" + e.getMessage();
            }
            out.append("  ;; " + show(c[0]) + " | " + c[1] + " | " + c[2] + "\n");
            out.append("  (is (= (h/time \"" + hex(c[0]) + "\" \"" + hex(c[1]) + "\" \"" + c[2] + "\") \"" + esc(r) + "\"))\n");
        }
        out.append(")\n(deftest golden-int-format\n");
        for (int n : INTS) out.append("  (is (= (h/int-format " + n + ") \"" + MessageFormat.format("{0}", Integer.valueOf(n)) + "\"))\n");
        out.append(")\n");
        System.out.print(out);
    }
}
