// mulay.lib.time の golden データを java.time から作る。
//
//   java tools/gen-time-golden.java [mulay のルート]
//
// 出力:
//   src/mulay/lib/time/names.clay        ゾーンの表示名 (DateTimeFormatter の z / zzzz、Locale.US) と逆引き表
//   test/time/golden_cal_data.clay       暦 (epoch 日・曜日・年内日・ISO/US 週)
//   test/time/golden_amount_data.clay    Period / Duration の解析と表示、月末加算、between
//   test/time/golden_dst_data.clay       DST 境界 (ofLocal / ofInstant / 加算 / ゾーン変換)
//   test/time/golden_fmt_data.clay       DateTimeFormatter.format (パターン × 値)
//   test/time/golden_parse_data.clay     DateTimeFormatter.parse (SMART resolver)
// 各データは TAB 区切りの 1 行 1 ケース。読み方は test/time/golden_*_test.clay にある。
//
// 注意: JDK の tzdb (ZoneRulesProvider.getVersions) と /usr/share/zoneinfo の版がずれると DST の
// ケースが食い違うことがある。対象ゾーンは規則の変わりにくいものを選んでいる。

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.text.DateFormatSymbols;
import java.time.*;
import java.time.format.*;
import java.time.temporal.*;
import java.time.zone.*;
import java.util.*;

public class GenTimeGolden {
    static Path root;
    static final Locale L = Locale.US;

    public static void main(String[] args) throws Exception {
        root = Paths.get(args.length > 0 ? args[0] : ".").toAbsolutePath().normalize();
        names();
        cal();
        amount();
        dst();
        fmt();
        parse();
        System.err.println("tzdb " + ZoneRulesProvider.getVersions("UTC").keySet());
    }

