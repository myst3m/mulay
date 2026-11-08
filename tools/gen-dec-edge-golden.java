// mulay.lib.dec の 64 ビットの境目 (±2^63、Long.MIN_VALUE、10^18 前後、平方根の前後) の期待値を Java で作る。
//
//   /usr/lib/jvm/java-17-openjdk-amd64/bin/java tools/gen-dec-edge-golden.java > test/dec/edge_data.clay
//
// 行の形は tools/gen-dec-golden.java と同じ (演算名 入力... 期待値、失敗は "ERR")。乱数の種は固定。

import java.math.*;
import java.util.*;

public class GenDecEdgeGolden {
    static final Random R = new Random(20261107L);
    static final RoundingMode[] MODES = RoundingMode.values();
    static StringBuilder out = new StringBuilder();

    interface Op { String run(); }

    static String err(Op op) {
        try { return op.run(); } catch (ArithmeticException | NumberFormatException e) { return "ERR"; }
    }

    static void line(String... f) { out.append(String.join("\t", f)).append("\n"); }

    public static void main(String[] args) {
        BigInteger two63 = BigInteger.ONE.shiftLeft(63);
        BigInteger[] us = {
            BigInteger.ZERO, BigInteger.ONE, BigInteger.ONE.negate(), BigInteger.valueOf(9), BigInteger.TEN,
            BigInteger.valueOf(1000), BigInteger.valueOf(-1200), BigInteger.valueOf(123456789),
            two63.subtract(BigInteger.ONE), two63.negate(), two63.negate().add(BigInteger.ONE),
            two63, two63.negate().subtract(BigInteger.ONE), two63.subtract(BigInteger.ONE).multiply(BigInteger.TEN),
            BigInteger.TEN.pow(18), BigInteger.TEN.pow(18).subtract(BigInteger.ONE), BigInteger.TEN.pow(18).negate(),
            BigInteger.TEN.pow(19), BigInteger.valueOf(922337203685477580L), BigInteger.ONE.shiftLeft(62),
            BigInteger.valueOf(3037000499L), BigInteger.valueOf(-3037000500L), BigInteger.valueOf(999999999999999999L),
            new BigInteger("-99999999999999999990"), BigInteger.valueOf(4999999999999999995L),
            BigInteger.ONE.shiftLeft(57), BigInteger.ONE.shiftLeft(57).subtract(BigInteger.ONE), BigInteger.ONE.shiftLeft(57).negate(),
            BigInteger.ONE.shiftLeft(57).negate().subtract(BigInteger.ONE), BigInteger.ONE.shiftLeft(57).add(BigInteger.ONE),
            BigInteger.valueOf(72057594037927935L), BigInteger.valueOf(-144115188075855870L)};
        int[] scales = {-33, -32, -31, -3, -1, 0, 1, 2, 5, 18, 19, 20, 30, 31, 32, 33};
        List<BigDecimal> vs = new ArrayList<>();
        for (BigInteger u : us) for (int s : scales) vs.add(new BigDecimal(u, s));

        StringBuilder file = new StringBuilder();
        file.append(";; 生成物: tools/gen-dec-edge-golden.java が作る。手で編集しない。\n")
            .append(";; JDK: ").append(System.getProperty("java.version")).append("\n")
            .append("(ns dec-edge-data)\n\n");

        for (BigDecimal x : vs) {
            String s = x.toString();
            line("parse", s, s + "\t" + (Math.abs(x.scale()) < 10000 ? x.toPlainString() : "-") + "\t" + x.unscaledValue() + "\t" + x.scale());
            line("neg", s, x.negate().toString());
            line("abs", s, x.abs().toString());
            line("strip", s, x.stripTrailingZeros().toString());
            line("prec", s, Integer.toString(x.precision()));
            line("toint", s, err(() -> Long.toString(x.longValueExact())));
            line("floor", s, x.setScale(0, RoundingMode.FLOOR).toString());
            line("ceil", s, x.setScale(0, RoundingMode.CEILING).toString());
            line("intq", s, Boolean.toString(x.signum() == 0 || x.stripTrailingZeros().scale() <= 0));
            for (int k = 0; k < 4; k++) {
                int ns = scales[R.nextInt(scales.length)] + R.nextInt(3) - 1;
                int m = R.nextInt(MODES.length);
                line("setsc", s, Integer.toString(ns), Integer.toString(m), err(() -> x.setScale(ns, MODES[m]).toString()));
                int p = new int[]{1, 2, 5, 17, 18, 19, 20}[R.nextInt(7)];
                int m2 = R.nextInt(MODES.length);
                line("round", s, Integer.toString(p), Integer.toString(m2), err(() -> x.round(new MathContext(p, MODES[m2])).toString()));
            }
        }
        for (int i = 0; i < 8000; i++) {
            BigDecimal a = vs.get(R.nextInt(vs.size())), b = vs.get(R.nextInt(vs.size()));
            String sa = a.toString(), sb = b.toString();
            line("add", sa, sb, a.add(b).toString());
            line("sub", sa, sb, a.subtract(b).toString());
            line("mul", sa, sb, a.multiply(b).toString());
            line("cmp", sa, sb, Integer.toString(a.compareTo(b)));
            line("eq", sa, sb, Boolean.toString(a.equals(b)));
            if (i % 4 == 0) {
                line("rem", sa, sb, err(() -> a.remainder(b).toString()));
                line("div", sa, sb, err(() -> {
                    try { return a.divide(b).toString(); }
                    catch (ArithmeticException e) {
                        if (b.signum() == 0) throw e;
                        return a.divide(b, MathContext.DECIMAL128).toString();
                    }
                }));
            }
        }
        long[] ns = {1, 3, 7, 9, 10, 99, 997, 65536, 999999999, 1000000000, 123456789012L, Long.MAX_VALUE, Long.MIN_VALUE + 1, Long.MIN_VALUE};
        int[] precs = {1, 2, 5, 9, 16, 17, 18, 19, 20, 27, 28, 33, 34, 35};
        for (int i = 0; i < 6000; i++) {
            BigDecimal a = new BigDecimal(BigInteger.valueOf(R.nextBoolean() ? ns[R.nextInt(ns.length)] * (R.nextBoolean() ? 1 : -1) : R.nextLong() >> R.nextInt(64)), R.nextInt(10) - 3);
            BigDecimal b = new BigDecimal(BigInteger.valueOf(ns[R.nextInt(ns.length)] * (R.nextBoolean() ? 1 : -1)), R.nextInt(10) - 3);
            int p = precs[R.nextInt(precs.length)];
            int m = R.nextInt(MODES.length);
            line("divmc", a.toString(), b.toString(), Integer.toString(p), Integer.toString(m), err(() -> a.divide(b, new MathContext(p, MODES[m])).toString()));
        }
        for (BigDecimal a : vs) {
            line("eq", a.toString(), new BigDecimal(a.unscaledValue(), a.scale()).toString(), "true");
            BigDecimal b = a.add(BigDecimal.ONE.movePointLeft(Math.max(a.scale(), 0)));
            line("add", b.toString(), a.negate().toString(), b.add(a.negate()).toString());
        }
        file.append("(defn edge-cases Str []\n  \"").append(out.toString().replace("\\", "\\\\").replace("\"", "\\\"")).append("\")\n");
        System.out.print(file);
    }
}
