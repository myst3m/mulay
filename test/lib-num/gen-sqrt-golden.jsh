// decimalSqrt の golden (test/lib-num/math_sqrt_data.clay の元データ sqrt.tsv) を Java 17 で作る:
//   /usr/lib/jvm/java-17-openjdk-amd64/bin/jshell -q test/lib-num/gen-sqrt-golden.jsh  (カレントに sqrt.tsv ができる)
import java.math.*; import java.util.*;
Random r = new Random(7); StringBuilder sb = new StringBuilder();
for (int i=0;i<400;i++){ BigDecimal x = new BigDecimal(new BigInteger(1+r.nextInt(40), r).add(BigInteger.ONE), r.nextInt(30)-10); int p = r.nextInt(40); RoundingMode m = RoundingMode.values()[r.nextInt(7)]; String out; try { out = x.sqrt(new MathContext(p, m)).toString(); } catch (ArithmeticException e) { out = "ERR:" + e.getMessage(); } sb.append(x+"\t"+p+"\t"+m.ordinal()+"\t"+out+"\n"); }
for (String s : new String[]{"4","1E+10","0.0001","6.25","100","1.21","15241578750190521","0.01","1E-10","2.25","0"}) for (int p : new int[]{0,5,34}) { BigDecimal x = new BigDecimal(s); String out; try { out = x.sqrt(new MathContext(p, RoundingMode.HALF_EVEN)).toString(); } catch (ArithmeticException e) { out = "ERR:" + e.getMessage(); } sb.append(x+"\t"+p+"\t6\t"+out+"\n"); }
java.nio.file.Files.writeString(java.nio.file.Path.of("sqrt.tsv"), sb.toString());
/exit
