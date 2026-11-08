// Generates src/mulay/lib/tlds.clay: the top-level domains that commons-validator 1.10.1
// DomainValidator.getInstance(false).isValidTld accepts (infrastructure, generic and country-code TLDs,
// the default overrides applied). mulay.lib.validate uses it for EmailValidator (is-email、Validation::isEmail).
// Run:
//   CV=~/.m2/repository/commons-validator/commons-validator/1.10.1/commons-validator-1.10.1.jar
//   /usr/lib/jvm/java-17-openjdk-amd64/bin/java -cp "$CV" tools/gen-tlds.java > src/mulay/lib/tlds.clay
import java.lang.reflect.Field;
import java.util.*;
import org.apache.commons.validator.routines.DomainValidator;

public class GenTlds {
    public static void main(String[] args) throws Exception {
        TreeSet<String> all = new TreeSet<>();
        for (String f : new String[] {"INFRASTRUCTURE_TLDS", "GENERIC_TLDS", "COUNTRY_CODE_TLDS", "LOCAL_TLDS"}) {
            Field fl = DomainValidator.class.getDeclaredField(f);
            fl.setAccessible(true);
            all.addAll(Arrays.asList((String[]) fl.get(null)));
        }
        DomainValidator dv = DomainValidator.getInstance(false);
        List<String> ok = new ArrayList<>();
        for (String t : all) {
            if (!t.equals(t.toLowerCase(Locale.ENGLISH))) throw new IllegalStateException("not lower case: " + t);
            if (dv.isValidTld(t)) ok.add(t);
        }
        StringBuilder out = new StringBuilder();
        out.append("(ns mulay.lib.tlds)\n\n");
        out.append("(def TLDS\n  [");
        int col = 3;
        for (int i = 0; i < ok.size(); i++) {
            String s = "\"" + ok.get(i) + "\"";
            if (col + s.length() + 1 > 120) { out.append("\n   "); col = 3; }
            else if (i > 0) { out.append(" "); col++; }
            out.append(s);
            col += s.length();
        }
        out.append("])\n");
        System.out.print(out);
    }
}
