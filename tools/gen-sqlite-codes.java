// mulay.db.sqlite_codes を xerial sqlite-jdbc の org.sqlite.SQLiteErrorCode から作る。
//
//   /usr/lib/jvm/java-17-openjdk-amd64/bin/java -cp ~/.m2/repository/org/xerial/sqlite-jdbc/3.50.3.0/sqlite-jdbc-3.50.3.0.jar \
//     tools/gen-sqlite-codes.java [mulay のルート]
//
// 出力: src/mulay/db/sqlite_codes.clay。CODES: code (10 進の文字列) -> [名前 文言]。同じ code は最初のもの。

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.sqlite.SQLiteErrorCode;

public class GenSqliteCodes {
    public static void main(String[] args) throws Exception {
        Path root = Paths.get(args.length > 0 ? args[0] : ".").toAbsolutePath().normalize();
        Map<Integer, SQLiteErrorCode> first = new LinkedHashMap<>();
        for (SQLiteErrorCode c : SQLiteErrorCode.values()) first.putIfAbsent(c.code, c);
        StringBuilder b = new StringBuilder();
        b.append("(ns mulay.db.sqlite_codes)\n\n");
        b.append("(def CODES: Map(Str Vec(Str))\n  {");
        boolean f = true;
        for (SQLiteErrorCode c : first.values()) {
            if (!f) b.append("\n   ");
            f = false;
            b.append('"').append(c.code).append("\" [").append(lit(c.name())).append(' ').append(lit(c.message)).append(']');
        }
        b.append("})\n");
        Files.write(root.resolve("src/mulay/db/sqlite_codes.clay"), b.toString().getBytes(StandardCharsets.UTF_8));
    }

    static String lit(String s) { return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\""; }
}