    // ---- 出力の小道具 ----
    static String q(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            if (c == '"' || c == '\\') b.append('\\').append(c);
            else if (c == '\t') b.append("\\t");
            else if (c == '\n') b.append("\\n");
            else b.append(c);
        }
        return b.append('"').toString();
    }

    static void writeData(String file, String ns, String header, List<String> lines) throws IOException {
        StringBuilder b = new StringBuilder();
        b.append("(ns ").append(ns).append(")\n\n");
        b.append(";; 生成物: tools/gen-time-golden.java (手で編集しない)\n");
        for (String h : header.split("\n")) b.append(";; ").append(h).append("\n");
        // 大きなベクタ リテラル 1 つはコンパイラが落ちるので、CHUNK 行ごとの関数に分ける
        final int CHUNK = 500;
        int parts = (lines.size() + CHUNK - 1) / CHUNK;
        for (int k = 0; k < parts; k++) {
            b.append("\n(defn- part").append(k).append(" Vec(Str) []\n  [");
            for (int i = k * CHUNK; i < Math.min(lines.size(), (k + 1) * CHUNK); i++) {
                if (i > k * CHUNK) b.append("\n   ");
                b.append(q(lines.get(i)));
            }
            b.append("])\n");
        }
        b.append("\n(defn cases Vec(Str) []\n  (let [acc: Vec(Str) []]\n    (-> acc");
        for (int k = 0; k < parts; k++) b.append("\n        (concat (part").append(k).append("))");
        b.append(")))\n");
        Path p = root.resolve(file);
        Files.write(p, b.toString().getBytes(StandardCharsets.UTF_8));
        System.err.println(file + ": " + lines.size() + " cases");
    }

    static String j(Object... xs) {
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < xs.length; i++) {
            if (i > 0) b.append('\t');
            b.append(String.valueOf(xs[i]));
        }
        return b.toString();
    }

    static String err(Throwable e) {
        String m = e.getMessage();
        return "ERR:" + (m == null ? e.getClass().getSimpleName() : m);
    }

    // ---- ゾーン名 ----
    static void names() throws IOException {
        TreeSet<String> ids = new TreeSet<>(ZoneId.getAvailableZoneIds());
        StringBuilder b = new StringBuilder();
        b.append("(ns mulay.lib.time.names)\n\n");
        b.append(";; 生成物: tools/gen-time-golden.java (手で編集しない)。JDK tzdb ")
         .append(ZoneRulesProvider.getVersions("UTC").keySet()).append("、Locale.US。\n");
        b.append(";; DateTimeFormatter の z (短い名前) と zzzz (長い名前) が出す表示名と、その逆引き。\n;;\n");
        b.append(";; 公開 API\n");
        b.append(";;   zone-names    Map: ゾーン ID -> [標準の短い名前 標準の長い名前 夏時間の短い名前 夏時間の長い名前 総称の短い名前 総称の長い名前]\n");
        b.append(";;   short-names   Map: 短い名前 -> パースしたときのゾーン ID (z..zzz)\n");
        b.append(";;   long-names    Map: 長い名前 -> ゾーン ID (zzzz)\n");
        b.append(";;   text-ids      Vec: z / zzzz の解析で ID のまま受ける region ID\n\n");
        TreeSet<String> genShort = new TreeSet<>(), genLong = new TreeSet<>();
        b.append("(def zone-names\n  {");
        boolean first = true;
        int mismatch = 0;
        for (String id : ids) {
            TimeZone tz = TimeZone.getTimeZone(id);
            String ss = tz.getDisplayName(false, TimeZone.SHORT, L);
            String sl = tz.getDisplayName(false, TimeZone.LONG, L);
            String ds = tz.getDisplayName(true, TimeZone.SHORT, L);
            String dl = tz.getDisplayName(true, TimeZone.LONG, L);
            // DateTimeFormatter と一致するか (1 月と 7 月で確かめる)
            ZoneId z = ZoneId.of(id);
            for (int m : new int[]{1, 7}) {
                ZonedDateTime x = ZonedDateTime.of(2021, m, 15, 12, 0, 0, 0, z);
                boolean dst = z.getRules().isDaylightSavings(x.toInstant());
                String f = DateTimeFormatter.ofPattern("z|zzzz", L).format(x);
                String want = dst ? ds + "|" + dl : ss + "|" + sl;
                if (!f.equals(want)) { mismatch++; System.err.println("name mismatch " + id + " " + f + " vs " + want); }
            }
            ZonedDateTime gx = ZonedDateTime.of(2021, 1, 15, 12, 0, 0, 0, z);
            String gs = DateTimeFormatter.ofPattern("v", L).format(gx);
            String gl = DateTimeFormatter.ofPattern("vvvv", L).format(gx);
            genShort.add(gs); genLong.add(gl);
            if (!first) b.append("\n   ");
            first = false;
            b.append(q(id)).append(" [").append(q(ss)).append(' ').append(q(sl)).append(' ').append(q(ds)).append(' ').append(q(dl))
             .append(' ').append(q(gs)).append(' ').append(q(gl)).append(']');
        }
        b.append("})\n\n");
        // 逆引き
        TreeMap<String, String> shortRev = new TreeMap<>(), longRev = new TreeMap<>();
        String[][] zs = DateFormatSymbols.getInstance(L).getZoneStrings();
        TreeSet<String> shorts = new TreeSet<>(), longs = new TreeSet<>();
        for (String[] r : zs) {
            if (r.length > 2) shorts.add(r[2]);
            if (r.length > 4) shorts.add(r[4]);
            if (r.length > 1) longs.add(r[1]);
            if (r.length > 3) longs.add(r[3]);
        }
        for (String id : ids) {
            TimeZone tz = TimeZone.getTimeZone(id);
            shorts.add(tz.getDisplayName(false, TimeZone.SHORT, L));
            shorts.add(tz.getDisplayName(true, TimeZone.SHORT, L));
            longs.add(tz.getDisplayName(false, TimeZone.LONG, L));
            longs.add(tz.getDisplayName(true, TimeZone.LONG, L));
        }
        shorts.addAll(genShort);
        longs.addAll(genLong);
        for (String s : shorts) {
            try {
                ZoneId z = DateTimeFormatter.ofPattern("z", L).parse(s).query(TemporalQueries.zoneId());
                if (z != null && !z.getId().equals(s)) shortRev.put(s, z.getId());
            } catch (Exception e) { }
        }
        for (String s : longs) {
            try {
                ZoneId z = DateTimeFormatter.ofPattern("zzzz", L).parse(s).query(TemporalQueries.zoneId());
                if (z != null && !z.getId().equals(s)) longRev.put(s, z.getId());
            } catch (Exception e) { }
        }
        // z / zzzz の解析木に入る ID (DateFormatSymbols の zoneStrings にある region ID)
        TreeSet<String> textIds = new TreeSet<>();
        for (String[] r : zs) if (ids.contains(r[0])) textIds.add(r[0]);
        b.append(";; z / zzzz の解析で ID として受ける region ID (Java の解析木と同じ集合)\n(def text-ids\n  [");
        first = true;
        for (String id : textIds) { if (!first) b.append("\n   "); first = false; b.append(q(id)); }
        b.append("])\n\n");
        for (String[] pair : new String[][]{{"short-names", ""}, {"long-names", ""}}) {
            TreeMap<String, String> m = pair[0].equals("short-names") ? shortRev : longRev;
            b.append("(def ").append(pair[0]).append("\n  {");
            first = true;
            for (Map.Entry<String, String> e : m.entrySet()) {
                if (!first) b.append("\n   ");
                first = false;
                b.append(q(e.getKey())).append(' ').append(q(e.getValue()));
            }
            b.append("})\n\n");
        }
        Files.write(root.resolve("src/mulay/lib/time/names.clay"), b.toString().getBytes(StandardCharsets.UTF_8));
        System.err.println("names: " + ids.size() + " zones, " + shortRev.size() + " short, " + longRev.size() + " long, mismatch " + mismatch);
    }

    // ---- 暦 ----
    static void cal() throws IOException {
        List<String> out = new ArrayList<>();
        List<LocalDate> ds = new ArrayList<>();
        for (int y = 1995; y <= 2032; y++) {
            for (int d = 20; d <= 31; d++) ds.add(LocalDate.of(y, 12, d));
            for (int d = 1; d <= 10; d++) ds.add(LocalDate.of(y, 1, d));
        }
        Random r = new Random(42);
        for (int i = 0; i < 300; i++) ds.add(LocalDate.ofEpochDay(r.nextInt(200000) - 100000));
        for (int i = 0; i < 60; i++) ds.add(LocalDate.ofEpochDay((long) (r.nextDouble() * 730000000000L) - 365000000000L));
        ds.add(LocalDate.MIN); ds.add(LocalDate.MAX); ds.add(LocalDate.of(0, 1, 1)); ds.add(LocalDate.of(-1, 12, 31));
        WeekFields us = WeekFields.of(L), iso = WeekFields.ISO;
        for (LocalDate d : ds) {
            out.add(j(d, d.toEpochDay(), d.getDayOfWeek().getValue(), d.getDayOfYear(),
                    d.getLong(iso.weekBasedYear()), d.getLong(iso.weekOfWeekBasedYear()), d.getLong(iso.weekOfMonth()), d.getLong(iso.weekOfYear()),
                    d.getLong(us.weekBasedYear()), d.getLong(us.weekOfWeekBasedYear()), d.getLong(us.weekOfMonth()), d.getLong(us.weekOfYear()),
                    d.getLong(us.dayOfWeek()), d.lengthOfMonth(), d.isLeapYear()));
        }
        writeData("test/time/golden_cal_data.clay", "golden-cal-data",
                "date epochDay dow doy isoWBY isoWoWBY isoWoM isoWoY usWBY usWoWBY usWoM usWoY usDow lengthOfMonth leap", out);
    }

    // ---- 期間 ----
    static void amount() throws IOException {
        List<String> out = new ArrayList<>();
        String[] ps = {"P1Y2M3D", "P0D", "P1W", "P-1D", "-P1D", "+P1Y", "p1y", "P1Y-2M", "P2W3D", "P", "PT1H", "P1DT2H", "P1.5D",
                "P2147483647D", "P2147483648D", "P-2147483648Y", "P1Y1Y", "P1M1Y", "P1D2", "", "P0Y0M0D", "P12M", "-P1Y2M3W4D", "P1y2m3w4d"};
        for (String s : ps) {
            String rp, rd, rw;
            try { rp = Period.parse(s).toString(); } catch (Exception e) { rp = "ERR"; }
            try { rd = Duration.parse(s).toString(); } catch (Exception e) { rd = "ERR"; }
            out.add(j("pparse", s, rp));
            out.add(j("dparse", s, rd));
        }
        String[] dss = {"PT1H30M", "PT0S", "P1DT2H", "PT-1.5S", "PT1.5S", "-PT1H", "PT-0.5S", "PT0.000000001S", "PT1,5S", "pt1h",
                "P2D", "PT36H", "PT90M", "PT3601S", "P1DT", "PT", "P", "PT1.S", "PT1.1234567891S", "-PT-1H", "PT+1H", "P-1DT1H",
                "PT9223372036854775807S", "PT9223372036854775808S", "P106751991167300D", "P106751991167301D", "PT1H2M3.004S",
                "PT-0S", "PT0.5M", "P1W", "PT1M-1S"};
        for (String s : dss) {
            String rd;
            try { rd = Duration.parse(s).toString(); } catch (Exception e) { rd = "ERR"; }
            out.add(j("dparse", s, rd));
        }
        Random r = new Random(7);
        long[] secs = {0, 1, -1, 59, 60, 3599, 3600, 86399, 86400, -86401, 1234567, -1234567, Long.MAX_VALUE, Long.MIN_VALUE + 1};
        int[] nanos = {0, 1, 500000000, 999999999, 120000000, 100};
        for (long s : secs) for (int n : nanos) {
            if (s == Long.MAX_VALUE && n > 0) continue;
            Duration d = Duration.ofSeconds(s, n);
            out.add(j("dstr", s, n, d.toString(), d.getSeconds(), d.getNano()));
        }
        for (int i = 0; i < 40; i++) {
            long s = r.nextInt(2000000) - 1000000; int n = r.nextInt(1000000000);
            Duration d = Duration.ofSeconds(s, n);
            out.add(j("dstr", s, n, d.toString(), d.getSeconds(), d.getNano()));
        }
        // 月末加算
        LocalDate[] bases = {LocalDate.of(2020, 1, 31), LocalDate.of(2020, 2, 29), LocalDate.of(2019, 1, 31), LocalDate.of(2020, 3, 31),
                LocalDate.of(2020, 12, 31), LocalDate.of(2021, 5, 31), LocalDate.of(-1, 2, 28), LocalDate.of(0, 2, 29), LocalDate.of(2000, 2, 29)};
        Period[] pp = {Period.ofMonths(1), Period.ofMonths(-1), Period.ofYears(1), Period.ofYears(-1), Period.of(1, 1, 1), Period.of(0, 13, -40),
                Period.ofDays(-366), Period.of(-1, 11, 30), Period.ofMonths(25), Period.of(4, 0, 0), Period.of(0, 0, 0)};
        for (LocalDate b : bases) for (Period p : pp) {
            out.add(j("dplus", b, p, b.plus(p), b.minus(p)));
        }
        // between
        LocalDate[] bs = {LocalDate.of(2020, 1, 31), LocalDate.of(2020, 3, 1), LocalDate.of(2019, 1, 15), LocalDate.of(2020, 2, 29),
                LocalDate.of(2021, 2, 28), LocalDate.of(2000, 12, 31), LocalDate.of(2023, 7, 4), LocalDate.of(-5, 6, 30), LocalDate.of(2020, 1, 1)};
        for (LocalDate a : bs) for (LocalDate b : bs) {
            out.add(j("between", a, b, Period.between(a, b), ChronoUnit.DAYS.between(a, b), ChronoUnit.WEEKS.between(a, b),
                    ChronoUnit.MONTHS.between(a, b), ChronoUnit.YEARS.between(a, b), ChronoUnit.DECADES.between(a, b)));
        }
        // LocalDateTime / LocalTime
        LocalDateTime[] ls = {LocalDateTime.of(2020, 1, 1, 10, 0), LocalDateTime.of(2020, 1, 2, 9, 59, 59, 999999999),
                LocalDateTime.of(2019, 12, 31, 23, 0, 0, 1), LocalDateTime.of(2020, 3, 1, 0, 0), LocalDateTime.of(1969, 12, 31, 23, 59, 59, 500000000)};
        for (LocalDateTime a : ls) for (LocalDateTime b : ls) {
            out.add(j("ldtbetween", a, b, Duration.between(a, b), ChronoUnit.HOURS.between(a, b), ChronoUnit.MILLIS.between(a, b),
                    ChronoUnit.DAYS.between(a, b), ChronoUnit.MONTHS.between(a, b)));
        }
        Duration[] durs = {Duration.ofHours(25), Duration.ofSeconds(-1, 1), Duration.ofDays(-400), Duration.ofNanos(86399999999999L), Duration.ofMinutes(-90)};
        for (LocalDateTime a : ls) for (Duration d : durs) {
            out.add(j("ldtplus", a, d, a.plus(d), a.minus(d), a.toLocalTime().plus(d), a.toLocalTime().minus(d)));
        }
        LocalTime[] ts = {LocalTime.of(10, 0), LocalTime.of(10, 0, 5), LocalTime.of(0, 0, 0, 1), LocalTime.of(23, 59, 59, 120000000),
                LocalTime.of(1, 2, 3, 456000), LocalTime.of(12, 0, 0, 100)};
        for (LocalTime t : ts) out.add(j("tstr", t.getHour(), t.getMinute(), t.getSecond(), t.getNano(), t));
        LocalDate[] ys = {LocalDate.of(5, 1, 1), LocalDate.of(-5, 1, 1), LocalDate.of(999, 1, 1), LocalDate.of(10000, 1, 1), LocalDate.of(-10000, 1, 1),
                LocalDate.of(0, 1, 1), LocalDate.MAX, LocalDate.MIN};
        for (LocalDate d : ys) out.add(j("datestr", d.getYear(), d.getMonthValue(), d.getDayOfMonth(), d));
        long[] ins = {0, -1, 1600000000, -62135596800L, 253402300800L, -377705116800L, 31556889864403199L, -31557014167219200L};
        int[] ino = {0, 1000000, 123456789, 500};
        for (long s : ins) for (int n : ino) {
            Instant i = Instant.ofEpochSecond(s, n);
            String em;
            try { em = String.valueOf(i.toEpochMilli()); } catch (Exception e) { em = "ERR"; }
            out.add(j("instant", s, n, i, em));
        }
        // ZoneId.of / ZoneOffset.of
        String[] zids = {"Z", "UTC", "GMT", "UT", "+09:00", "+9", "+09", "+0930", "+09:30:15", "+093015", "-18:00", "+18:00", "+18:01", "+19", "+24:00",
                "+09:60", "+9:00", "GMT+9", "GMT+09:00", "UTC-05:30", "UT+01", "UTC+0", "GMT-0", "UTC+", "GMTx", "Asia/Tokyo", "asia/tokyo",
                "America/Argentina/Buenos_Aires", "Nowhere/City", "1abc", "Asia/Tokyo/", "Etc/GMT+5", "../etc/passwd", "US/Eastern", "", "Z1", "+",
                "UTC+18:30", "Europe/Dublin", "EST5EDT", "WET", "Asia/Calcutta"};
        for (String z : zids) {
            String zr, zo;
            try { zr = ZoneId.of(z).getId() + "|" + ZoneId.of(z).getClass().getSimpleName(); } catch (Exception e) { zr = err(e); }
            try { zo = String.valueOf(ZoneOffset.of(z).getTotalSeconds()); } catch (Exception e) { zo = err(e); }
            out.add(j("zoneid", z, zr, zo));
        }
        // OffsetTime
        OffsetTime[] ots = {OffsetTime.of(23, 0, 0, 0, ZoneOffset.ofHours(-8)), OffsetTime.of(1, 30, 0, 5, ZoneOffset.ofHoursMinutes(5, 30)),
                OffsetTime.of(12, 0, 0, 0, ZoneOffset.UTC)};
        for (OffsetTime a : ots) for (OffsetTime b : ots) {
            out.add(j("ot", a, b, a.plusHours(5), a.minus(Duration.ofMinutes(90)), a.withOffsetSameInstant(b.getOffset()), Integer.signum(a.compareTo(b)),
                    Duration.between(a, b), a.until(b, ChronoUnit.MINUTES)));
        }
        // ZonedDateTime until / compare
        ZonedDateTime[] zs = {ZonedDateTime.of(2021, 3, 13, 12, 0, 0, 0, ZoneId.of("America/New_York")), ZonedDateTime.of(2021, 3, 14, 12, 0, 0, 0, ZoneId.of("America/New_York")),
                ZonedDateTime.of(2021, 3, 14, 12, 0, 0, 0, ZoneId.of("Asia/Tokyo")), ZonedDateTime.of(2021, 3, 14, 3, 0, 0, 0, ZoneOffset.UTC),
                ZonedDateTime.of(2021, 4, 14, 11, 59, 59, 999999999, ZoneId.of("America/New_York"))};
        for (ZonedDateTime a : zs) for (ZonedDateTime b : zs) {
            out.add(j("zuntil", a, b, a.until(b, ChronoUnit.HOURS), a.until(b, ChronoUnit.DAYS), a.until(b, ChronoUnit.MONTHS), Duration.between(a, b),
                    Integer.signum(a.compareTo(b)), a.isEqual(b)));
        }
        writeData("test/time/golden_amount_data.clay", "golden-amount-data",
                "kind TAB 入力 TAB 期待値 (種類ごとの列は golden_amount_test.clay を見る)", out);
    }

    // ---- DST ----
    static void dst() throws IOException {
        List<String> out = new ArrayList<>();
        String[] zones = {"America/New_York", "Europe/London", "Australia/Lord_Howe", "Asia/Tokyo", "Australia/Sydney", "Europe/Dublin",
                "America/Sao_Paulo", "Pacific/Chatham", "America/St_Johns", "Europe/Paris", "US/Eastern", "Pacific/Apia", "Asia/Kolkata",
                "America/Nuuk", "Asia/Jerusalem", "America/Santiago", "Antarctica/Troll", "Pacific/Norfolk", "Asia/Gaza", "America/Havana"};
        int[] years = {1850, 1918, 1945, 1970, 1987, 2000, 2011, 2020, 2021, 2024, 2037, 2038, 2050, 2100, 2300};
        for (String zid : zones) {
            ZoneId z = ZoneId.of(zid);
            ZoneRules rules = z.getRules();
            for (int y : years) {
                Instant start = LocalDate.of(y, 1, 1).atStartOfDay(ZoneOffset.UTC).toInstant().minusSeconds(1);
                Instant end = LocalDate.of(y + 1, 1, 1).atStartOfDay(ZoneOffset.UTC).toInstant();
                ZoneOffsetTransition tr = rules.nextTransition(start);
                int cnt = 0;
                while (tr != null && tr.getInstant().isBefore(end) && cnt < 4) {
                    cnt++;
                    LocalDateTime b = tr.getDateTimeBefore(), a = tr.getDateTimeAfter();
                    LocalDateTime[] probes = {b.minusHours(1), b.minusMinutes(1), b, b.plusMinutes(15), b.plusMinutes(30), b.plusMinutes(59),
                            a.minusMinutes(1), a, a.plusMinutes(1), b.plusHours(1)};
                    for (LocalDateTime p : probes) {
                        ZonedDateTime zdt = ZonedDateTime.of(p, z);
                        out.add(j("oflocal", zid, p, zdt, zdt.withEarlierOffsetAtOverlap(), zdt.withLaterOffsetAtOverlap()));
                        out.add(j("plus", zdt, zdt.plusDays(1), zdt.plusHours(1), zdt.plusMinutes(-30), zdt.plus(Period.ofMonths(1)),
                                zdt.minusDays(1), zdt.plus(Duration.ofHours(24))));
                    }
                    long ts = tr.getInstant().getEpochSecond();
                    for (long d : new long[]{-3601, -1, 0, 1, 1800, 3600}) {
                        ZonedDateTime zi = ZonedDateTime.ofInstant(Instant.ofEpochSecond(ts + d), z);
                        out.add(j("ofinstant", zid, ts + d, zi, rules.isDaylightSavings(zi.toInstant()), rules.getStandardOffset(zi.toInstant()).getTotalSeconds()));
                    }
                    tr = rules.nextTransition(tr.getInstant());
                }
            }
            Random r = new Random(zid.hashCode());
            for (int i = 0; i < 40; i++) {
                long s = (long) (r.nextDouble() * 8000000000L) - 3000000000L;
                ZonedDateTime zi = ZonedDateTime.ofInstant(Instant.ofEpochSecond(s), z);
                out.add(j("ofinstant", zid, s, zi, rules.isDaylightSavings(zi.toInstant()), rules.getStandardOffset(zi.toInstant()).getTotalSeconds()));
            }
            ZonedDateTime base = ZonedDateTime.of(2021, 6, 30, 12, 0, 0, 0, z);
            for (String other : new String[]{"UTC", "Asia/Tokyo", "America/New_York", "+05:30", "Z", "GMT+9"}) {
                out.add(j("same", base, other, base.withZoneSameInstant(ZoneId.of(other)), base.withZoneSameLocal(ZoneId.of(other))));
            }
        }
        writeData("test/time/golden_dst_data.clay", "golden-dst-data",
                "oflocal zone ldt zdt earlier later / plus zdt +1d +1h -30m +P1M -1d +PT24H / ofinstant zone epochSec zdt dst stdOffset / same zdt zone sameInstant sameLocal", out);
    }

    // ---- format ----
    static final String[] PATTERNS = {
        "yyyy-MM-dd", "uuuu-MM-dd'T'HH:mm:ss.SSSXXX", "y", "yy", "yyy", "yyyy", "yyyyy", "u", "uu", "uuu", "uuuuu", "Y", "YY", "YYYY", "YYYYY",
        "G", "GG", "GGG", "GGGG", "GGGGG", "GGGGGG", "M", "MM", "MMM", "MMMM", "MMMMM", "MMMMMM", "L", "LL", "LLL", "LLLL", "LLLLL",
        "d", "dd", "ddd", "D", "DD", "DDD", "DDDD", "Q", "QQ", "QQQ", "QQQQ", "QQQQQ", "q", "qq", "qqq", "qqqq", "qqqqq",
        "w", "ww", "www", "W", "WW", "E", "EE", "EEE", "EEEE", "EEEEE", "EEEEEE", "e", "ee", "eee", "eeee", "eeeee", "c", "cc", "ccc", "cccc", "ccccc",
        "F", "FF", "a", "aa", "h", "hh", "hhh", "K", "KK", "k", "kk", "H", "HH", "HHH", "m", "mm", "s", "ss", "S", "SS", "SSS", "SSSS", "SSSSSS", "SSSSSSSSS",
        "SSSSSSSSSS", "A", "AAAA", "n", "nn", "nnnnnnnnn", "N", "NNNNNNNNNNNNNNN", "V", "VV", "VVV", "z", "zz", "zzz", "zzzz", "zzzzz",
        "O", "OO", "OOOO", "Z", "ZZ", "ZZZ", "ZZZZ", "ZZZZZ", "ZZZZZZ", "X", "XX", "XXX", "XXXX", "XXXXX", "XXXXXX", "x", "xx", "xxx", "xxxx", "xxxxx",
        "'at' HH 'o''clock'", "''", "'", "'abc", "[yyyy][MM]", "yyyy[-MM[-dd]]", "HH[:mm[:ss[.SSS]]]", "[z]", "yyyy]", "#", "{", "}", "b", "t", "ppH", "pppd", "pd",
        "yyyyMMdd", "HHmmss", "yyyyMMddHHmmssSSS", "EEE, dd MMM yyyy HH:mm:ss zzz", "EEEE, MMMM d, yyyy h:mm a", "dd/MM/yy", "MMM d yyyy hh:mm:ss a z",
        "yyyy-MM-dd'T'HH:mm:ssZ", "YYYY-'W'ww-e", "uuuu-DDD", "h 'o''clock' a, zzzz", "G yyyy", "Q qqq QQQQ", "K:mm a", "k:mm", "x xx xxx",
        "yyyy-MM-dd HH:mm:ss.SSSSSS VV", "!@$%^&*()_+-=,./;<>?", "hh:mm a (VV)", "[[yyyy]]", "d MMMM uuuu G", "B",
        "v", "vv", "vvvv", "g", "gg", "ggggg", "BBBB", "BBBBB", "BB"
    };

    static List<Temporal> fmtValues() {
        List<Temporal> v = new ArrayList<>();
        v.add(ZonedDateTime.of(2020, 1, 5, 0, 0, 0, 0, ZoneId.of("America/New_York")));
        v.add(ZonedDateTime.of(2021, 7, 4, 13, 5, 9, 123456789, ZoneId.of("Europe/London")));
        v.add(ZonedDateTime.of(2019, 12, 30, 23, 59, 59, 0, ZoneId.of("Asia/Tokyo")));
        v.add(ZonedDateTime.of(-44, 3, 15, 12, 0, 0, 0, ZoneOffset.UTC));
        v.add(ZonedDateTime.of(12345, 6, 7, 8, 9, 10, 5000000, ZoneOffset.ofHoursMinutes(5, 30)));
        v.add(ZonedDateTime.of(1, 1, 1, 0, 0, 0, 0, ZoneId.of("UTC")));
        v.add(ZonedDateTime.of(2023, 1, 1, 12, 30, 0, 500000000, ZoneId.of("Australia/Lord_Howe")));
        v.add(ZonedDateTime.of(2021, 10, 31, 1, 30, 0, 0, ZoneId.of("Europe/Dublin")));
        v.add(ZonedDateTime.of(2021, 3, 14, 12, 0, 0, 0, ZoneOffset.ofHoursMinutesSeconds(-3, -30, -15)));
        v.add(ZonedDateTime.of(2020, 12, 31, 12, 0, 0, 0, ZoneId.of("GMT+9")));
        v.add(LocalDate.of(2020, 1, 5));
        v.add(LocalTime.of(0, 7, 9, 10));
        v.add(LocalDateTime.of(1999, 12, 31, 12, 0));
        v.add(OffsetTime.of(23, 0, 0, 0, ZoneOffset.ofHours(-8)));
        return v;
    }

    static final String[] WORLD = {"America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "America/Anchorage",
        "Pacific/Honolulu", "America/Sao_Paulo", "America/Argentina/Buenos_Aires", "America/Mexico_City", "America/Toronto", "America/Halifax",
        "America/St_Johns", "Europe/London", "Europe/Dublin", "Europe/Paris", "Europe/Berlin", "Europe/Moscow", "Europe/Istanbul", "Africa/Cairo",
        "Africa/Johannesburg", "Africa/Lagos", "Asia/Dubai", "Asia/Kolkata", "Asia/Kathmandu", "Asia/Shanghai", "Asia/Hong_Kong", "Asia/Singapore",
        "Asia/Tokyo", "Asia/Seoul", "Australia/Sydney", "Australia/Adelaide", "Australia/Perth", "Australia/Lord_Howe", "Pacific/Auckland",
        "Pacific/Chatham", "Pacific/Kiritimati", "Atlantic/Azores", "UTC", "Etc/GMT-14", "Asia/Tehran"};

    static List<ZonedDateTime> worldValues() {
        List<ZonedDateTime> v = new ArrayList<>();
        Random r = new Random(1234);
        for (int i = 0; i < 160; i++) {
            long s = (long) (r.nextDouble() * 3500000000L) - 600000000L;
            int ns = r.nextInt(4) == 0 ? 0 : r.nextInt(1000000000);
            v.add(ZonedDateTime.ofInstant(Instant.ofEpochSecond(s, ns), ZoneId.of(WORLD[i % WORLD.length])));
        }
        return v;
    }

    static final String[] WORLD_PATTERNS = {"yyyy-MM-dd HH:mm:ss z", "zzzz", "yyyy-MM-dd HH:mm v", "vvvv", "g", "EEE, d MMM yyyy HH:mm:ss Z", "yyyy-MM-dd'T'HH:mm:ss.SSSXXX'['VV']'",
        "O", "YYYY-'W'ww-e", "G y QQQ W F D", "EEE MMM dd HH:mm:ss zzz yyyy", "yyyy-MM-dd'T'HH:mm:ss.SSSSSSSSSx", "h:mm:ss.SSS a, MMMM d, uuuu (zzzz)"};

    static String kind(Temporal t) {
        if (t instanceof ZonedDateTime) return "Z";
        if (t instanceof LocalDate) return "D";
        if (t instanceof LocalTime) return "T";
        if (t instanceof LocalDateTime) return "L";
        return "O";
    }

    static void fmt() throws IOException {
        List<String> out = new ArrayList<>();
        for (String p : PATTERNS) {
            DateTimeFormatter f;
            try {
                f = DateTimeFormatter.ofPattern(p, L);
            } catch (Exception e) {
                out.add(j("Z", "2020-01-05T00:00-05:00[America/New_York]", p, err(e)));
                continue;
            }
            for (Temporal t : fmtValues()) {
                String r;
                try { r = f.format(t); } catch (Exception e) { r = err(e); }
                out.add(j(kind(t), t.toString(), p, r));
            }
        }
        for (String p : WORLD_PATTERNS) {
            DateTimeFormatter f = DateTimeFormatter.ofPattern(p, L);
            for (ZonedDateTime z : worldValues()) {
                String r;
                try { r = f.format(z); } catch (Exception e) { r = err(e); }
                out.add(j("Z", z.toString(), p, r));
            }
        }
        writeData("test/time/golden_fmt_data.clay", "golden-fmt-data", "kind value pattern result (kind: Z D T L O)", out);
    }

    // ---- parse ----
    static String parseOne(String p, String text) {
        DateTimeFormatter f;
        try { f = DateTimeFormatter.ofPattern(p, L); } catch (Exception e) { return err(e); }
        TemporalAccessor ta;
        try { ta = f.parse(text); } catch (Exception e) { return err(e); }
        LocalDate d = ta.query(TemporalQueries.localDate());
        LocalTime t = ta.query(TemporalQueries.localTime());
        String z;
        try { z = ZonedDateTime.from(ta).toString(); } catch (Exception e) { z = "-"; }
        ZoneId zi = ta.query(TemporalQueries.zone());
        return "D=" + (d == null ? "-" : d) + ";T=" + (t == null ? "-" : t) + ";Z=" + z + ";ZONE=" + (zi == null ? "-" : zi.getId());
    }

    static void parse() throws IOException {
        List<String> out = new ArrayList<>();
        LinkedHashSet<String> seen = new LinkedHashSet<>();
        // 往復: format の結果をそのまま parse する
        for (String p : PATTERNS) {
            DateTimeFormatter f;
            try { f = DateTimeFormatter.ofPattern(p, L); } catch (Exception e) { continue; }
            for (Temporal t : fmtValues()) {
                if (!(t instanceof ZonedDateTime)) continue;
                String text;
                try { text = f.format(t); } catch (Exception e) { continue; }
                if (seen.add(p + "\t" + text)) out.add(j(p, text, parseOne(p, text)));
            }
        }
        for (String p : WORLD_PATTERNS) {
            DateTimeFormatter f = DateTimeFormatter.ofPattern(p, L);
            for (ZonedDateTime z : worldValues()) {
                String text = f.format(z);
                if (seen.add(p + "\t" + text)) out.add(j(p, text, parseOne(p, text)));
            }
        }
        String[][] cases = {
            {"yyyy-MM-dd", "2021-02-30"}, {"yyyy-MM-dd", "2021-02-32"}, {"yyyy-MM-dd", "2021-13-01"}, {"yyyy-MM-dd", "2020-02-30"},
            {"yyyy-MM-dd", "2021-04-31"}, {"uuuu-MM-dd", "2021-02-29"}, {"yyyy-MM-dd", "0000-01-01"}, {"uuuu-MM-dd", "0000-01-01"},
            {"yyyy-MM-dd", "20210-01-01"}, {"yyyy-MM-dd", "+20210-01-01"}, {"uuuu-MM-dd", "-0001-01-01"}, {"yyyy-MM-dd", "21-01-01"},
            {"yyyy-MM-dd", "2021-1-01"}, {"yyyy-M-d", "2021-1-1"}, {"yyyy-M-d", "2021-12-31"}, {"yyyy-M-d", "2021-123-1"},
            {"HH:mm", "24:00"}, {"HH:mm:ss", "24:00:00"}, {"HH:mm:ss", "24:00:01"}, {"yyyy-MM-dd HH:mm", "2021-12-31 24:00"},
            {"HH:mm", "23:60"}, {"HH", "10"}, {"HH:mm", "10:00"}, {"h:mm a", "12:00 AM"}, {"h:mm a", "12:00 PM"}, {"h:mm a", "0:30 AM"},
            {"h:mm a", "13:00 PM"}, {"h:mm", "10:00"}, {"hh:mm a", "07:15 pm"}, {"K:mm a", "0:15 PM"}, {"k:mm", "24:00"}, {"k:mm", "0:00"},
            {"HH:mm a", "14:00 AM"}, {"HH:mm a", "14:00 PM"}, {"mm:ss", "10:20"}, {"ss", "10"}, {"HH:mm:ss.SSS", "10:00:00.12"},
            {"HH:mm:ss.SSS", "10:00:00.1"}, {"HH:mm:ss.SSS", "10:00:00.1234"}, {"HHmmssSSS", "100000123"}, {"yyyyMMdd", "20210315"},
            {"yyyyMMdd", "120210315"}, {"yyyyMMdd", "2021031"}, {"yyyyMMddHHmm", "202103151030"}, {"yyMMdd", "210315"}, {"yy", "99"},
            {"yy-MM-dd", "69-01-01"}, {"yy-MM-dd", "1969-01-01"}, {"y-MM-dd", "69-01-01"}, {"u-MM-dd", "69-01-01"}, {"yyy-MM-dd", "069-01-01"},
            {"EEE, dd MMM yyyy", "Fri, 05 Mar 2021"}, {"EEE, dd MMM yyyy", "Sat, 05 Mar 2021"}, {"EEEE MMMM d yyyy", "Friday March 5 2021"},
            {"EEE MMM d yyyy", "fri mar 5 2021"}, {"MMM d yyyy", "Sept 5 2021"}, {"MMMMM d yyyy", "J 5 2021"}, {"LLLL yyyy", "March 2021"},
            {"MMMM yyyy", "March 2021"}, {"yyyy-MM", "2021-03"}, {"yyyy", "2021"}, {"MM-dd", "03-05"}, {"yyyy-DDD", "2021-060"},
            {"yyyy-DDD", "2021-366"}, {"yyyy-DDD", "2020-366"}, {"yyyy-MM-dd DDD", "2021-03-01 060"}, {"yyyy-MM-dd DDD", "2021-03-01 061"},
            {"YYYY-ww-e", "2021-01-1"}, {"YYYY-ww-e", "2021-53-7"}, {"YYYY-ww-e", "2020-53-7"}, {"YYYY-ww", "2021-10"}, {"YYYY-'W'ww-e", "2020-W01-2"},
            {"yyyy-MM-W-e", "2021-03-2-4"}, {"yyyy-MM-W-E", "2021-03-2-Wed"}, {"yyyy-MM-dd e", "2021-03-05 6"}, {"yyyy-MM-dd c", "2021-03-05 6"},
            {"yyyy-MM-dd eee", "2021-03-05 Fri"}, {"G yyyy-MM-dd", "BC 0044-03-15"}, {"G yyyy-MM-dd", "AD 2021-03-15"},
            {"GGGG y-MM-dd", "Before Christ 44-03-15"}, {"yyyy-MM-dd G", "2021-03-15 A"}, {"Q yyyy", "3 2021"}, {"QQQ yyyy", "Q3 2021"},
            {"yyyy-MM-dd QQQ", "2021-08-01 Q3"}, {"yyyy-MM-dd QQQ", "2021-08-01 Q2"}, {"yyyy-MM-dd HH:mm XXX", "2021-03-15 10:00 +09:00"},
            {"yyyy-MM-dd HH:mm XXX", "2021-03-15 10:00 Z"}, {"yyyy-MM-dd HH:mm XXX", "2021-03-15 10:00 +0900"}, {"yyyy-MM-dd HH:mm X", "2021-03-15 10:00 +09"},
            {"yyyy-MM-dd HH:mm X", "2021-03-15 10:00 +0930"}, {"yyyy-MM-dd HH:mm x", "2021-03-15 10:00 +00"}, {"yyyy-MM-dd HH:mm Z", "2021-03-15 10:00 -0500"},
            {"yyyy-MM-dd HH:mm Z", "2021-03-15 10:00 +0000"}, {"yyyy-MM-dd HH:mm ZZZZ", "2021-03-15 10:00 GMT+09:00"}, {"yyyy-MM-dd HH:mm ZZZZ", "2021-03-15 10:00 GMT"},
            {"yyyy-MM-dd HH:mm O", "2021-03-15 10:00 GMT+9"}, {"yyyy-MM-dd HH:mm O", "2021-03-15 10:00 GMT-3:30"}, {"yyyy-MM-dd HH:mm OOOO", "2021-03-15 10:00 GMT+09:00"},
            {"yyyy-MM-dd HH:mm ZZZZZ", "2021-03-15 10:00 +09:00:30"}, {"yyyy-MM-dd HH:mm XXXXX", "2021-03-15 10:00 -05:00"},
            {"yyyy-MM-dd HH:mm VV", "2021-03-15 10:00 Asia/Tokyo"}, {"yyyy-MM-dd HH:mm VV", "2021-03-15 10:00 America/Argentina/Buenos_Aires"},
            {"yyyy-MM-dd HH:mm VV", "2021-03-15 10:00 UTC"}, {"yyyy-MM-dd HH:mm VV", "2021-03-15 10:00 Z"}, {"yyyy-MM-dd HH:mm VV", "2021-03-15 10:00 +05:30"},
            {"yyyy-MM-dd HH:mm VV", "2021-03-15 10:00 GMT+9"}, {"yyyy-MM-dd HH:mm VV", "2021-03-15 10:00 Nowhere/City"}, {"yyyy-MM-dd HH:mm VV", "2021-03-15 10:00 US/Eastern"},
            {"yyyy-MM-dd HH:mm z", "2021-03-15 10:00 EST"}, {"yyyy-MM-dd HH:mm z", "2021-07-15 10:00 EDT"}, {"yyyy-MM-dd HH:mm z", "2021-03-15 10:00 JST"},
            {"yyyy-MM-dd HH:mm z", "2021-03-15 10:00 PST"}, {"yyyy-MM-dd HH:mm z", "2021-03-15 10:00 UTC"}, {"yyyy-MM-dd HH:mm z", "2021-03-15 10:00 GMT"},
            {"yyyy-MM-dd HH:mm zzzz", "2021-03-15 10:00 Eastern Standard Time"}, {"yyyy-MM-dd HH:mm zzzz", "2021-03-15 10:00 Japan Standard Time"},
            {"yyyy-MM-dd HH:mm z", "2021-03-15 10:00 Asia/Tokyo"}, {"yyyy-MM-dd HH:mm z", "2021-03-15 10:00 BST"},
            {"yyyy-MM-dd HH:mm VV", "2021-03-14 02:30 America/New_York"}, {"yyyy-MM-dd HH:mm VV", "2021-11-07 01:30 America/New_York"},
            {"yyyy-MM-dd HH:mm XXX VV", "2021-11-07 01:30 -05:00 America/New_York"}, {"yyyy-MM-dd HH:mm XXX VV", "2021-11-07 01:30 +09:00 America/New_York"},
            {"yyyy-MM-dd'T'HH:mm:ss", "2021-03-15T10:00:00"}, {"yyyy-MM-dd'T'HH:mm:ss", "2021-03-15t10:00:00"}, {"yyyy-MM-dd'T'HH:mm:ss", "2021-03-15T10:00:00Z"},
            {"yyyy-MM-dd[ HH:mm]", "2021-03-15"}, {"yyyy-MM-dd[ HH:mm]", "2021-03-15 10:30"}, {"yyyy-MM-dd[ HH:mm]", "2021-03-15 10"},
            {"[yyyy-MM-dd][dd/MM/yyyy]", "15/03/2021"}, {"[yyyy-MM-dd][dd/MM/yyyy]", "2021-03-15"}, {"yyyy-MM-dd[[ HH]:mm]", "2021-03-15 10:30"},
            {"'Date:' yyyy-MM-dd", "Date: 2021-03-15"}, {"'Date:' yyyy-MM-dd", "date: 2021-03-15"}, {"yyyy''MM", "2021'03"}, {"ppd/MM/yyyy", " 5/03/2021"},
            {"ppd/MM/yyyy", "5/03/2021"}, {"ppd/MM/yyyy", "15/03/2021"}, {"A", "3600000"}, {"N", "3600000000001"}, {"n", "123"}, {"HH:mm:ss n", "10:00:00 5"},
            {"yyyy-MM-dd HH:mm:ss A", "2021-03-15 01:00:00 3600000"}, {"yyyy-MM-dd HH:mm:ss A", "2021-03-15 01:00:00 3600001"}, {"yyyy-MM-dd", "2021-03-15 extra"},
            {"yyyy-MM-dd", ""}, {"yyyy-MM-dd", "abcd-ef-gh"}, {"yyyy-MM-dd", "-2021-03-15"}, {"yyyy-MM-dd", "+2021-03-15"}, {"uuuu-MM-dd", "+2021-03-15"},
            {"uuuu-MM-dd", "-0000-03-15"}, {"MMM", "Mar"}, {"EEE", "Mon"}, {"a", "PM"}, {"yyyy MM dd HH mm ss", "2021 03 15 25 00 00"},
            {"dd.MM.yyyy HH:mm", "31.12.1999 23:59"}, {"d MMM uuuu", "1 Jan 2000"}, {"d MMM uuuu", "1 JAN 2000"}, {"yyyy-MM-dd HH:mm:ss.SSSSSSSSS", "2021-03-15 10:00:00.123456789"},
            {"yyyy-MM-dd HH:mm:ss.nnnnnnnnn", "2021-03-15 10:00:00.000000001"}, {"yyyy-MM-dd HH.mm.ss", "2021-03-15 10.00.00"}, {"yyyyMMddHHmmss", "20210315100000"},
            {"yyyyMMddHHmmssSSS", "20210315100000123"}, {"uuuuMMdd", "20210315"}, {"MMddyyyy", "03152021"}, {"ddMMyy", "150321"}, {"HHmm", "1030"},
            {"yyyy-MM-dd'T'HH:mm:ss.SSSZ", "2021-03-15T10:00:00.000+0900"}, {"MM/dd/yyyy", "3/15/2021"}, {"M/d/yyyy", "3/15/2021"}, {"dd-MMM-yyyy", "15-Mar-2021"},
            {"dd-MMM-yyyy", "15-MAR-2021"}, {"EEE MMM dd HH:mm:ss zzz yyyy", "Mon Mar 15 10:00:00 JST 2021"}, {"EEE MMM dd HH:mm:ss zzz yyyy", "Mon Mar 15 10:00:00 CET 2021"},
            {"EEE MMM dd HH:mm:ss zzz yyyy", "Mon Mar 15 10:00:00 IST 2021"}, {"EEE MMM dd HH:mm:ss zzz yyyy", "Sun Jul 04 10:00:00 BST 2021"},
            {"yyyy-MM-dd HH:mm z", "2021-03-15 10:00 CST"}, {"yyyy-MM-dd HH:mm z", "2021-03-15 10:00 America/Chicago"}, {"yyyy-MM-dd HH:mm zzzz", "2021-03-15 10:00 Central European Standard Time"},
            {"yyyy-MM-dd HH:mm zzzz", "2021-03-15 10:00 GMT+09:00"}, {"yyyy-MM-dd HH:mm z", "2021-03-15 10:00 GMT+9"}, {"yyyy-MM-dd HH:mm z", "2021-03-15 10:00 UTC+01:00"},
            {"yyyy-MM-dd HH:mm VV", "2021-03-15 10:00 UTC+01:00"}, {"yyyy-MM-dd HH:mm VV", "2021-03-15 10:00 UT"}, {"yyyy-MM-dd HH:mm VV", "2021-03-15 10:00 GMT0"},
            {"yyyy-MM-dd HH:mm VV", "2021-03-15 10:00 Europe/Paris"}, {"yyyy-MM-dd HH:mm VV", "2021-03-15 10:00 Asia/Calcutta"}, {"yyyy-MM-dd HH:mm VV", "2021-03-15 10:00 Etc/GMT+5"},
            {"yyyy-MM-dd HH:mm VV", "2021-03-15 10:00 Asia/Tokyoo"}, {"yyyy-MM-dd HH:mm VVX", "2021-03-15 10:00 Asia/TokyoZ"}, {"yyyy-MM-dd HH:mm VV", "2021-03-15 10:00 -05:00"},
            {"yyyy-MM-dd HH:mm VV", "2021-03-15 10:00 +9"}, {"uuuu-MM-dd HH:mm:ss.SSS", "2021-03-15 10:00:00.12"}, {"uuuu-MM-dd HH:mm:ss.SSS", "2021-03-15 10:00:00.12x"},
            {"yyyy-MM-dd HH:mm:ss.SSSSSS", "2021-03-15 10:00:00.000001"}, {"yyyy-MM-dd'T'HH:mm:ss[.SSS][XXX]", "2021-03-15T10:00:00"}, {"yyyy-MM-dd'T'HH:mm:ss[.SSS][XXX]", "2021-03-15T10:00:00.5+01:00"},
            {"yyyy-MM-dd'T'HH:mm:ss[.SSS][XXX]", "2021-03-15T10:00:00.500Z"}, {"yyyy-MM-dd[ ]['T']HH:mm", "2021-03-15T10:00"}, {"yyyy-MM-dd[ ]['T']HH:mm", "2021-03-15 10:00"},
            {"yyyy-MM-dd HH:mm:ss VV", "2021-03-14 02:30:00 America/New_York"}, {"yyyy-MM-dd HH:mm:ss VV", "2021-03-28 01:30:00 Europe/London"},
            {"yyyy-MM-dd HH:mm:ss VV", "2021-10-03 02:15:00 Australia/Lord_Howe"}, {"yyyy-MM-dd HH:mm:ss VV", "2021-04-04 01:45:00 Australia/Lord_Howe"},
            {"yyyy-MM-dd HH:mm:ss XXX VV", "2021-04-04 01:45:00 +10:30 Australia/Lord_Howe"}, {"yyyy-MM-dd HH:mm:ss XXX VV", "2021-04-04 01:45:00 +11:00 Australia/Lord_Howe"},
            {"yyyy/MM/dd HH:mm:ss", "2021/02/29 10:00:00"}, {"yyyy/MM/dd kk:mm", "2021/02/28 24:00"}, {"yyyy/MM/dd hh:mm", "2021/02/28 12:00"},
            {"yyyy/MM/dd hh:mm a", "2021/02/28 00:00 AM"}, {"yyyy/MM/dd KK:mm a", "2021/02/28 12:00 PM"}, {"yyyy-MM-dd'T'HH:mm:ss.SSSSSSSSSx", "2021-03-15T10:00:00.123456789+05"},
            {"G uuuu", "BC 0001"}, {"uuuu G", "0000 AD"}, {"y G", "1 BC"}, {"yyyy-MM-dd e", "2021-03-15 8"}, {"yyyy-MM-dd F", "2021-03-15 1"}, {"yyyy-MM-dd F", "2021-03-15 2"},
            {"YYYY-ww-eeee", "2021-11-Monday"}, {"YYYY-ww-EEE", "2021-11-Mon"}, {"YY-ww-e", "21-11-2"}, {"Y-w-e", "2021-1-1"},
            {"yyyy-MM-dd HH:mm:ss.SSS O", "2021-03-15 10:00:00.000 GMT+5:30"}, {"yyyy-MM-dd HH:mm:ss.SSS OOOO", "2021-03-15 10:00:00.000 GMT+05:30:15"},
            {"yyyy-MM-dd HH:mm:ss.SSS ZZZZZ", "2021-03-15 10:00:00.000 Z"}, {"yyyy-MM-dd HH:mm:ss.SSS xxxxx", "2021-03-15 10:00:00.000 +00:00"},
            {"yyyy-MM-dd HH:mm:ss.SSS X", "2021-03-15 10:00:00.000 +24"}, {"yyyy-MM-dd HH:mm:ss.SSS XXX", "2021-03-15 10:00:00.000 +18:30"},
            {"yyyy-MM-dd HH:mm", "2021-03-15 10:00　"}, {"yyyy年MM月dd日", "2021年03月15日"}, {"ppppyyyy-MM-dd", "2021-03-15"}, {"MMM", "May"}, {"MMMM", "May"},
        };
        for (String[] c : cases) out.add(j(c[0], c[1], parseOne(c[0], c[1])));
        // すべてのゾーン名と ID (z / zzzz / VV)
        TreeSet<String> shorts = new TreeSet<>(), longs = new TreeSet<>(), ids = new TreeSet<>(ZoneId.getAvailableZoneIds());
        for (String[] r : DateFormatSymbols.getInstance(L).getZoneStrings()) {
            if (r.length > 2) shorts.add(r[2]); if (r.length > 4) shorts.add(r[4]);
            if (r.length > 1) longs.add(r[1]); if (r.length > 3) longs.add(r[3]);
        }
        // SystemV/* は JDK の tzdb にだけあり、zoneinfo には無い (mulay はファイルシステムに従う)
        ids.removeIf(x -> x.startsWith("SystemV/"));
        for (String n : shorts) out.add(j("z", n, parseOne("z", n)));
        for (String n : ids) out.add(j("z", n, parseOne("z", n)));
        for (String n : longs) out.add(j("zzzz", n, parseOne("zzzz", n)));
        for (String n : ids) out.add(j("VV", n, parseOne("VV", n)));
        for (String n : new String[]{"UTC", "UTC+01:00", "UT", "GMT", "JST", "Asia/Tokyo", "Z", "+09:00"}) {
            out.add(j("z 'x'", n + " x", parseOne("z 'x'", n + " x")));
            out.add(j("VV 'x'", n + " x", parseOne("VV 'x'", n + " x")));
        }
        writeData("test/time/golden_parse_data.clay", "golden-parse-data", "pattern text result (D=date;T=time;Z=ZonedDateTime.from;ZONE=zone か ERR:message)", out);
    }
}
