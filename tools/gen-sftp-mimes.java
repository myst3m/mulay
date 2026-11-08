// mulay.conn.sftp_mimes を mule-sftp-connector 2.7.3 の MimeTypesRegistry (同梱の tika-mimetypes.xml) から作る。
//
//   M=~/srv/mule-enterprise-standalone-4.11.3
//   /usr/lib/jvm/java-17-openjdk-amd64/bin/java \
//     -cp ~/.m2/repository/org/mule/connectors/mule-sftp-connector/2.7.3/mule-sftp-connector-2.7.3-mule-plugin.jar:$M/lib/mule/mule-api-1.11.3.jar:$M/lib/boot/slf4j-api-2.0.17.jar \
//     tools/gen-sftp-mimes.java [mulay のルート]
//
// 出力: src/mulay/conn/sftp_mimes.clay。EXTS: 拡張子 (小文字) -> mime、NAMES: ファイル名 (小文字) -> mime。
// どちらも getNormalizedMimeType を通した値 (MimeTypeDetector が返すもの)。
import java.nio.file.*;
import java.util.*;

public class GenSftpMimes {
  static String q(String s) { return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\""; }

  public static void main(String[] args) throws Exception {
    String root = args.length > 0 ? args[0] : ".";
    Class<?> c = Class.forName("org.mule.extension.sftp.internal.util.MimeTypesRegistry");
    Object reg = c.getConstructor().newInstance();
    c.getMethod("initialise").invoke(reg);
    @SuppressWarnings("unchecked") Map<String, String> ext = (Map<String, String>) c.getMethod("getExtensionMap").invoke(reg);
    @SuppressWarnings("unchecked") Map<String, String> names = (Map<String, String>) c.getMethod("getFilenameMap").invoke(reg);
    java.lang.reflect.Method norm = c.getMethod("getNormalizedMimeType", String.class);
    StringBuilder sb = new StringBuilder();
    sb.append("(ns mulay.conn.sftp_mimes)\n\n");
    for (String[] part : new String[][] {{"EXTS", "e"}, {"NAMES", "n"}}) {
      Map<String, String> m = part[0].equals("EXTS") ? ext : names;
      if (part[0].equals("NAMES")) sb.append("\n");
      sb.append("(def " + part[0] + "\n  [");
      int k = 0;
      for (String key : new TreeSet<>(m.keySet())) {
        String v = (String) norm.invoke(reg, m.get(key));
        if (k++ > 0) sb.append("\n   ");
        sb.append("[" + q(key) + " " + q(v) + "]");
      }
      sb.append("])\n");
    }
    Files.writeString(Path.of(root, "src/mulay/conn/sftp_mimes.clay"), sb.toString());
    System.out.println("EXTS " + ext.size() + ", NAMES " + names.size());
  }
}
