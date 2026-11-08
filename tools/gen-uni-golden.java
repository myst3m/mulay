// Generates test/uni/golden_test.clay: java.lang.Character / String results that
// mulay.lib.uni must reproduce.  Run: java tools/gen-uni-golden.java > test/uni/golden_test.clay
// Only code points whose general category is the same in the JVM's Unicode
// version and in mulay's tables (python unicodedata) are sampled; the list of
// categories per code point is read from tools/uni-gc.txt (made by the python
// one-liner in the comment of main).
import java.util.*;
import java.nio.file.*;

public class GenUniGolden {
    static String esc(String s) {
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < s.length(); ) {
            int c = s.codePointAt(i); i += Character.charCount(c);
            if (c == '"' ) b.append("\\\"");
            else if (c == '\\') b.append("\\\\");
            else if (c == '\n') b.append("\\n");
            else if (c == '\t') b.append("\\t");
            else if (c == '\r') b.append("\\r");
            else b.appendCodePoint(c);
        }
        return b.toString();
    }
    static final String[] GC = {"Cn","Lu","Ll","Lt","Lm","Lo","Mn","Mc","Me","Nd","Nl","No","Pc","Pd","Ps","Pe","Pi","Pf","Po","Sm","Sc","Sk","So","Zs","Zl","Zp","Cc","Cf","Cs","Co"};
    static String gcName(int t) {
        switch (t) {
            case Character.UNASSIGNED: return "Cn";
            case Character.UPPERCASE_LETTER: return "Lu";
            case Character.LOWERCASE_LETTER: return "Ll";
            case Character.TITLECASE_LETTER: return "Lt";
            case Character.MODIFIER_LETTER: return "Lm";
            case Character.OTHER_LETTER: return "Lo";
            case Character.NON_SPACING_MARK: return "Mn";
            case Character.COMBINING_SPACING_MARK: return "Mc";
            case Character.ENCLOSING_MARK: return "Me";
            case Character.DECIMAL_DIGIT_NUMBER: return "Nd";
            case Character.LETTER_NUMBER: return "Nl";
            case Character.OTHER_NUMBER: return "No";
            case Character.CONNECTOR_PUNCTUATION: return "Pc";
            case Character.DASH_PUNCTUATION: return "Pd";
            case Character.START_PUNCTUATION: return "Ps";
            case Character.END_PUNCTUATION: return "Pe";
            case Character.INITIAL_QUOTE_PUNCTUATION: return "Pi";
            case Character.FINAL_QUOTE_PUNCTUATION: return "Pf";
            case Character.OTHER_PUNCTUATION: return "Po";
            case Character.MATH_SYMBOL: return "Sm";
            case Character.CURRENCY_SYMBOL: return "Sc";
            case Character.MODIFIER_SYMBOL: return "Sk";
            case Character.OTHER_SYMBOL: return "So";
            case Character.SPACE_SEPARATOR: return "Zs";
            case Character.LINE_SEPARATOR: return "Zl";
            case Character.PARAGRAPH_SEPARATOR: return "Zp";
            case Character.CONTROL: return "Cc";
            case Character.FORMAT: return "Cf";
            case Character.SURROGATE: return "Cs";
            case Character.PRIVATE_USE: return "Co";
        }
        return "??";
    }
    public static void main(String[] a) throws Exception {
        // tools/uni-gc.txt is not kept; it is produced on the fly by:
        //   python3 -c 'import unicodedata as u;print("".join(u.category(chr(c)) for c in range(0x110000)))'
        String py = new String(Files.readAllBytes(Paths.get(a[0]))).trim();
        StringBuilder rec = new StringBuilder();
        int n = 0;
        Random rnd = new Random(42);
        List<Integer> sample = new ArrayList<>();
        for (int c = 0; c < 0x3000; c++) sample.add(c);
        for (int i = 0; i < 6000; i++) sample.add(0x3000 + rnd.nextInt(0x110000 - 0x3000));
        int[] extra = {0x1E9E, 0x2126, 0x212A, 0x212B, 0x10400, 0x10428, 0x1D400, 0x1F600, 0xFB00, 0xFF21, 0xFF41, 0x10D0, 0x1C90, 0x13A0, 0xAB70};
        for (int c : extra) sample.add(c);
        // Code points whose properties changed between the JVM's Unicode (13.0 on
        // Java 17) and mulay's tables (16.0): new case pairs (U+019B, U+0264),
        // Other_Alphabetic additions (combining letters), Other_Lowercase (U+10FC).
        // Found by running this golden; each was checked against the UCD history.
        Set<Integer> drift = new HashSet<>();
        int[][] driftRanges = {{0x19B,0x19B},{0x264,0x264},{0x363,0x36F},{0xC04,0xC04},{0xF82,0xF83},{0x10FC,0x10FC},{0x1DD3,0x1DF4}};
        for (int[] r : driftRanges) for (int c = r[0]; c <= r[1]; c++) drift.add(c);
        for (int c : sample) {
            if (c >= 0xD800 && c <= 0xDFFF) continue;
            if (drift.contains(c)) continue;
            String jg = gcName(Character.getType(c));
            String pg = py.substring(2 * c, 2 * c + 2);
            if (!jg.equals(pg)) continue;              // Unicode version drift
            if (jg.equals("Cn")) continue;
            int flags = (Character.isLetter(c) ? 1 : 0) | (Character.isDigit(c) ? 2 : 0)
                | (Character.isWhitespace(c) ? 4 : 0) | (Character.isUpperCase(c) ? 8 : 0)
                | (Character.isLowerCase(c) ? 16 : 0) | (Character.isAlphabetic(c) ? 32 : 0)
                | (Character.isLetterOrDigit(c) ? 64 : 0) | (Character.isTitleCase(c) ? 128 : 0)
                | (Character.isSpaceChar(c) ? 256 : 0) | (Character.isIdeographic(c) ? 512 : 0);
            rec.append(String.format("%06X%s%03X%06X%06X%06X", c, jg, flags,
                Character.toUpperCase(c), Character.toLowerCase(c), Character.toTitleCase(c)));
            n++;
        }
        System.out.println("(ns uni-golden-test (:require [mulay.lib.uni :as u] [clay.utf8 :as u8]))");
        System.out.println(";; GENERATED by tools/gen-uni-golden.java on " + System.getProperty("java.version") + " -- do not edit.");
        System.out.println(";; record: cp(6) gc(2) flags(3) upper(6) lower(6) title(6); flags = letter 1, digit 2,");
        System.out.println(";; whitespace 4, upper 8, lower 16, alphabetic 32, letter-or-digit 64, title 128,");
        System.out.println(";; space-char 256, ideographic 512.");
        System.out.println("(def N-RECS " + n + ")");
        System.out.println("(def RECS \"" + rec + "\")");
        String[] strs = {"hello World", "straße", "ΟΔΟΣ", "ΟΔΟΣ ΚΑΛΟΣ.", "Σ", "ﬁx", "İstanbul", "ǆemal", "ŉ", "ΐ", "ᾳ", "Ǉ", "ÀÉÎõü", "Ὀδυσσεύς", "ԱԲԳ", "𐐀𐐨", "ﬀﬃ", "ʼn", "ǰ", "ẞ", "Kelvin K", "ᏸᏹ", "日本語テキスト", " x ", " \t\n x 　", "", "abc123XYZ"};
        StringBuilder u = new StringBuilder();
        for (String s : strs) {
            u.append("(is (= (u/upper \"").append(esc(s)).append("\") \"").append(esc(s.toUpperCase(Locale.ROOT))).append("\"))\n  ");
            u.append("(is (= (u/lower \"").append(esc(s)).append("\") \"").append(esc(s.toLowerCase(Locale.ROOT))).append("\"))\n  ");
            u.append("(is (= (u/java-trim \"").append(esc(s)).append("\") \"").append(esc(s.trim())).append("\"))\n  ");
            u.append("(is (= (u/strip \"").append(esc(s)).append("\") \"").append(esc(s.strip())).append("\"))\n  ");
            u.append("(is (= (u8/codepoint-count \"").append(esc(s)).append("\") ").append(s.codePointCount(0, s.length())).append("))\n  ");
        }
        System.out.println("(deftest java-strings\n  " + u.toString().trim() + ")");
        System.out.println(String.join("\n",
            "(defn- hv Int [s: &Str i: Int n: Int]",
            "  (loop [k 0 acc 0] (if (>= k n) acc (let [c (nth s (+ i k))] (recur (+ k 1) (+ (* acc 16) (if (<= c 57) (- c 48) (- c 55))))))))",
            "(defn- flags Int [c: Int]",
            "  (+ (if (u/letter? c) 1 0) (if (u/java-digit? c) 2 0) (if (u/java-whitespace? c) 4 0) (if (u/upper-case? c) 8 0)",
            "     (if (u/lower-case? c) 16 0) (if (u/alphabetic? c) 32 0) (if (u/letter-or-digit? c) 64 0)",
            "     (if (u/title-case? c) 128 0) (if (u/space-char? c) 256 0) (if (u/ideographic? c) 512 0)))",
            "(defn- check Int []",
            "  (loop [k 0 bad 0]",
            "    (if (>= k N-RECS) bad",
            "      (let [o (* k 29) c (hv RECS o 6) g (subs RECS (+ o 6) (+ o 8)) f (hv RECS (+ o 8) 3)",
            "            up (hv RECS (+ o 11) 6) lo (hv RECS (+ o 17) 6) ti (hv RECS (+ o 23) 6)",
            "            ok (and (= g (u/gc c)) (= f (flags c)) (= up (u/upper-cp c)) (= lo (u/lower-cp c)) (= ti (u/title-cp c)))]",
            "        (if ok (recur (+ k 1) bad)",
            "          (let [p (if (< bad 20) (println (str \"mismatch cp=\" c \" gc \" g \"/\" (u/gc c) \" flags \" f \"/\" (flags c) \" up \" up \"/\" (u/upper-cp c) \" lo \" lo \"/\" (u/lower-cp c) \" ti \" ti \"/\" (u/title-cp c))) 0)]",
            "            (recur (+ k 1) (+ bad 1))))))))",
            "(deftest java-character (is (= (check) 0)))"));
    }
}
