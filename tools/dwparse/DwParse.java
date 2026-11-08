import org.mule.weave.v2.parser.MappingParser$;
import org.mule.weave.v2.sdk.ParsingContextFactory$;
import org.mule.weave.v2.sdk.WeaveResource$;
import org.mule.weave.v2.parser.phase.*;
import java.nio.file.*;
public class DwParse {
  static void dump(Object o, StringBuilder sb) {
    if (o instanceof scala.Product && !(o instanceof scala.Option && ((scala.Option)o).isEmpty())) {
      scala.Product p = (scala.Product) o;
      String name = p.productPrefix();
      if (o instanceof scala.Some) { dump(((scala.Some)o).get(), sb); return; }
      if (o instanceof scala.collection.Seq) { sb.append("["); scala.collection.Iterator it = ((scala.collection.Seq)o).iterator(); boolean f=true; while (it.hasNext()) { if(!f) sb.append(" "); f=false; dump(it.next(), sb);} sb.append("]"); return; }
      if (p.productArity() == 0) { sb.append(name); return; }
      if (name.equals("VariableReferenceNode") || name.equals("NameIdentifier")) { sb.append(p.productElement(0) instanceof String ? (String)p.productElement(0) : ""); if (!(p.productElement(0) instanceof String)) dump(p.productElement(0), sb); return; }
      sb.append("(").append(name);
      scala.collection.Iterator it = p.productIterator();
      while (it.hasNext()) { Object c = it.next(); if (c instanceof scala.collection.Seq && ((scala.collection.Seq)c).isEmpty() && !it.hasNext()) break; sb.append(" "); dump(c, sb); }
      sb.append(")");
    } else if (o instanceof scala.collection.Seq) {
      sb.append("["); scala.collection.Iterator it = ((scala.collection.Seq)o).iterator(); boolean f=true; while (it.hasNext()) { if(!f) sb.append(" "); f=false; dump(it.next(), sb);} sb.append("]");
    } else if (o instanceof scala.Option) { sb.append("None");
    } else if (o instanceof String) { sb.append('"').append(o).append('"');
    } else if (o != null && o.getClass().getName().startsWith("org.mule")) { sb.append(o.getClass().getSimpleName().replace("$","").replace("OpId",""));
    } else sb.append(String.valueOf(o));
  }
  static boolean module = false;
  static boolean json = false;
  static void js(String x, StringBuilder sb) {
    sb.append('"');
    for (int i = 0; i < x.length(); i++) { char c = x.charAt(i);
      if (c == '"' || c == '\\') sb.append('\\').append(c);
      else if (c < 32) sb.append(String.format("\\u%04x", (int)c));
      else sb.append(c); }
    sb.append('"');
  }
  static void jdump(Object o, StringBuilder sb) {
    if (o instanceof scala.Some) { jdump(((scala.Some)o).get(), sb); return; }
    if (o instanceof scala.Option) { sb.append("null"); return; }
    if (o instanceof scala.collection.Seq) { sb.append("["); scala.collection.Iterator it = ((scala.collection.Seq)o).iterator(); boolean f=true; while (it.hasNext()) { if(!f) sb.append(","); f=false; jdump(it.next(), sb);} sb.append("]"); return; }
    if (o instanceof String) { js((String)o, sb); return; }
    if (o instanceof Boolean || o instanceof Number) { sb.append(o); return; }
    if (o instanceof scala.Product && ((scala.Product)o).productArity() > 0) {
      scala.Product p = (scala.Product) o;
      sb.append("{\"t\":"); js(p.productPrefix(), sb);
      if (o instanceof org.mule.weave.v2.parser.ast.AstNode) {
        try { sb.append(",\"s\":").append(((org.mule.weave.v2.parser.ast.AstNode)o).location().startPosition().index()); } catch (Throwable e) {}
      }
      sb.append(",\"c\":[");
      scala.collection.Iterator it = p.productIterator(); boolean f = true;
      while (it.hasNext()) { if(!f) sb.append(","); f=false; jdump(it.next(), sb); }
      sb.append("]}"); return;
    }
    if (o == null) { sb.append("null"); return; }
    String n = o.getClass().getSimpleName().replace("$","");
    if (o instanceof scala.Product) n = ((scala.Product)o).productPrefix();
    sb.append("{\"t\":"); js(n, sb);
    if (o instanceof org.mule.weave.v2.parser.ast.AstNode) {
      try { sb.append(",\"s\":").append(((org.mule.weave.v2.parser.ast.AstNode)o).location().startPosition().index()); } catch (Throwable e) {}
    }
    sb.append(",\"c\":[]}");
  }
  public static void main(String[] a) throws Exception {
    if (a.length > 0 && a[0].equals("-files")) {
      // each stdin line: path ; prints "OK path" or "ERR path<TAB>msg"
      java.io.BufferedReader br = new java.io.BufferedReader(new java.io.InputStreamReader(System.in));
      String line;
      while ((line = br.readLine()) != null) {
        if (line.isEmpty()) continue;
        String src = new String(Files.readAllBytes(Paths.get(line)), "UTF-8");
        module = line.endsWith(".mod.dwl");
        String r = check(src);
        System.out.println((r == null ? "OK\t" : "ERR\t") + line + (r == null ? "" : "\t" + r));
      }
      return;
    }
    if (a.length > 0 && a[0].equals("-json")) {
      // stdin: records separated by a line "\u0001"; each record: first line = m or e, rest = source. prints one JSON per record
      json = true;
      String all = new String(System.in.readAllBytes(), "UTF-8");
      for (String rec : all.split("\u0001\n", -1)) {
        if (rec.isEmpty()) continue;
        int nl = rec.indexOf('\n');
        module = rec.substring(0, nl).equals("m");
        String src = rec.substring(nl + 1);
        StringBuilder sb = new StringBuilder();
        try {
          PhaseResult r = doParse(src);
          if (r.hasErrors()) { sb.append("{\"err\":"); js(check(src), sb); sb.append("}"); }
          else { sb.append("{\"ast\":"); jdump(((ParsingResult) r.getResult()).astNode(), sb); sb.append("}"); }
        } catch (Throwable e) { sb.append("{\"err\":"); js("EXC " + e, sb); sb.append("}"); }
        System.out.println(sb);
      }
      return;
    }
    if (a.length > 0 && a[0].equals("-m")) { module = true; a = java.util.Arrays.copyOfRange(a, 1, a.length); }
    String all = a.length > 0 ? new String(Files.readAllBytes(Paths.get(a[0]))) : new String(System.in.readAllBytes());
    for (String src : all.split("\n=====\n")) run(src);
  }
  static PhaseResult doParse(String src) {
    ParsingContext ctx = ParsingContextFactory$.MODULE$.createParsingContext(true);
    if (module) return org.mule.weave.v2.parser.ModuleParser$.MODULE$.parse(org.mule.weave.v2.parser.ModuleParser$.MODULE$.parsingPhase(), WeaveResource$.MODULE$.anonymous(src), ctx);
    return MappingParser$.MODULE$.parse(MappingParser$.MODULE$.parsingPhase(), WeaveResource$.MODULE$.anonymous(src), ctx);
  }
  static String check(String src) {
    try {
      PhaseResult r = doParse(src);
      if (r.hasErrors()) { scala.Tuple2 t = (scala.Tuple2) r.errorMessages().head(); return ((org.mule.weave.v2.parser.Message)t._2()).message().replace("\n"," ") + " @" + ((org.mule.weave.v2.parser.location.WeaveLocation)t._1()).startPosition(); }
      return null;
    } catch (Throwable e) { return "EXC " + e; }
  }
  static void run(String src) {
    PhaseResult r = doParse(src);
    if (r.hasErrors()) { scala.Tuple2 t = (scala.Tuple2) r.errorMessages().head(); System.out.println("ERR " + ((org.mule.weave.v2.parser.Message)t._2()).message().replace("\n"," ") + " @" + ((org.mule.weave.v2.parser.location.WeaveLocation)t._1()).startPosition()); return; }
    ParsingResult pr = (ParsingResult) r.getResult();
    StringBuilder sb = new StringBuilder(); dump(pr.astNode(), sb); System.out.println(sb);
  }
}
