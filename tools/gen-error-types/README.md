# エラー型の親子関係の抽出

Mule のコネクタのエラー型 (ErrorTypeDefinition の enum) の親を、実物の jar から取り出す。
`src/mulay/rt/error.clay` の表はこの出力から書いている (推測で親を決めない)。

```bash
M=~/srv/mule-enterprise-standalone-4.11.3
CP="<コネクタの mule-plugin.jar>:$(ls $M/lib/mule/*.jar $M/lib/opt/*.jar | tr '\n' ':')"
javac --release 17 -cp "$CP" E.java && java -cp "$CP:." E org.mule.extension.http.api.error.HttpError
java -cp "$CP:." E org.mule.runtime.extension.api.error.MuleErrors
```

出力は「型 親」。親が `-` のものは ANY の直下 (CRITICAL を除く)。
