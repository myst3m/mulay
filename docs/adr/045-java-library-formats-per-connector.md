# 045 — 実コネクタが使う Java のライブラリの読み書きを、コネクタごとに写す

状態: **採用** (2026-09-29 lib/jhash と Salesforce から。以後のコネクタも同じ)

## 決定
- 実コネクタが中で使う Java のライブラリの書き方・読み方・失敗の文言を、そのコネクタの ns に小さく写して持つ。共通の JSON の
  読み書き (DW の writer) では代えない。
  - A2A (`a2a_spec`): a2a-java-sdk 0.3.3 の型として Jackson 2.17.0 で読み直して書き出す。キーは @JsonCreator の引数の順、
    値の無いものは書かない (NON_ABSENT)、知らないキーは捨てる、失敗は Jackson の例外の文言 (位置と参照の連鎖)。
  - Anypoint MQ (`amq_wire`): Gson 2.12 の JsonWriter (htmlSafe) と lenient な JsonReader、java.util.Base64 の decoder、
    URLEncoder。
  - Salesforce Composite (`sf_cjson`): Jackson 2.22 の ObjectMapper の既定 (LinkedHashMap・ArrayList・Integer / Long /
    BigInteger / Double、最上位の HashMap)。
  - Vectors: org.json (JSONObject.numberToString、JSONObject.quote) と、保存先のファイルは Jackson。
  - MCP・Inference: Jackson の空白なしの書き出し (`mcp/compact`)。
  - WSC: CXF が使う Woodstox の文字データと属性のエスケープ、名前空間の宣言の置き方。
- Java の HashMap に入れたものの並びは、HashMap の反復順 (容量と桶) を lib/jhash で再現する。`new HashMap<>(m)` の容量
  (size / 0.75 + 1) のように、どの生成子で作ったかまで写す。
- 期待値は実物の Java で作る生成器 (tools/gen-a2a-golden.java、tools/gen-amq-golden.java) で作り、単体テストで比べる。
- 実コネクタの表 (Salesforce のメタデータの型、SFTP の mime) は生成物として持ち、手で編集しない:
  `sf_metatypes` は tools/gen-sf-metatypes.py (force-metadata-api 65.0.0 と mule-salesforce-connector 11.3.4)、
  `sftp_mimes` は tools/gen-sftp-mimes.java (mule-sftp-connector 2.7.3 の tika-mimetypes.xml)。

## 理由
- 実 Mule の結果 (キーの並び、エスケープ、数の書き方、失敗の文言) は、コネクタが中で使う Java のライブラリで決まり、
  ライブラリと版がコネクタごとに違う。実 Mule の記録と文字列で比べるので、ライブラリごとに写す。
- HashMap の順は同じ桶の中では入れた順になるので、入れる順と容量を写さないと並びが合わない。

## 場所
- `mulay.conn.a2a_spec`、`mulay.conn.amq_wire`、`mulay.conn.sf_cjson`、`mulay.conn.vectors`、`mulay.conn.mcp/compact`、
  `mulay.conn.wsc` (`esc-text`、`decls-of`)
- `mulay.lib.jhash` (使う側: `amq_wire`、`a2a`、`db`、`salesforce`、`sf_core`、`sf_cjson`、`vectors`、`wsc`)
- `mulay.conn.sf_metatypes`、`mulay.conn.sftp_mimes`
