# 068 — MySQL のドライバは mysql-connector-j 9.2 の既定の設定と同じに振る舞う

状態: **採用** (2026-10-10、51588ca)

## 決定
- 既定の設定として次を前提にする (docs/connectors.md の「MySQL」に書いていないもの):
  - `tinyInt1isBit` と `yearIsDateType` は既定の true (TINYINT(1) は Boolean、YEAR は java.sql.Date)。
  - `connectionTimeZone=LOCAL`: 時間帯付きの日時のパラメータは実行環境の既定の地域の時刻にする。
  - `useAffectedRows=false` なのでクライアントの能力に FOUND_ROWS を立てる。`allowMultiQueries=false`。
  - 文字列のパラメータ (日時のリテラルも) は `_utf8mb4 X'<16 進>'` にする (2026-10-25 から)。前は `\` と `'` を
    逃がして `'..'` に埋めていたが、接続の文字コードが SJIS・GBK・Big5 (アプリの `SET NAMES` など) だと、
    `0x95 0x5c 0x27` のように逃がした `\` が前のバイトと 1 文字になって `'` が閉じ、SQL を注入できた
    (敵対的レビューで実 MySQL 8.4 に対して確かめた)。sql_mode が NO_BACKSLASH_ESCAPES だと `\` が 2 つになって
    値が変わる不具合もあった。16 進の文字列は接続の文字コードと sql_mode によらず同じ値になる。文字コードを書いた
    リテラルの coercibility は普通の文字列と同じ 4 で、数値・日時の文脈でも普通の文字列と同じく変換される
    (`1 = _utf8mb4 X'31'` は真、`DATE(_utf8mb4 X'..')` も通る。照合順序の違う列と比べても失敗しない)。
  - LocalDateTime のリテラルは小数部の末尾の 0 を削る (Connector/J の LocalDateTime の書き方)。
- `{call p(..)}` は `CALL p(..)` にする (Connector/J の escape の処理)。
- execute-script で結果セットを返す文かどうかは Connector/J の QueryInfo と同じく、注釈と空白を飛ばした最初の語と、
  その前に `(` があったかで決める。
- 通信の失敗は CommunicationsException (SQLState 08S01)。Data truncation (1406、1264) の SQLState は 22001。
- bulk と execute-script は接続が切れたらそこで止める (他の失敗では残りを送る)。
- 生成したキーは、サーバーの返す LAST_INSERT_ID から affected rows の数だけ 1 ずつ増やして作る。affected rows が
  1,000,000 を超えるか、キーが Int の上限を超えるなら、キーを作らずに SQLException (HY000) にする
  (`the server reported <n> affected rows, but mulay returns at most 1000000 generated keys`、
  `the server reported generated keys past 9223372036854775807`)。Connector/J は数をそのまま使うので、嘘の数を返す
  サーバーや中間者がメモリを使い切らせることができた (2026-10-25、敵対的レビュー)。テストは test/db/mysql_keys_test。
- TLS (2026-11-08、公開前の安全性の見直し)。sslMode と旧い指定 (useSSL / requireSSL / verifyServerCertificate) は
  Connector/J の読み替えと同じ: sslMode が無ければ、useSSL=false は DISABLED、verifyServerCertificate=true は
  VERIFY_CA、requireSSL=true は REQUIRED、ほかは PREFERRED (useSSL=true だけなら PREFERRED のまま)。
  - PREFERRED と REQUIRED は Connector/J と同じく証明書を確かめない。caching_sha2_password の全部の認証はこの上で
    パスワードをそのまま送るので、中間者に読まれうる。docs/connectors.md で VERIFY_IDENTITY を勧める。
  - VERIFY_CA / VERIFY_IDENTITY は trustCertificateKeyStoreUrl (file: の URL だけ)・Type (既定 JKS)・Password の
    倉庫で確かめる。Java と同じく、JKS の型で PKCS12 のファイルも読み、JKS はパスワードが空なら完全性の検査を飛ばして
    信頼する証明書の項目だけを使う (lib/keystore の read-jks-certs)。倉庫が無ければ JVM の cacerts の代わりに clay.tls
    の OS の CA (SSL_CERT_FILE) で確かめる。fallbackToSystemTrustStore=false で倉庫が無ければ Connector/J と同じ失敗。
  - VERIFY_IDENTITY の名前は clay.tls と同じく subjectAltName だけと比べる。Connector/J は SAN が無ければ CN と比べる
    (deviations.md)。PKCS12 の倉庫を読めない時の [..] の中は clay の pkix の文言。
  - 倉庫を読めない失敗の文言は Connector/J の SSLParamsException (SQLState 08000) と同じ。証明書が通らなければ
    CommunicationsException (08S01) で、パスワードを送る前に止まる。
  - DISABLED と PREFERRED 以外でサーバーが SSL を持たなければ "SSL Connection required, but not provided by
    server." (08001)。前は REQUIRED だけが失敗し、VERIFY_* は入り口で断っていた。サーバーの能力の SSL の印を中間者が
    消すと平文に落ちる道を、確かめるモードで閉じる。
  - VERIFY_CA は鎖だけを確かめ、名前は確かめない (clay 0.115.0 の `tls/->VerifyCa`。Connector/J と同じく、MySQL が
    自動で作る SAN の無い証明書でもつながる)。VERIFY_IDENTITY は名前も確かめる (`tls/->VerifyFull`)。clay 0.114 までは
    鎖だけを確かめる指定が無く、VERIFY_CA も名前を確かめていた (断るより安全側に失敗する方を選んでいた)。
  - 期待値は Connector/J 9.2 を Java 17 で MySQL 8.4 (k0 の mulay-mysql) につないで確かめた。テストは
    test/db/mysql_ssl_test (指定の読み方) と test/mytls (偽のサーバーとの TLS とパスワードの送り先)。
- サーバーから読むパケットは、0xffffff バイトのパケットを継いだ大きさが上限を超えたら、残りを読まずに
  PacketTooBigException (S1000、"Packet for query is too large (<n> > <上限>). You can change this value on the server by
  setting the 'max_allowed_packet' variable.") にする (2026-11-08)。上限は URL の maxAllowedPacket、無ければ 64 MiB
  (MySQL 8.4 の max_allowed_packet の既定)。前は上限なく継いだので、偽のサーバーや中間者がメモリを使い切らせることが
  できた。Connector/J は物理パケット 1 つずつを maxAllowedPacket (指定が無ければつないだ後にサーバーの
  max_allowed_packet) と比べ、継いだ大きさは見ない。mulay はサーバーの値を信じない (嘘をつくサーバーを防ぐため) ので、
  既定は決まった値にする (deviations.md)。maxAllowedPacket が数でなければ Connector/J と同じ S1009。0 以下は
  Connector/J と同じく全部のパケットが大きすぎる。テストは test/mytls/mysql_packet_test。

## 理由
- 実 Mule のアプリが使う JDBC ドライバが mysql-connector-j 9.2 で、設定を変えないアプリはこの既定で動く。

## 注意
- パケットの書き出しは 0xffffff バイトごとに分け、本体がちょうどその倍数なら空のパケットで終える。
- Handshake v10 の nonce の後半の最後の NUL は nonce に入れない。

## 場所
- `mulay.db.mywire/cell-of`、`mulay.db.mywire/client-caps`、`mulay.db.mywire/quote-str`、`mulay.db.mywire/ldt-lit`、
  `mulay.db.mywire/zoned-lit`、`mulay.db.mywire/first-word`、`mulay.db.mywire/result-set-query?`、`mulay.db.mywire/server-err`、
  `mulay.db.mywire/comm-err`、`mulay.db.mywire/packets`、`mulay.db.mywire/parse-hello`、`mulay.db.mysql/unescape-call`、
  `mulay.db.mysql/run-batch`、`mulay.db.mysql/gen-keys`、`mulay.db.mysql/ssl-config`、`mulay.db.mysql/read-packet`、`mulay.lib.keystore/read-jks-certs`
