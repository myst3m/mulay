# 038 — Java の名前で引く機能 (文字コード、MessageDigest / Mac) は、名前を写して mulay と clay の実装で計算する

状態: **採用** (2026-09-28。表の文字コードの strict の失敗は 2026-09-29、116ea6f)

## 決定
- 文字コード: 名前は Java の `Charset.forName` と同じく大小文字を区別せず、別名を含めて ID に写す (対応外は "")。
  - UTF 系・US-ASCII・ISO-8859-1・windows-1252 は binaries で自前に符号化・復号する (CharsetDecoder の REPORT の
    失敗の種類と長さも)。
  - それ以外 (Shift_JIS、windows-31j、EUC-JP、ISO-8859-x、windows-125x) は clay.charset の表で扱い、strict の失敗の
    種類と長さは clay.charset の check で JDK と同じにする。
  - 符号化で表せない文字は '?' (String.getBytes と同じ)。UTF-16 は BOM 付き、UTF-32 は BOM なしのビッグエンディアン
    (Java の UTF_32 の符号化器)。復号は strict でなければ不正な並びを U+FFFD (new String と同じ)、strict なら最初の
    不正で止めて "Malformed" / "Unmappable" と長さを返す。
- dw::Crypto: Java の MessageDigest / Mac の名前 (別名と OID を含む、大小文字を区別しない) を OpenSSL の名前に写し、
  mulay.lib.crypto で計算する。MD2 は自前。失敗の文言は実 DW に合わせる。

## 理由
- JVM を持たないので、Java の名前を受けて同じバイト列と同じ失敗を返すには、名前の表と実装を自前で持つしかない。

## 場所
- `mulay.dw.lib.binaries/charset-id`、`mulay.dw.lib.binaries/cs-encode`、`mulay.dw.lib.binaries/cs-decode`
- `mulay.dw.lib.crypto/digest-name`、`mulay.dw.lib.crypto/hmac-name`
