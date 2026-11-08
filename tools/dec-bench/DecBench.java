import java.math.*;

public class DecBench {
  static final int N = 1000000;
  static String ps(int i) { return (1 + i % 997) + "." + (10 + i % 89); }
  static long ms(long t) { return (System.nanoTime() - t) / 1000000; }
  public static void main(String[] a) {
    BigDecimal[] p = new BigDecimal[1000];
    for (int i = 0; i < 1000; i++) p[i] = new BigDecimal(ps(i));
    BigDecimal t = new BigDecimal("1.08"), k = new BigDecimal("7");
    for (int r = 0; r < 6; r++) {
      long t0 = System.nanoTime(); BigDecimal s = BigDecimal.ZERO;
      for (int i = 0; i < N; i++) s = s.add(p[i % 1000]);
      long sum = ms(t0); t0 = System.nanoTime(); BigDecimal x = BigDecimal.ZERO;
      for (int i = 0; i < N; i++) x = x.add(p[i % 1000].multiply(t).setScale(2, RoundingMode.HALF_UP));
      long tax = ms(t0); t0 = System.nanoTime(); long n = 0;
      for (int i = 0; i < N; i++) n += new BigDecimal(ps(i)).toString().length();
      long text = ms(t0); t0 = System.nanoTime(); long f = 0;
      for (int i = 0; i < N; i++) f += p[i % 1000].divide(k, MathContext.DECIMAL128).precision();
      long div = ms(t0); t0 = System.nanoTime(); long g = 0;
      for (int i = 0; i < N; i++) g += p[i % 1000].compareTo(p[(i + 1) % 1000]);
      long cmp = ms(t0);
      if (r == 5) {
        System.out.println("sum  " + sum + " ms " + s);
        System.out.println("tax  " + tax + " ms " + x);
        System.out.println("text " + text + " ms " + n);
        System.out.println("div  " + div + " ms " + f);
        System.out.println("cmp  " + cmp + " ms " + g);
      }
    }
  }
}
