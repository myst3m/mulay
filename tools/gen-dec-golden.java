// mulay.lib.bigint / mulay.lib.dec の golden テストの期待値を Java で作る。
//
//   /usr/lib/jvm/java-21-openjdk-amd64/bin/java tools/gen-dec-golden.java > test/dec/golden_data.clay
//
// Java 19 以降が必要 (Double.toString が最短表現になったのは JDK 19。Java 17 の結果は一部違う)。
// 乱数の種は固定なので、同じ JDK なら同じファイルになる。
//
// 出力は Clay のモジュール (ns dec-golden-data) で、区分ごとに 1 つの関数が
// タブ区切りの行を返す。1 行 = 演算名 入力... 期待値。失敗が期待される場合の期待値は "ERR"。
// 丸めモードは java.math.RoundingMode の ordinal (mulay.lib.dec の定数と同じ値)。

import java.math.*;
import java.util.*;

public class GenDecGolden {
    static final Random R = new Random(20260928L);
    static final RoundingMode[] MODES = RoundingMode.values();

    static String digits(int n) {
        StringBuilder b = new StringBuilder();
        b.append((char) ('1' + R.nextInt(9)));
        for (int i = 1; i < n; i++) b.append((char) ('0' + R.nextInt(10)));
        return b.toString();
    }

    // 桁数の分布: 小さい数を多めに、ときどき巨大な数
    static int ndig() {
        int k = R.nextInt(10);
        if (k < 4) return 1 + R.nextInt(4);
        if (k < 7) return 1 + R.nextInt(20);
        if (k < 9) return 1 + R.nextInt(60);
        return 100 + R.nextInt(250);
    }

    static BigInteger bigint() {
        if (R.nextInt(12) == 0) return BigInteger.ZERO;
        BigInteger x = new BigInteger(digits(ndig()));
        // 基数 10^9 の境界付近 (999999999、1000000000 など) を混ぜる
        if (R.nextInt(8) == 0) x = BigInteger.TEN.pow(9 * (1 + R.nextInt(4))).add(BigInteger.valueOf(R.nextInt(3) - 1));
        return R.nextBoolean() ? x.negate() : x;
    }

    static BigDecimal dec() {
        BigInteger u = bigint();
        int k = R.nextInt(10);
        int scale = k < 6 ? R.nextInt(8) : (k < 8 ? R.nextInt(40) - 20 : R.nextInt(200) - 100);
        // 末尾に 0 を持つ unscaled も作る (strip / preferred scale の検査用)
        if (R.nextInt(5) == 0) u = u.multiply(BigInteger.TEN.pow(1 + R.nextInt(5)));
        return new BigDecimal(u, scale);
    }

    static BigDecimal smallDec() {
        BigInteger u = BigInteger.valueOf(R.nextInt(2000) - 1000);
        return new BigDecimal(u, R.nextInt(6) - 1);
    }

    static StringBuilder out = new StringBuilder();
    static int count;

    static void line(String... f) {
        out.append(String.join("\t", f)).append("\n");
        count++;
    }

    static void section(String name) {
        if (out.length() > 0) flush();
        cur = name;
    }

    static String cur = null;
    static StringBuilder file = new StringBuilder();

    static void flush() {
        file.append("(defn ").append(cur).append(" Str []\n  \"")
            .append(out.toString().replace("\\", "\\\\").replace("\"", "\\\""))
            .append("\")\n\n");
        out.setLength(0);
    }

    interface Op { String run(); }

    static String err(Op op) {
        try { return op.run(); } catch (ArithmeticException | NumberFormatException e) { return "ERR"; }
    }

