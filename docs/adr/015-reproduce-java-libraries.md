# 015 — Mule が使う Java のライブラリの判定と文言は、版を決めてその手順を写し、生成した期待値で照合する

状態: **採用** (2026-09-29〜2026-10-10。各 ns の最初のコミット: x509 9244a85・keystore 0a32129 (09-29)、logfile efa6f81・secure e0be9d2 (10-08)、
validate 75fb925・textsplit d61e255・wsdl 0228c8b (10-10))

## 決定

実 Mule の結果はコネクタやモジュールが使う Java のライブラリで決まるので、ライブラリと版を決め、その手順を写す。

- `mulay.lib.validate` (Validation モジュール): commons-validator 1.10.1 の EmailValidator / DomainValidator (getInstance(false)) /
  InetAddressValidator、Guava 33.6 の InetAddresses.isInetAddress、`new java.net.URL(s)` が例外を投げないか (JDK 17 の既定のプロトコル)、
  java.net.IDN.toASCII。正は tools/gen-validation-golden.java の出力 (test/validate/golden_test.clay)。commons-validator の正規表現は定数を
  そのまま使う。Java の String の長さが要る所は UTF-16 の単位で数える (`utf16-len`)。
  - TLD の表 `mulay.lib.tlds` は生成物 (tools/gen-tlds.java、Java 17.0.21-ea。DomainValidator.isValidTld が受ける 1444 個)。
  - IDN の nameprep は簡略にする (違いは docs/compat/deviations.md)。
- `mulay.lib.textsplit` (Vectors の transform-chunk-text): langchain4j 1.1.0 の DocumentSplitters.recursive(max, overlap)。大きさは Java の
  String.length (UTF-16 の単位)。文の切り分けは OpenNLP の学習済みモデルの代わりに規則で近似する (docs/compat/deviations.md)。
- `mulay.lib.wsdl` (Web Service Consumer 2.2.2): mule-wsdl-parser 1.4.11 (wsdl4j) と同じものを取り出す。失敗は "<例外の単純名>: <文言>"。
  import の失敗は最初の文書の文言で報告する (wsdl4j は import を親の文書の失敗として報告する)。読めない import は、実物 (CXF の
  URIResolver) と同じく NullPointerException にする (実物の不具合だが写す)。XML の誤りの文言は Xerces の SAXParseException の形に直す。
- `mulay.lib.logfile` (jmx モジュールの log-file 操作): 実モジュールの LogFileReader と同じ結果にする。`search` は一致が max*2 件を
  超えるたびに最後の max 件に縮める (実モジュールと同じ)。そのため max が負だと 1 件目で範囲外の失敗 ("fromIndex(a) > toIndex(b)") になる。
- `mulay.lib.keystore`: JKS (sun.security.provider.JavaKeyStore と KeyProtector) を読む。失敗の文言は Java の例外と同じ。
- `mulay.lib.secure` (secure-properties、mule-secure-configuration-property-module 1.2.5 と mule-encryption 1.9.3): useRandomIVs が false なら
  鍵の先頭 16 バイトを IV にするなど、実モジュールの方式に合わせる。失敗は実モジュールの文言。AES 以外は未対応 (docs/compat/deviations.md)。
- `mulay.lib.x509`: java.security.cert.X509Certificate が返す値にする。DN の文字列は X500Name.toString と同じ (RDN を DER と逆の順に ", "
  でつなぐ)。知らない OID は "OID.1.2.3=#hex" ではなく "1.2.3=値" にする (値が文字列でなければ #hex)。
- `mulay.lib.glob`: java.nio.file.FileSystem#getPathMatcher("glob:..") の構文。壊れたパターン (閉じない `[` や `{`) はどの文字列にも一致しない。
  入れ子の `{` (Java では "Cannot nest groups" の誤り) も一致しない。照合は、パターンを命令の列 (`{..}` は分岐) に
  直し、すべての状態を 1 文字ずつ同時に進める (Thompson の NFA)。時間はパターンの長さ × 文字列の長さで済む。
  前は `*` ごとに戻って探し、`*a*a*a..b` のようなパターンで指数時間になっていた (2026-10-25、敵対的レビュー)。

## 理由

- 正しさの基準は実 Mule の挙動 (CLAUDE.md)。それを決めているのは各ライブラリの振る舞い。

## 場所

- `mulay.lib.validate/email?`、`domain?`、`tld?`、`inet?`、`inet-address?`、`url?`、`idn-ascii`、`utf16-len`、`mulay.lib.tlds`
- `mulay.lib.textsplit/recursive`、`sentences`
- `mulay.lib.wsdl/parse`、`mulay.lib.logfile/search`、`tail`、`mulay.lib.keystore/read-jks`、`mulay.lib.secure/decrypt-bytes`、
  `mulay.lib.x509/parse-der`、`mulay.lib.glob/glob-match`
