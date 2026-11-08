// mulay.dw.numfmt の golden テストの期待値を Java 17 の DecimalFormat で作る。
//
//   /usr/lib/jvm/java-17-openjdk-amd64/bin/java test/lib-num/gen-numfmt-golden.java > test/lib-num/numfmt_golden_data.clay
//
// 実 DW 2.11.2 が動く Java 17 (ロケールデータは CLDR) を使うこと。乱数の種は固定。
// 出力は Clay のモジュール (ns numfmt-golden-data)。1 行 = タブ区切り:
//   F <pattern> <locale> <mode> <number> <期待>    書式化。期待は結果か "ERRP:<文言>" (パターン) / "ERRA:<文言>" (丸め)
//   P <pattern> <locale> - <text> <期待>           解析。期待は BigDecimal.toString か "FAIL" か "ERRP:<文言>"
// locale が "-" なら既定 (en-US)。mode は java.math.RoundingMode の ordinal。

import java.math.*;
import java.text.*;
import java.util.*;

public class GenNumfmtGolden {
    static final Random R = new Random(20260928L);
    static final StringBuilder F = new StringBuilder();
    static final StringBuilder P = new StringBuilder();

    static Locale loc(String l) { return l.equals("-") ? Locale.US : Locale.forLanguageTag(l); }

    static DecimalFormat mk(String pattern, String l, RoundingMode m) {
        DecimalFormat f = new DecimalFormat(pattern, DecimalFormatSymbols.getInstance(loc(l)));
        f.setRoundingMode(m);
        f.setParseBigDecimal(true);
        return f;
    }

    static void fmt(String pattern, String l, int mode, String num) {
        String out;
        try {
            DecimalFormat f = mk(pattern, l, RoundingMode.values()[mode]);
            try { out = f.format(new BigDecimal(num)); }
            catch (ArithmeticException e) { out = "ERRA:" + e.getMessage(); }
        } catch (IllegalArgumentException e) { out = "ERRP:" + e.getMessage(); }
        F.append("F\t").append(pattern).append('\t').append(l).append('\t').append(mode).append('\t').append(num).append('\t').append(out).append('\n');
    }

    static void parse(String pattern, String l, String text) {
        String out;
        try {
            DecimalFormat f = mk(pattern, l, RoundingMode.HALF_UP);
            ParsePosition pp = new ParsePosition(0);
            Number n = f.parse(text, pp);
            if (n == null || pp.getIndex() == 0) out = "FAIL";
            else if (n instanceof BigDecimal) out = n.toString();
            else out = "FAIL";   // NaN / 無限大 (Double)
        } catch (IllegalArgumentException e) { out = "ERRP:" + e.getMessage(); }
        P.append("P\t").append(pattern).append('\t').append(l).append("\t-\t").append(text).append('\t').append(out).append('\n');
    }

    static final String[] PATTERNS = {
        "#,##0.00", "#,##0.###", "0.00", "#", "#.#", "#.##", "0", "000", "00.000", "#,###", "#,##,###", "#,##0",
        "0.###E0", "##0.##E0", "00.###E0", "##0.#####E0", "0.0E00", "#E0", "0E0", "0.E0", "##E0", "###.##E0", "0.00E0",
        "#%", "0.0%", "#‰", "0.00‰", "'#'#", "'x''y'0.0", "''#", "#;(#)", "#,##0.00;(#,##0.00)", "0.0;-0.0",
        "#,##0.00;-#,##0.00", "¤#,##0.00", "¤¤ #,##0.00", "#,##0.00 ¤", "abc", "", "1", "#.", "0.", ".0", ".##",
        "#,##0.0#", "#0.0#", "##00.00##", "-#", "#-", "%#", "#,##0.00%;(#,##0.00%)", "0.00 'kg'", "'%'#", "#'%'",
        "#,##0.###;#", "#a#", "0.0#E0", "0,000", "#,##0.00;#", "#;#", "#;-#", "#;", "#,##0.##;(#)", "# 'items'",
        "0.00000000000000000000000000", "#,##0.0000000000", "#.###############",
        // 不正なパターン
        "00.00.00", "0#", "#,##0.0#0", "#,", "#E", "0.0E", "E0", ";#", "#;#;#", "'abc", "#%%", "#%‰", "0E0E0", "#.#E0.0",
        "#,##0.00;(#.##.#)", "0.#0",
    };

