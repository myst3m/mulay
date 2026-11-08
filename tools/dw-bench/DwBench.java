import org.mule.weave.v2.runtime.*;
import java.nio.file.*;
import java.util.*;

public class DwBench {
  public static void main(String[] a) throws Exception {
    String text = new String(Files.readAllBytes(Paths.get(a[0])), "UTF-8");
    byte[] input = a[1].isEmpty() ? null : Files.readAllBytes(Paths.get(a[1]));
    int n = Integer.parseInt(a[2]);
    String script = text.substring(text.indexOf('\n') + 1);
    int e = script.indexOf("\n%%% ");
    if (e >= 0) script = script.substring(0, e);
    DataWeaveScriptingEngine eng = new DataWeaveScriptingEngine();
    String[] names = input == null ? new String[0] : new String[]{"payload"};
    DataWeaveScript ds = eng.compile(script, names);
    long[] ts = new long[n];
    for (int i = 0; i < n; i++) {
      ScriptingBindings b = new ScriptingBindings();
      if (input != null) b.addBinding("payload", new java.io.ByteArrayInputStream(input), "application/json", new HashMap<>());
      long t = System.nanoTime();
      String out = ds.write(b).getContentAsString();
      ts[i] = System.nanoTime() - t;
      if (out.length() < 0) System.out.print("");
    }
    long[] warm = Arrays.copyOfRange(ts, Math.min(3, n - 1), n);
    Arrays.sort(warm);
    System.out.println("bench median " + warm[warm.length / 2] / 1000000 + " ms, min " + warm[0] / 1000000 + " ms (" + warm.length + " warm runs)");
  }
}