    public static void main(String[] args) {
        file.append(";; 生成物: tools/gen-dec-golden.java が作る。手で編集しない。\n")
            .append(";; JDK: ").append(System.getProperty("java.version")).append("\n")
            .append("(ns dec-golden-data)\n\n");

        // ---- BigInteger
        section("bigint-cases");
        for (int i = 0; i < 400; i++) {
            BigInteger a = bigint(), b = bigint();
            line("add", a.toString(), b.toString(), a.add(b).toString());
            line("sub", a.toString(), b.toString(), a.subtract(b).toString());
            line("mul", a.toString(), b.toString(), a.multiply(b).toString());
            if (b.signum() != 0) {
                BigInteger[] qr = a.divideAndRemainder(b);
                line("divmod", a.toString(), b.toString(), qr[0].toString() + "," + qr[1].toString());
                // 被除数が大きい割り算も (Knuth D の分岐を通す)
                BigInteger big = a.multiply(b).add(BigInteger.valueOf(R.nextInt(1000)));
                BigInteger[] qr2 = big.divideAndRemainder(b);
                line("divmod", big.toString(), b.toString(), qr2[0].toString() + "," + qr2[1].toString());
            } else {
                line("divmod", a.toString(), "0", "ERR");
            }
            line("gcd", a.toString(), b.toString(), a.gcd(b).toString());
            line("cmp", a.toString(), b.toString(), Integer.toString(a.compareTo(b)));
            line("toint", a.toString(), a.bitLength() < 64 ? Long.toString(a.longValue()) : "ERR");
        }
        for (int i = 0; i < 60; i++) {
            BigInteger a = BigInteger.valueOf(R.nextInt(2001) - 1000);
            int e = R.nextInt(60);
            line("pow", a.toString(), Integer.toString(e), a.pow(e).toString());
        }
        String[] longs = {"9223372036854775807", "-9223372036854775808", "9223372036854775808",
            "-9223372036854775809", "18446744073709551616", "1000000000000000000", "-1000000000000000000",
            "999999999999999999", "0", "-0", "+17", "0000123"};
        for (String s : longs) {
            BigInteger a = new BigInteger(s);
            line("toint", s, a.bitLength() < 64 ? Long.toString(a.longValue()) : "ERR");
            line("parse", s, a.toString());
        }
        for (String s : new String[]{"", "-", "+", "1.0", "12a", " 1", "--1", "1e3", "0x10"})
            line("parse", s, err(() -> new BigInteger(s).toString()));
        // 大きい桁の乗除 (Karatsuba と長い除算)
        for (int i = 0; i < 20; i++) {
            BigInteger a = new BigInteger(digits(300 + R.nextInt(1500)));
            BigInteger b = new BigInteger(digits(300 + R.nextInt(700)));
            line("mul", a.toString(), b.toString(), a.multiply(b).toString());
            BigInteger[] qr = a.multiply(b).add(a).divideAndRemainder(b);
            line("divmod", a.multiply(b).add(a).toString(), b.toString(), qr[0] + "," + qr[1]);
        }

        // ---- BigDecimal: parse と toString / toPlainString
        section("dec-parse-cases");
        String[] ps = {"0", "-0", "0.0", "0.00", "-0.000", "0E+3", "0E-7", "0E-6", "0.000000", "0.0000000",
            "-12.340", "1e-3", "1E-3", ".5", "-.5", "+.5", "5.", "1E+10", "1e10", "1E10", "123.456e-2",
            "123456789012345678901234567890.123456789", "1E-6", "1E-7", "0.000001", "0.0000001",
            "0.00000123", "0.000000123", "-0.000000123", "12E-8", "1.5E+3", "1500E-3", "1E+0", "1E-0",
            "100", "1E2", "1.00E2", "-1.00E+2", "9.99E-7", "0.1", "1234.5E-4", "1234.5E+4",
            "1e2147483647", "1e-2147483647", "1e2147483648", "1e-2147483648", "1.5e-2147483648",
            "", "-", ".", "e5", "1e", "1e+", "1.2.3", "1,5", " 1", "1 ", "++1", "1e5.5", "0x10", "NaN",
            "Infinity", "00012.3400", "-00.000", "1E00000000000000000005", "1E-0000000000000000000000007"};
        for (String s : ps) {
            String r;
            try {
                BigDecimal x = new BigDecimal(s);
                // 巨大な scale の toPlainString は作れない (Java も OOM) ので "-" にして比較を省く
                String plain = Math.abs((long) x.scale()) < 10000 ? x.toPlainString() : "-";
                r = x.toString() + "\t" + plain + "\t" + x.unscaledValue() + "\t" + x.scale();
            } catch (NumberFormatException e) { r = "ERR"; }
            line("parse", s, r);
        }
        for (int i = 0; i < 300; i++) {
            BigDecimal x = dec();
            String s = x.toString();
            line("parse", s, s + "\t" + x.toPlainString() + "\t" + x.unscaledValue() + "\t" + x.scale());
            // 同じ値を指数なしで書いた場合 (toPlainString を読み戻す)
            String p = x.toPlainString();
            BigDecimal y = new BigDecimal(p);
            line("parse", p, y.toString() + "\t" + y.toPlainString() + "\t" + y.unscaledValue() + "\t" + y.scale());
        }

        // ---- BigDecimal の算術
        section("dec-arith-cases");
        for (int i = 0; i < 300; i++) {
            BigDecimal a = dec(), b = dec();
            line("add", a.toString(), b.toString(), a.add(b).toString());
            line("sub", a.toString(), b.toString(), a.subtract(b).toString());
            line("mul", a.toString(), b.toString(), a.multiply(b).toString());
            line("cmp", a.toString(), b.toString(), Integer.toString(a.compareTo(b)));
            line("rem", a.toString(), b.toString(), err(() -> a.remainder(b).toString()));
            line("divex", a.toString(), b.toString(), err(() -> a.divide(b).toString()));
            line("div", a.toString(), b.toString(), err(() -> dwDiv(a, b).toString()));
            line("strip", a.toString(), a.stripTrailingZeros().toString());
            line("toint", a.toString(), err(() -> Long.toString(a.longValueExact())));
            line("floor", a.toString(), a.setScale(0, RoundingMode.FLOOR).toString());
            line("ceil", a.toString(), a.setScale(0, RoundingMode.CEILING).toString());
            line("prec", a.toString(), Integer.toString(a.precision()));
        }
        // 小さい値どうし (割り切れる除算、剰余の scale、比較の等号)
        for (int i = 0; i < 300; i++) {
            BigDecimal a = smallDec(), b = smallDec();
            line("rem", a.toString(), b.toString(), err(() -> a.remainder(b).toString()));
            line("divex", a.toString(), b.toString(), err(() -> a.divide(b).toString()));
            line("div", a.toString(), b.toString(), err(() -> dwDiv(a, b).toString()));
            line("cmp", a.toString(), b.toString(), Integer.toString(a.compareTo(b)));
            line("toint", a.toString(), err(() -> Long.toString(a.longValueExact())));
        }
        String[][] fixed = {{"1", "3"}, {"2", "3"}, {"-2", "3"}, {"10", "4"}, {"1", "8"}, {"1.00", "4"},
            {"100", "0.25"}, {"1E+2", "4"}, {"1", "1024"}, {"7", "0.07"}, {"0", "5"}, {"0.00", "5.0"},
            {"5", "0"}, {"0", "0"}, {"1", "7"}, {"22", "7"}, {"1E-10", "3"}, {"9.99", "1"},
            {"123456789012345678901234567890", "7"}, {"1", "6.25E-2"}, {"-7.5", "2"}, {"7.5", "-2"},
            {"1E+5", "1E-5"}, {"9223372036854775807", "1"}, {"9223372036854775808", "1"},
            {"-9223372036854775808", "1"}, {"-9223372036854775809", "1"}, {"12.00", "1"}, {"1.5", "1"}};
        for (String[] f : fixed) {
            BigDecimal a = new BigDecimal(f[0]), b = new BigDecimal(f[1]);
            line("rem", f[0], f[1], err(() -> a.remainder(b).toString()));
            line("divex", f[0], f[1], err(() -> a.divide(b).toString()));
            line("div", f[0], f[1], err(() -> dwDiv(a, b).toString()));
            line("toint", f[0], err(() -> Long.toString(a.longValueExact())));
        }

        // ---- 丸め: divide(mc) / divide(scale) / round / setScale / pow
        section("dec-round-cases");
        for (int i = 0; i < 300; i++) {
            BigDecimal a = dec(), b = dec();
            int prec = 1 + R.nextInt(40);
            RoundingMode m = MODES[R.nextInt(MODES.length)];
            line("divmc", a.toString(), b.toString(), Integer.toString(prec), Integer.toString(m.ordinal()),
                 err(() -> a.divide(b, new MathContext(prec, m)).toString()));
            int sc = R.nextInt(30) - 10;
            line("divsc", a.toString(), b.toString(), Integer.toString(sc), Integer.toString(m.ordinal()),
                 err(() -> a.divide(b, sc, m).toString()));
            line("round", a.toString(), Integer.toString(prec), Integer.toString(m.ordinal()),
                 err(() -> a.round(new MathContext(prec, m)).toString()));
            int ns = a.scale() - R.nextInt(8) + 2;
            line("setsc", a.toString(), Integer.toString(ns), Integer.toString(m.ordinal()),
                 err(() -> a.setScale(ns, m).toString()));
        }
        // .5 の境界をすべてのモードで (正負、偶奇、0.5 ちょうどと少し上下)
        String[] halves = {"0.5", "1.5", "2.5", "-0.5", "-1.5", "-2.5", "0.49", "0.51", "-0.49", "-0.51",
            "2.50", "2.500001", "-2.500001", "9.5", "99.5", "999.5", "0.05", "1.05", "0", "0.0", "-0.00",
            "1.0", "12345.6789", "-12345.6789", "5E-1", "25E-1", "15E+1", "0.9999999", "-0.9999999"};
        for (String h : halves) {
            BigDecimal a = new BigDecimal(h);
            for (RoundingMode m : MODES) {
                String o = Integer.toString(m.ordinal());
                line("setsc", h, "0", o, err(() -> a.setScale(0, m).toString()));
                line("round", h, "1", o, err(() -> a.round(new MathContext(1, m)).toString()));
                line("round", h, "2", o, err(() -> a.round(new MathContext(2, m)).toString()));
                line("divmc", h, "1", "1", o, err(() -> a.divide(BigDecimal.ONE, new MathContext(1, m)).toString()));
                line("divsc", h, "3", "0", o, err(() -> a.divide(new BigDecimal(3), 0, m).toString()));
            }
        }
        // 1/3, 2/3 などの 34 桁 (DECIMAL128) と、繰り上がりで桁が増える場合
        String[][] dd = {{"1", "3"}, {"2", "3"}, {"-2", "3"}, {"1", "7"}, {"10", "3"}, {"1E+40", "3"},
            {"1E-40", "3"}, {"9.99", "1"}, {"99999", "1.00001"}, {"1.9999", "1"}, {"1.00", "1"},
            {"100", "1"}, {"1000", "10"}, {"4", "2"}, {"0.004", "0.2"}, {"1", "0.3"}};
        for (String[] f : dd) {
            BigDecimal a = new BigDecimal(f[0]), b = new BigDecimal(f[1]);
            for (int prec : new int[]{1, 2, 3, 16, 34}) {
                for (RoundingMode m : new RoundingMode[]{RoundingMode.HALF_EVEN, RoundingMode.UP, RoundingMode.DOWN, RoundingMode.UNNECESSARY}) {
                    line("divmc", f[0], f[1], Integer.toString(prec), Integer.toString(m.ordinal()),
                         err(() -> a.divide(b, new MathContext(prec, m)).toString()));
                }
            }
        }
        for (int i = 0; i < 120; i++) {
            BigDecimal a = R.nextInt(3) == 0 ? dec() : smallDec();
            int n = R.nextInt(25) - 8;
            int prec = R.nextInt(4) == 0 ? 0 : 1 + R.nextInt(40);
            RoundingMode m = MODES[R.nextInt(MODES.length - 1)];
            line("powmc", a.toString(), Integer.toString(n), Integer.toString(prec), Integer.toString(m.ordinal()),
                 err(() -> a.pow(n, new MathContext(prec, m)).toString()));
            if (n >= 0) line("pow", a.toString(), Integer.toString(n), a.pow(n).toString());
        }

        // ---- double: Double.toString / BigDecimal.valueOf(double) / doubleValue
        section("float-cases");
        List<Double> ds = new ArrayList<>();
        double[] fixedD = {0.1, 0.2, 0.3, 1.0, 100.0, 1e7, 9999999.0, 9999999.999999998, 1e-3, 0.001,
            9.999999999999998E-4, 1e23, 2e23, 8.41e21, 5e-324, 1e-323, Double.MIN_NORMAL,
            Double.MAX_VALUE, Double.MIN_VALUE, 4.35, 1.0E22, 1.0E21, 123456789.0, 0.5, 2.5E-5,
            Math.PI, Math.E, 1.0 / 3, 2.0 / 3, 1e-7, 1.2345678e-8, 9007199254740993.0, 9007199254740992.0,
            4503599627370496.0, 1.7976931348623157E308, 2.2250738585072014E-308, 2.225073858507201E-308,
            4.9406564584124654E-324, 1e16, 1e17, 123e18, 1.5, 0.05, 0.15, 3.0E-44, 1.1754943508222875E-38,
            -0.0, 0.0, -1.5, -1e300};
        for (double d : fixedD) ds.add(d);
        for (int i = -330; i <= 310; i += 7) { ds.add(Math.pow(10, i)); ds.add(Math.nextUp(Math.pow(10, i))); }
        for (int i = -1074; i <= 1023; i += 37) ds.add(Math.scalb(1.0, i));
        for (int i = 0; i < 250; i++) {
            long bits = R.nextLong() & 0x7fffffffffffffffL;
            double d = Double.longBitsToDouble(bits);
            if (Double.isNaN(d) || Double.isInfinite(d)) continue;
            ds.add(R.nextBoolean() ? -d : d);
        }
        for (int i = 0; i < 100; i++) ds.add((R.nextInt(2000000) - 1000000) / 1000.0);
        for (int i = 0; i < 50; i++) ds.add(R.nextDouble() * Math.pow(10, R.nextInt(20) - 10));
        for (double d : ds) {
            if (Double.isInfinite(d) || Double.isNaN(d)) continue;
            // 入力は Double.toString の文字列 (Clay 側は strtod で同じ double に戻す)
            String s = Double.toString(d);
            line("dtostr", s, s);
            line("dvalueof", s, BigDecimal.valueOf(d).toString());
        }
        for (int i = 0; i < 150; i++) {
            BigDecimal x = dec();
            line("todouble", x.toString(), Double.toString(x.doubleValue()));
        }
        for (String s : new String[]{"1E+400", "-1E+400", "1E-400", "0.1", "1.00000000000000011102230246251565404236316680908203125",
                                     "1.00000000000000011102230246251565404236316680908203124", "9007199254740993", "123456789012345678901234567890"})
            line("todouble", s, Double.toString(new BigDecimal(s).doubleValue()));
        flush();
        System.out.print(file);
        System.err.println("golden lines: " + count);
    }

    // DataWeave の `/`: 割り切れれば divide(BigDecimal)、割り切れなければ DECIMAL128
    static BigDecimal dwDiv(BigDecimal a, BigDecimal b) {
        try { return a.divide(b); }
        catch (ArithmeticException e) {
            if (b.signum() == 0) throw e;
            return a.divide(b, MathContext.DECIMAL128);
        }
    }
}
