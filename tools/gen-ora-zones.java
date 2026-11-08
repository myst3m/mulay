// mulay.db.ora_zones を ojdbc11 の oracle.sql.ZONEIDMAP から作る。
//
//   /usr/lib/jvm/java-17-openjdk-amd64/bin/java -cp ~/.m2/repository/com/oracle/database/jdbc/ojdbc11/23.8.0.25.04/ojdbc11-23.8.0.25.04.jar \
//     tools/gen-ora-zones.java [mulay のルート]
//
// 出力: src/mulay/db/ora_zones.clay。ZONES: 地域の番号 -> 地域の名前 (TIMESTAMP WITH TIME ZONE の地域の時間帯。
// ojdbc の TIMESTAMPTZ が timeZone に出す名前)。

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import oracle.sql.ZONEIDMAP;

public class GenOraZones {
    public static void main(String[] args) throws Exception {
        Path root = Paths.get(args.length > 0 ? args[0] : ".").toAbsolutePath().normalize();
        StringBuilder b = new StringBuilder();
        b.append("(ns mulay.db.ora_zones)\n\n");
        b.append("(def ZONES: Map(Str Str)\n  {");
        boolean first = true;
        for (int i = 0; i < 8192; i++) {
            if (!ZONEIDMAP.isValidID(i)) continue;
            if (!first) b.append("\n   ");
            first = false;
            b.append("\"").append(i).append("\" \"").append(ZONEIDMAP.getRegion(i)).append("\"");
        }
        b.append("})\n");
        Files.write(root.resolve("src/mulay/db/ora_zones.clay"), b.toString().getBytes(StandardCharsets.UTF_8));
    }
}
