// secure-properties の暗号化済みの値を、実モジュールのクラスで作る (期待値の元)。
//   MOD=~/.m2/repository/com/mulesoft/modules/mule-secure-configuration-property-module/1.2.5/*-mule-plugin.jar
//   ENC=~/srv/mule-enterprise-standalone-4.11.3/lib/opt/mule-encryption-1.9.3.jar
//   JAVA=/usr/lib/jvm/java-17-openjdk-amd64/bin
//   /usr/lib/jvm/java-17-openjdk-amd64/bin/java -cp "$MOD:$ENC" tools/gen-secure-golden.java <algorithm> <mode> <useRandomIVs> <key> <plain>...
// 出力: 1 行に 1 値、`![<base64>]`。
import com.mulesoft.modules.configuration.properties.api.EncryptionAlgorithm;
import com.mulesoft.modules.configuration.properties.api.EncryptionMode;
import org.mule.encryption.Encrypter;
import java.util.Base64;

public class GenSecureGolden {
  public static void main(String[] a) throws Exception {
    EncryptionAlgorithm alg = EncryptionAlgorithm.valueOf(a[0]);
    EncryptionMode mode = EncryptionMode.valueOf(a[1]);
    boolean rnd = Boolean.parseBoolean(a[2]);
    Encrypter e = alg.getBuilder().using(mode).forKey(a[3]).useRandomIVs(rnd).build();
    for (int i = 4; i < a.length; i++)
      System.out.println("![" + Base64.getEncoder().encodeToString(e.encrypt(a[i].getBytes())) + "]");
  }
}
