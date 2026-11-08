// test/dec/dtoa_long_data.clay の期待値を作る: Java 17 の Double.toString。
//   /usr/lib/jvm/java-17-openjdk-amd64/bin/java tools/gen-dtoa-long-golden.java
import java.util.*;
public class GenDtoaLong { public static void main(String[] a) {
  List<Double> xs = new ArrayList<>();
  long[] ls = {-446744073709551616L, 9007199254740992L, 9007199254740993L, 18014398509481988L, 36028797018963972L, 72057594037927944L, 144115188075855888L, 288230376151711776L, 576460752303423552L, 1152921504606846976L, 4611686018427387904L, 9223372036854775807L, -9223372036854775807L-1, 123456789012345678L, 987654321098765432L, -446744073709551616L, 1L<<62, (1L<<62)+(1L<<10), 5000000000000000000L, 999999999999999999L};
  for (long l : ls) xs.add((double) l);
  Random r = new Random(42);
  for (int i = 0; i < 40; i++) { long l = r.nextLong(); xs.add((double) l); xs.add((double)(l >>> (r.nextInt(11)))); }
  xs.add(1e20); xs.add(9.2233720368547758E18); xs.add(1.8446744073709552E19);
  for (double x : xs) System.out.println("[\"" + Double.doubleToRawLongBits(x) + "\" \"" + Double.toString(x) + "\"]");
}}
