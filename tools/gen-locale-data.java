// mulay.lib.time の地域 (Locale) ごとの名前を java.time (JDK 17、CLDR) から作る。
//
//   /usr/lib/jvm/java-17-openjdk-amd64/bin/java tools/gen-locale-data.java [mulay のルート]
//
// 出力: src/mulay/lib/time/locales.clay
//   locale-data  Map: 言語タグ (小文字、"es"、"pt-br") -> 名前の列 (並びは LAYOUT)
// DateTimeFormatter.ofPattern(p, locale) が書く月・曜日・午前午後・紀元・四半期の名前と、
// WeekFields.of(locale) の週の始まり・最初の週の最小日数。

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.*;
import java.time.format.*;
import java.time.temporal.*;
import java.util.*;

public class GenLocaleData {
    // 言語だけのタグと、名前が言語の既定と違う地域 (pt-BR など) を入れる
    static final String[] TAGS = {
        "en", "en-US", "en-GB", "es", "es-MX", "fr", "fr-CA", "de", "de-AT", "de-CH", "it", "pt", "pt-BR", "nl", "ja", "zh",
        "zh-TW", "ko", "ru", "pl", "sv", "da", "fi", "nb", "no", "tr", "cs", "hu", "ro", "el", "he", "ar", "th",
        "vi", "id", "uk", "ca", "sk", "sl", "hr", "bg", "lt", "lv", "et", "ms", "hi", "bn", "fa", "sr", "is",
        "ga", "eu", "gl", "af", "sw", "ta", "te", "mr", "ur", "fil", "kk", "az", "ka", "hy", "sq", "mk", "mt", "cy"
    };

    public static void main(String[] args) throws Exception {
        Path root = Paths.get(args.length > 0 ? args[0] : ".").toAbsolutePath().normalize();
        StringBuilder b = new StringBuilder();
        b.append("(ns mulay.lib.time.locales)\n\n");
        b.append("(def locale-data\n  {");
        boolean first = true;
        for (String tag : TAGS) {
            Locale loc = Locale.forLanguageTag(tag);
            List<String> xs = new ArrayList<>();
            for (String p : new String[]{"MMM", "MMMM", "MMMMM", "LLL", "LLLL", "LLLLL"})
                for (int m = 1; m <= 12; m++) xs.add(fmt(p, loc, LocalDate.of(2020, m, 1)));
            for (String p : new String[]{"EEE", "EEEE", "EEEEE", "ccc", "cccc", "ccccc"})
                for (int d = 0; d < 7; d++) xs.add(fmt(p, loc, LocalDate.of(2020, 1, 6).plusDays(d)));
            xs.add(fmt("a", loc, LocalTime.of(6, 0)));
            xs.add(fmt("a", loc, LocalTime.of(18, 0)));
            for (String p : new String[]{"G", "GGGG", "GGGGG"}) {
                xs.add(fmt(p, loc, LocalDate.of(-5, 1, 1)));
                xs.add(fmt(p, loc, LocalDate.of(2020, 1, 1)));
            }
            for (String p : new String[]{"QQQ", "QQQQ", "QQQQQ", "qqq", "qqqq", "qqqqq"})
                for (int q = 0; q < 4; q++) xs.add(fmt(p, loc, LocalDate.of(2020, 1 + 3 * q, 1)));
            WeekFields wf = WeekFields.of(loc);
            xs.add(Integer.toString(wf.getFirstDayOfWeek().getValue()));
            xs.add(Integer.toString(wf.getMinimalDaysInFirstWeek()));
            if (!first) b.append("\n   ");
            first = false;
            b.append('"').append(tag.toLowerCase(Locale.ROOT)).append("\" [");
            for (int i = 0; i < xs.size(); i++) {
                if (i > 0) b.append(' ');
                b.append(lit(xs.get(i)));
            }
            b.append(']');
        }
        b.append("})\n");
        Files.write(root.resolve("src/mulay/lib/time/locales.clay"), b.toString().getBytes(StandardCharsets.UTF_8));
    }

    static String fmt(String p, Locale loc, TemporalAccessor t) {
        return DateTimeFormatter.ofPattern(p, loc).format(t);
    }

    // Clay の文字列リテラル (エスケープは \" \\ だけ。制御文字は出ない)
    static String lit(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            if (c == '"' || c == '\\') b.append('\\');
            b.append(c);
        }
        return b.append('"').toString();
    }
}
