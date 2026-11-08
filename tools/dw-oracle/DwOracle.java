// mulay の正しさの基準 (実 Mule の DataWeave) で .dwt フィクスチャを評価する。
//
//   java -cp <weave jars>:. DwOracle fill  <file.dwt>...   期待出力 (%%% output / %%% error) を実 DW の結果で書き直す
//   java -cp <weave jars>:. DwOracle check <file.dwt>...   食い違いを報告 (終了コード 1)
//   java -cp <weave jars>:. DwOracle eval  <file.dwt>      結果を標準出力へ
//
// .dwt の形式 (docs/fixtures.md):
//   %%% script                          DW スクリプト本文
//   %%% input <name> <mime> [k=v ...]   入力 (0 個以上)。本文がそのまま中身
//   %%% output <mime>                   期待出力 (成功時)
//   %%% error                           期待エラー (失敗時。本文は実 DW のメッセージ 1 行目)
//   %%% note                            自由記述 (評価には使わない)
//   %%% mask                            各行が正規表現。check で期待と結果の一致部分 (グループ 1 があればそこ) を *** にして比べる
//   %%% env                             各行が NAME=VALUE。環境変数をちょうどこれだけにした子の JVM で評価する
//   %%% sysprops                        各行が NAME=VALUE。評価の間だけ Java のシステムプロパティにする (dw::Runtime::prop が読む)
//   %%% variants <n>                    fill で n 回評価し、出た結果をすべて期待にする。check はどれかに一致すれば良い
import org.mule.weave.v2.runtime.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

public class DwOracle {
  static final String MARK = "%%% ";

  static final class Section { String head; StringBuilder body = new StringBuilder(); }

  static List<Section> parse(String text) {
    List<Section> out = new ArrayList<>();
    Section cur = null;
    if (text.endsWith("\n")) text = text.substring(0, text.length() - 1);
    for (String line : text.split("\n", -1)) {
      if (line.startsWith(MARK)) { cur = new Section(); cur.head = line.substring(MARK.length()).trim(); out.add(cur); }
      else if (cur != null) cur.body.append(line).append('\n');
    }
    return out;
  }

  // 本文の末尾改行は 1 つだけ区切りとして扱う
  static String body(Section s) {
    String b = s.body.toString();
    return b.endsWith("\n") ? b.substring(0, b.length() - 1) : b;
  }

  static String render(List<Section> secs) {
    StringBuilder sb = new StringBuilder();
    for (Section s : secs) { sb.append(MARK).append(s.head).append('\n').append(body(s)).append('\n'); }
    return sb.toString();
  }

  static final DataWeaveScriptingEngine ENGINE = new DataWeaveScriptingEngine();

  // 戻り値: {"output", mime, content} か {"error", "", message}
  static String[] eval(List<Section> secs) {
    Section sp = find(secs, "sysprops");
    List<String> setKeys = new ArrayList<>();
    if (sp != null) for (String kv : body(sp).split("\n")) { int eq = kv.indexOf('='); if (eq > 0) { System.setProperty(kv.substring(0, eq), kv.substring(eq + 1)); setKeys.add(kv.substring(0, eq)); } }
    try { return eval0(secs); } finally { for (String k : setKeys) System.clearProperty(k); }
  }

  static String[] eval0(List<Section> secs) {
    String script = null;
    ScriptingBindings b = new ScriptingBindings();
    List<String> names = new ArrayList<>();
    for (Section s : secs) {
      String[] h = s.head.split("\\s+");
      if (h[0].equals("script")) script = body(s);
      else if (h[0].equals("input")) {
        Map<String, Object> props = new HashMap<>();
        for (int i = 3; i < h.length; i++) { int eq = h[i].indexOf('='); props.put(h[i].substring(0, eq), h[i].substring(eq + 1)); }
        byte[] content = body(s).getBytes(StandardCharsets.UTF_8);
        b.addBinding(h[1], new java.io.ByteArrayInputStream(content), h[2], props);
        names.add(h[1]);
      }
    }
    try {
      DataWeaveScript ds = ENGINE.compile(script, names.toArray(new String[0]));
      DataWeaveResult r = ds.write(b);
      return new String[]{"output", r.getMimeType(), r.getContentAsString()};
    } catch (Throwable t) {
      String m = String.valueOf(t.getMessage());
      int nl = m.indexOf('\n');
      // fill / check は 1 行目だけ比べる。eval は全文を出す (r[3])
      return new String[]{"error", "", nl >= 0 ? m.substring(0, nl) : m, m};
    }
  }