    static final String[] NUMBERS = {
        "0", "1", "-1", "0.5", "-0.5", "1.5", "2.5", "-2.5", "0.125", "0.135", "2.345", "-2.345", "1234", "-1234",
        "1234.5", "1234.5678", "1234567.891", "-1234567.891", "0.001", "-0.001", "0.0009", "0.0005", "0.00049",
        "999.995", "9.9999", "99999", "0.9999", "1E+10", "1.23E-7", "12345678901234567890.123456789",
        "123456789012345678901234567890", "0.00", "100", "1000000", "0.1", "0.01", "5E-11", "-0.0000001",
        "9223372036854775807", "-9223372036854775808", "3.14159265358979323846", "1E+400", "1E-400", "0.999",
        "12.5", "13.5", "-12.5", "0.045", "0.055", "7", "-7", "10", "1.0000001",
    };

    static final String[] LOCALES = { "-", "de", "fr-FR", "de-CH", "sv", "ar", "fa", "ja-JP", "hi-IN", "und", "en", "es", "it", "pt-BR", "ru", "zh-CN", "en-IN", "de_DE", "xx", "EN-us" };

    static String randNum() {
        int k = R.nextInt(10);
        StringBuilder b = new StringBuilder();
        if (R.nextInt(3) == 0) b.append('-');
        int nd = k < 5 ? 1 + R.nextInt(6) : 1 + R.nextInt(25);
        for (int i = 0; i < nd; i++) b.append((char) ('0' + R.nextInt(10)));
        String digits = b.toString();
        BigDecimal x = new BigDecimal(new BigInteger(digits), R.nextInt(20) - 6);
        return x.toString();
    }

    static String pick(String... xs) { return xs[R.nextInt(xs.length)]; }

    static String randPattern() {
        StringBuilder b = new StringBuilder();
        b.append(pick("", "", "", "$", "'#'", "a", "%", "‰", "¤", "¤¤", "-", "''", "'x''y'", "(", " "));
        int nh = R.nextInt(4), nz = R.nextInt(4);
        boolean group = R.nextInt(3) == 0;
        String ip = "#".repeat(nh) + "0".repeat(nz);
        if (group && ip.length() > 1) { int g = 1 + R.nextInt(ip.length() - 1); ip = ip.substring(0, g) + "," + ip.substring(g); }
        if (group && ip.length() > 3 && R.nextBoolean()) { ip = ip.substring(0, 1) + "," + ip.substring(1); }
        b.append(ip);
        if (R.nextInt(3) > 0) { b.append('.'); b.append("0".repeat(R.nextInt(4))); b.append("#".repeat(R.nextInt(4))); }
        if (R.nextInt(5) == 0) { b.append('E'); b.append("0".repeat(R.nextInt(3))); }
        b.append(pick("", "", "", "%", "‰", " ¤", "'x'", " kg", ")", "-"));
        if (R.nextInt(5) == 0) b.append(';').append(pick("(", "-", "", "'neg'")).append("#").append(pick(")", "", "-"));
        return b.toString();
    }

    static String esc(String s) { return s.replace("\\", "\\\\").replace("\"", "\\\""); }

