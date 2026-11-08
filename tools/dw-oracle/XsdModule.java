// 実 DW (xmlschema-module) が XSD から作る DataWeave のモジュールを書き出す。xmlschema! の golden を作る時の参照用。
// 使い方: tools/dw-oracle/xsd-module <クラスパスのディレクトリ> <モジュールの名前 (a::b::C)>
import org.mule.weave.v2.module.xmlschema.XmlSchemaModuleLoader;
import org.mule.weave.v2.parser.ast.variables.NameIdentifier;
import org.mule.weave.v2.parser.phase.ParsingContext;
import org.mule.weave.v2.sdk.ClassLoaderWeaveResourceResolver;
import org.mule.weave.v2.sdk.ParsingContextFactory;

public class XsdModule {
  public static void main(String[] args) throws Exception {
    XmlSchemaModuleLoader loader = new XmlSchemaModuleLoader();
    loader.resolver(ClassLoaderWeaveResourceResolver.apply());
    NameIdentifier id = NameIdentifier.apply(args[0], scala.Option.empty());
    ParsingContext ctx = ParsingContextFactory.createParsingContext(id);
    scala.Option<?> r = loader.loadModule(id, ctx);
    if (r.isEmpty()) { System.err.println("not found: " + args[0]); System.exit(1); }
    org.mule.weave.v2.parser.phase.PhaseResult<?> pr = (org.mule.weave.v2.parser.phase.PhaseResult<?>) r.get();
    if (!pr.hasResult()) { System.err.println(pr.messages()); System.exit(1); }
    org.mule.weave.v2.parser.phase.ParsingResult<?> res = (org.mule.weave.v2.parser.phase.ParsingResult<?>) pr.getResult();
    System.out.println(org.mule.weave.v2.codegen.CodeGenerator$.MODULE$.generate((org.mule.weave.v2.parser.ast.AstNode) res.astNode()));
  }
}