  static boolean isExpect(Section s) { return s.head.startsWith("output") || s.head.equals("error"); }

  static Section find(List<Section> secs, String head) {
    for (Section s : secs) if (s.head.equals(head) || s.head.startsWith(head + " ")) return s;
    return null;
  }

  static String mask(String s, List<Section> secs) {
    Section m = find(secs, "mask");
    if (m == null) return s;
    for (String re : body(m).split("\n")) {
      if (re.isEmpty()) continue;
      java.util.regex.Matcher mt = java.util.regex.Pattern.compile(re).matcher(s);
      StringBuilder out = new StringBuilder(); int pos = 0;
      while (mt.find()) {
        int g = (mt.groupCount() > 0 && mt.start(1) >= 0) ? 1 : 0;
        if (mt.start(g) < pos) continue;
        out.append(s, pos, mt.start(g)).append("***"); pos = mt.end(g);
      }
      out.append(s.substring(pos)); s = out.toString();
    }
    return s;
  }

  // %%% env があれば、環境変数をちょうどそれだけにした子の JVM で評価する (raw の出力を読む)
  static String[] evalIn(List<Section> secs, Path p) throws Exception {
    Section env = find(secs, "env");
    if (env == null) return eval(secs);
    ProcessBuilder pb = new ProcessBuilder(Paths.get(System.getProperty("java.home"), "bin", "java").toString(),
        "-cp", System.getProperty("java.class.path"), "DwOracle", "raw", p.toString());
    pb.environment().clear();
    for (String kv : body(env).split("\n")) { int eq = kv.indexOf('='); if (eq > 0) pb.environment().put(kv.substring(0, eq), kv.substring(eq + 1)); }
    pb.redirectErrorStream(false);
    Process pr = pb.start();
    String out = new String(pr.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
    pr.waitFor();
    int nl = out.indexOf('\n');
    String[] h = out.substring(0, nl).split(" ", 2);
    String rest = out.substring(nl + 1);
    if (rest.endsWith("\n")) rest = rest.substring(0, rest.length() - 1);
    return new String[]{h[0], h.length > 1 ? h[1] : "", rest, rest};
  }

  public static void main(String[] args) throws Exception {
    // Mule のランタイムは起動時に既定のタイムゾーンを決める (user.timezone が入る)。DW 単体の JVM も同じにする
    java.util.TimeZone.getDefault();
    String mode = args[0];
    int bad = 0;
    for (int i = 1; i < args.length; i++) {
      Path p = Paths.get(args[i]);
      List<Section> secs = parse(Files.readString(p));
      if (mode.equals("raw")) {   // 子の JVM (evalIn) から: 1 行目に種類と mime、続けて本文
        String[] r = eval(secs);
        System.out.println(r[0] + " " + r[1]); System.out.println(r[2]); continue;
      }
      String[] r = evalIn(secs, p);
      if (mode.equals("eval")) { System.out.println(r[0] + " " + r[1]); System.out.println(r.length > 3 ? r[3] : r[2]); continue; }
      Section vs = find(secs, "variants");
      int runs = vs == null ? 1 : Integer.parseInt(vs.head.split("\\s+")[1]);
      List<Section> gots = new ArrayList<>();
      for (int k = 0; k < runs; k++) {
        String[] rk = k == 0 ? r : evalIn(secs, p);
        Section got = new Section();
        got.head = rk[0].equals("output") ? "output " + rk[1] : "error";
        got.body.append(rk[2]).append('\n');
        boolean dup = false;
        for (Section g : gots) if (g.head.equals(got.head) && body(g).equals(body(got))) dup = true;
        if (!dup) gots.add(got);
      }
      if (mode.equals("fill")) {
        List<Section> keep = new ArrayList<>();
        for (Section s : secs) if (!isExpect(s)) keep.add(s);
        keep.addAll(gots);
        Files.writeString(p, render(keep));
      } else {
        Section got = gots.get(0);
        boolean same = false;
        for (Section want : secs) if (isExpect(want) && want.head.equals(got.head) && mask(body(want), secs).equals(mask(body(got), secs))) same = true;
        if (!same) { bad++; System.out.println("DIFF " + p + "\n  got:  " + got.head + "\n" + body(got)); }
      }
    }
    if (bad > 0) { System.out.println(bad + " differ"); System.exit(1); }
  }
}