    public static void main(String[] a) {
        // 1. 固定のパターン × 固定の数 (en-US、HALF_UP / HALF_EVEN)
        for (String p : PATTERNS) for (String n : NUMBERS) { fmt(p, "-", 4, n); }
        for (String p : PATTERNS) for (String n : NUMBERS) { if (R.nextInt(3) == 0) fmt(p, "-", 6, n); }
        // 2. 丸めモード
        String[] mp = { "0.00", "#", "0.#", "#,##0.0", "0.00E0", "##0.#E0", "0%" };
        String[] mn = { "2.345", "-2.345", "2.355", "-2.355", "0.0005", "0.0009", "-0.0009", "0.001", "1.005", "15", "25", "-25", "0.5", "1.5", "0.04", "123.456", "99.999", "0" };
        for (int m = 0; m < 8; m++) for (String p : mp) for (String n : mn) fmt(p, "-", m, n);
        // 3. ロケール
        String[] lp = { "#,##0.00", "0.###E0", "#%", "¤#,##0.00", "¤¤#,##0.00", "#,##0.00;(#,##0.00)", "#‰", "0.00", "" };
        String[] ln = { "1234567.891", "-1234.5", "0.5", "0", "-0.001", "1E+10" };
        for (String l : LOCALES) for (String p : lp) for (String n : ln) fmt(p, l, 4, n);
        // 4. 乱数のパターンと数
        for (int i = 0; i < 400; i++) {
            String p = randPattern();
            for (int k = 0; k < 8; k++) fmt(p, "-", R.nextInt(3) == 0 ? R.nextInt(7) : 4, randNum());
        }
        // 5. 解析
        String[][] pc = {
            { "#,##0.##", "1,234.5" }, { "#,##0.##", "1,234.567" }, { "#", "12abc" }, { "#", "abc" }, { "#", "" }, { "#%", "50%" }, { "#%", "50" },
            { "#;(#)", "(12)" }, { "#;(#)", "-12" }, { "#", "-12" }, { "0.#E0", "1.2E3" }, { "#", "1.2E3" }, { "#", "1.2E-3" }, { "#", "1.2E+3" },
            { "#,##0", "1,2,3,4" }, { "#", "  12" }, { "#", "12 " }, { "", "1234.5" }, { "", "1,234.5" }, { "0.00", "0.10" }, { "0.00", "100" },
            { "#", "1e400" }, { "#", "+12" }, { "#", "12.50" }, { "#", ".5" }, { "#", "-0" }, { "#", "-0.0" }, { "#", "123456789012345678901234567890" },
            { "#", "1.2.3" }, { "#", "12E" }, { "#", "1,234" }, { "#", "NaN" }, { "#", "∞" }, { "#", "-∞" }, { "#‰", "500‰" },
            { "#,##0.00;(#,##0.00)", "(1,234.50)" }, { "#,##0.00;(#,##0.00)", "(1,234.50" }, { "'#'#", "#12" }, { "'#'#", "12" },
            { "¤#,##0.00", "$1,234.50" }, { "¤¤#,##0.00", "USD1,234.50" }, { "#", "0012" }, { "#", "0.000" }, { "#", "000.00100" },
            { "#", "١٢" }, { "#", "１２" }, { "#,##0", "1,,234" }, { "#,##0", "1,234," }, { "#,##0", ",234" }, { "#", "1E10000000000" },
            { "#", "1E-5" }, { "#", "1E05" }, { "#", "12-" }, { "#-", "12-" }, { "#;#-", "12-" }, { "0.00", "3.14159" }, { "#,##0.00", "1.234,5" },
            { "00.###E0", "12.5E-3" }, { "#", "9999999999999999999999.9999999999999" }, { "#E0", "5" }, { "#%", "12.5%" }, { "#%", "1%" }, { "#%", "0.3%" },
            { "#", "1.2E3x" }, { "#", "E3" }, { "#", "." }, { "#", "-" }, { "#", "-.5" }, { "0.#", "1.2E" }, { "00.00.00", "1" },
        };
        for (String[] c : pc) parse(c[0], "-", c[1]);
        String[][] lpc = { { "de", "1.234,5" }, { "de", "1,234.5" }, { "fr-FR", "1 234,5" }, { "fr-FR", "1 234,5" }, { "de-CH", "1’234.5" },
            { "sv", "−1 234,5" }, { "sv", "-1234,5" }, { "ar", "١٢٫٥" }, { "ar", "12.5" }, { "fa", "۱۲" }, { "en", "1,234.5" }, { "und", "1,234.5" } };
        for (String[] c : lpc) parse("#,##0.##", c[0], c[1]);
        // 書式化の結果を解析し直す (往復)
        for (int i = 0; i < 300; i++) {
            String p = randPattern();
            String n = randNum();
            try {
                String s = mk(p, "-", RoundingMode.HALF_UP).format(new BigDecimal(n));
                parse(p, "-", s);
            } catch (Exception e) { }
        }
        System.out.println(";; 生成物: test/lib-num/gen-numfmt-golden.java が作る。手で編集しない。");
        System.out.println(";; JDK: " + System.getProperty("java.version"));
        System.out.println("(ns numfmt-golden-data)");
        System.out.println();
        System.out.println("(defn format-cases Str []\n  \"" + esc(F.toString().stripTrailing()) + "\")");
        System.out.println();
        System.out.println("(defn parse-cases Str []\n  \"" + esc(P.toString().stripTrailing()) + "\")");
    }
}
