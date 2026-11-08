import org.mule.runtime.extension.api.error.ErrorTypeDefinition;
public class E {
  public static void main(String[] a) throws Exception {
    Class<?> c = Class.forName(a[0]);
    for (Object o : c.getEnumConstants()) {
      ErrorTypeDefinition<?> d = (ErrorTypeDefinition<?>) o;
      String p = d.getParent().map(x -> (x instanceof Enum ? ((Enum<?>)x).getDeclaringClass().getSimpleName()+":" : "") + x.getType()).orElse("-");
      System.out.println(d.getType() + " " + p);
    }
  }
}
