// 実 Mule と同じ sqlite-jdbc (同梱の SQLite 3.50.3) で式を評価し、値と格納型を 1 行ずつ出す (純 Clay の SQLite の差分テストの基準)。
// 入力: 1 行に 1 つの式 (SQL の式)。出力: 1 行に 1 つ、N / I:10 進 / R:double のビット (16 桁の 16 進) / T:UTF-8 の 16 進 /
// B:16 進 / E:SQLite の errmsg。
// 使い方: tools/sqlite-oracle/sqlite-oracle < exprs.txt、tools/sqlite-oracle/sqlite-oracle prepare < stmts.txt (構文だけ)
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.sql.*;
import java.util.*;

public class SqliteOracle {
    static String hex(byte[] b) {
        StringBuilder sb = new StringBuilder();
        for (byte x : b) sb.append(String.format("%02x", x & 255));
        return sb.toString();
    }
    // xerial の文言 "[SQLITE_ERROR] SQL error or missing database (msg)" から SQLite の errmsg を取り出す
    static String errmsg(SQLException e) {
        String m = e.getMessage();
        int i = m.indexOf(" (");
        if (m.startsWith("[") && i >= 0 && m.endsWith(")")) return m.substring(i + 2, m.length() - 1);
        return m;
    }
    public static void main(String[] args) throws Exception {
        Connection c = DriverManager.getConnection("jdbc:sqlite::memory:");
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
        PrintStream out = new PrintStream(new BufferedOutputStream(System.out), false, "UTF-8");
        String line;
        // prepare: 文を準備するだけ。構文の誤り (near .. / incomplete input / unrecognized token) なら E:、他は OK
        if (args.length > 0 && args[0].equals("prepare")) {
            while ((line = in.readLine()) != null) {
                try (PreparedStatement ps = c.prepareStatement(line)) {
                    out.println("OK");
                } catch (SQLException e) {
                    String m = errmsg(e);
                    out.println(m.startsWith("near ") || m.equals("incomplete input") || m.startsWith("unrecognized token") ? "E:" + m : "OK");
                }
            }
            out.flush();
            return;
        }
        // script: 1 行に 1 つの文を同じ接続で順に実行する。"----" の行で新しいメモリの DB に替える。出力は文ごとに 1 行:
        // 問い合わせは Q:列の名前|..|;行の値 (値は上と同じ形、空白で区切る);.. 、他は C:changes():last_insert_rowid()、
        // 失敗は E:拡張結果コード:errmsg
        if (args.length > 0 && args[0].equals("script")) {
            org.sqlite.SQLiteConfig cfg = new org.sqlite.SQLiteConfig();
            while ((line = in.readLine()) != null) {
                if (line.equals("----")) { c.close(); c = DriverManager.getConnection("jdbc:sqlite::memory:"); out.println("----"); continue; }
                try (Statement s = c.createStatement()) {
                    boolean q = s.execute(line);
                    if (q) {
                        ResultSet r = s.getResultSet();
                        ResultSetMetaData md = r.getMetaData();
                        int n = md.getColumnCount();
                        StringBuilder sb = new StringBuilder("Q:");
                        for (int i = 1; i <= n; i++) sb.append(md.getColumnLabel(i)).append("|");
                        while (r.next()) {
                            sb.append(";");
                            for (int i = 1; i <= n; i++) {
                                Object o = r.getObject(i);
                                if (i > 1) sb.append(" ");
                                if (o == null) sb.append("N");
                                else if (o instanceof Integer || o instanceof Long) sb.append("I:").append(((Number) o).longValue());
                                else if (o instanceof Double) sb.append(String.format("R:%016x", Double.doubleToRawLongBits((Double) o)));
                                else if (o instanceof String) sb.append("T:").append(hex(((String) o).getBytes(StandardCharsets.UTF_8)));
                                else sb.append("B:").append(hex((byte[]) o));
                            }
                        }
                        r.close();
                        out.println(sb);
                    } else {
                        try (Statement s2 = c.createStatement(); ResultSet r2 = s2.executeQuery("SELECT changes(), last_insert_rowid()")) {
                            r2.next();
                            out.println("C:" + r2.getLong(1) + ":" + r2.getLong(2));
                        }
                    }
                } catch (SQLException e) {
                    int code = (e instanceof org.sqlite.SQLiteException) ? ((org.sqlite.SQLiteException) e).getResultCode().code : e.getErrorCode();
                    out.println("E:" + code + ":" + errmsg(e));
                }
            }
            out.flush();
            return;
        }
        while ((line = in.readLine()) != null) {
            // 失敗の文言は式だけの SELECT で取る (包んだ形だと構文の誤りの位置が変わる)
            try (Statement s0 = c.createStatement(); ResultSet r0 = s0.executeQuery("SELECT " + line)) {
                r0.next();
            } catch (SQLException e) {
                out.println("E:" + errmsg(e));
                continue;
            }
            try (Statement s = c.createStatement();
                 ResultSet r = s.executeQuery("SELECT typeof(v), v FROM (SELECT " + line + " AS v)")) {
                r.next();
                String t = r.getString(1);
                switch (t) {
                    case "null": out.println("N"); break;
                    case "integer": out.println("I:" + r.getLong(2)); break;
                    case "real": out.println(String.format("R:%016x", Double.doubleToRawLongBits(r.getDouble(2)))); break;
                    case "text": out.println("T:" + hex(r.getBytes(2))); break;
                    default: out.println("B:" + hex(r.getBytes(2)));
                }
            } catch (SQLException e) {
                out.println("E:" + errmsg(e));
            }
        }
        out.flush();
    }
}
