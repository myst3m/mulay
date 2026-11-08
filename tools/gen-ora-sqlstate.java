// mulay.db.ora_sqlstate を ojdbc11 の oracle.jdbc.driver.SQLStateMapping から作る。
//
//   /usr/lib/jvm/java-17-openjdk-amd64/bin/java -cp ~/.m2/repository/com/oracle/database/jdbc/ojdbc11/23.8.0.25.04/ojdbc11-23.8.0.25.04.jar \
//     tools/gen-ora-sqlstate.java [mulay のルート]
//
// 出力: src/mulay/db/ora_sqlstate.clay。RANGES: [low high SQLState 例外の class] の並び (ojdbc が ORA 番号から
// SQLException を作るときに引く表。先に並ぶものが優先)。どれにも入らない番号の既定も DEFAULT に書く。

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.sql.SQLException;
import oracle.jdbc.driver.SQLStateMapping;

public class GenOraSqlstate {
    public static void main(String[] args) throws Exception {
        Path root = Paths.get(args.length > 0 ? args[0] : ".").toAbsolutePath().normalize();
        SQLStateMapping[] all = SQLStateMapping.getMappings();
        StringBuilder b = new StringBuilder();
        b.append("(ns mulay.db.ora_sqlstate)\n\n");
        b.append("(def RANGES\n  [");
        int n = 0;
        for (SQLStateMapping m : all) {
            java.lang.reflect.Field hf = SQLStateMapping.class.getDeclaredField("high");
            hf.setAccessible(true);
            int high = hf.getInt(m);
            SQLException e = m.newSQLException("x", m.low);
            if (n > 0) b.append("\n   ");
            b.append("[\"").append(m.low).append("\" \"").append(high).append("\" \"").append(m.sqlState)
             .append("\" \"").append(e.getClass().getName()).append("\"]");
            n++;
        }
        b.append("])\n\n");
        SQLStateMapping d = null;
        java.lang.reflect.Field df = SQLStateMapping.class.getDeclaredField("DEFAULT_SQLSTATE");
        df.setAccessible(true);
        d = (SQLStateMapping) df.get(null);
        b.append("(def DEFAULT [\"").append(d.sqlState).append("\" \"").append(d.newSQLException("x", 0).getClass().getName()).append("\"])\n");
        Files.write(root.resolve("src/mulay/db/ora_sqlstate.clay"), b.toString().getBytes(StandardCharsets.UTF_8));
        System.out.println("ranges: " + n);
    }
}
