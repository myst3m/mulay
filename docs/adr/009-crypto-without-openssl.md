# 009 — 暗号の部品は OpenSSL を使わず、clay.crypto・clay.pkix と OS の乱数と純 Clay で組み、名前は OpenSSL の綴りで引く

状態: **採用** (2026-10-11 に要約・HMAC・PBKDF2・AES・乱数・署名を移し、2026-10-13 の 8172744 で PKCS#12 も移して OpenSSL の FFI を外した)

## 決定

- 要約の名前は OpenSSL の名前 ("MD5" "SHA1" "SHA224" "SHA256" "SHA384" "SHA512" "SHA512-224" "SHA512-256" "SHA3-224"〜"SHA3-512")。
  知らない名前は ok = false。
- `mulay.lib.hash`: 名前で引く入口、途中の状態 (`start`・`feed`・`finish`)、HMAC (RFC 2104)、PBKDF2 (RFC 8018)。要約の計算そのものは
  clay.crypto (runtime の C。CPU に SHA 命令や BMI があればそれを使う)。外部の C のライブラリを使わないので wasm でもそのまま動く。
  - HMAC は鍵を ipad と opad で 1 ブロック圧縮した 2 つの状態を作り (`hmac-states`)、入力をそれに足す。PBKDF2 はこの状態を回数分使い回す。
  - PBKDF2 の 1 ブロックは、MD5・SHA-1・SHA-2 では要約の語のまま xor を積む (`hmac-words`)。
- `mulay.lib.crypto`:
  - 要約・HMAC・PBKDF2 は `mulay.lib.hash`。MD2 (RFC 1319) は OpenSSL 3 が既定で持たないので自前で計算する。
  - AES は clay.crypto (秘密のバイトで表を引かない portable 版、CPU に AES-NI があればそれ)。鍵の長さ (16 / 24 / 32) で AES-128 / 192 / 256。
    CBC と ECB は data が 16 の倍数、CFB (CFB128) と OFB は長さを問わない。
  - CFB の暗号化は前のブロックの結果を待つので 1 ブロックずつ。CFB の復号は、鍵の流れ (iv と、最後を除く暗号文のブロックを ECB で
    暗号化したもの) を 1 回で作って xor する。OFB の鍵の流れは iv から暗号化を繰り返したもので、0 の並びを CBC で暗号化したものと
    同じなので 1 回で作れる (暗号化と復号は同じ)。
  - 署名は clay.pkix で鍵 (PKCS#8 か PKCS#1 の DER) を読み、clay.crypto の rsa-sign (PKCS#1 v1.5、RS256〜RS512)。PKCS#1 の DER は
    PEM の RSA PRIVATE KEY にして clay.pkix で読む。
  - PKCS#12 は clay.pkix の pkcs12-decode と pkcs8-der (openssl と同じバイト)。証明書は捨て、鍵が複数あっても最初の 1 つ
    (OpenSSL の PKCS12_parse と同じ)。
- `mulay.lib.random/random-bytes`: 暗号用の乱数は OS の乱数 (clay の prim/random-bytes、Linux では getrandom)。

## 理由

- 外部ライブラリを減らす (mulay のリンクは libc と libm だけ。docs/aot.md)。
- 速さ: digest は MD5・SHA1・SHA-2・SHA-3 のどれも 64 MB と 64 バイト × 100 万回の両方で Java 17 より速い (下の「測定」)。乱数は 16 バイト × 100 万回で getrandom 35 ms、RAND_bytes 538 ms、Java 17 の UUID.randomUUID 136 ms (fdd352f)。
- CFB の復号と OFB を鍵の流れ 1 回で作るのは、ブロックごとに ECB を呼んで 1 バイトずつ xor する形をやめるため (0fd407a)。

## 測定

切り替えの条件は、64 MB と 64 バイト×100 万回の両方で Java 17 (実 Mule) より遅くないこと。Java は MessageDigest・Mac・Cipher を
毎回作る形 (DW や secure properties と同じ) で、温めた 3 回目の値。
測り方: 他の作業 (他のセッションのビルドや検証) が走っていない時に、`taskset -c 3` で 1 つのコアに止めて測る。負荷のある時の値は
膨らむ (64 バイトの SHA-512 が 255 ns と出て、止めて測ると 158 ns だった)。64 バイトの値は、同じ処理でもループの置き方で
±30% ほど動くので、余裕を持って勝つものだけを切り替える。
2026-10-11 に clay 0.83.0 で止めて測った値 (mulay / Java):
- 64 MB (ms): MD5 62 / 65、SHA-1 25 / 25、SHA-224 27 / 27、SHA-256 27 / 27、SHA-384・SHA-512 の族 61〜62 / 65〜66、
  SHA3-224 109 / 137、SHA3-256 115 / 145、SHA3-384 148 / 186、SHA3-512 210 / 271。
- 64 バイト×100 万回 (ms): MD5 135 / 177、SHA-1 67 / 164、SHA-224 73 / 114、SHA-256 75 / 112、SHA-384・SHA-512 の族 139〜142 /
  193〜202、SHA-3 258〜261 / 358〜367。
- HMAC 43 バイト×100 万回 (ms): SHA-256 228 / 391、SHA-1 222 / 370、SHA-512 720 / 818、MD5 356 / 458、SHA3-256 1090 / 1456。
- PBKDF2 4096 回・64 バイト (ms、clay 0.82.0): SHA-512 1.7 / 2.46、SHA-256 1.26 / 1.34、SHA-1 1.9 / 2.55。
- AES の復号 1 回 (µs): CBC 32 バイト 0.58 / 2.0、10 KB 1.9 / 5.0。CFB 10 KB 2.4 / 19.5。OFB 1 KB 1.6 / 4.1、4 KB 4.1 / 8.6、
  10 KB 9.4 / 17.7。CFB の暗号化は 1 ブロックずつ (使う所は無い)。

## 場所

- `mulay.lib.hash/digest`、`start`、`feed`、`finish`、`hmac`、`pbkdf2`、`hmac-states`、`hmac-words`、`block-size`
- `mulay.lib.crypto/digest`、`hmac`、`md2`、`pbkdf2`、`aes-cbc`、`aes-raw`、`aes-cfb-encrypt`、`aes-cfb-decrypt`、`aes-ofb`、`sign`、
  `pkcs1-private`、`pkcs12-key`
- `mulay.lib.random/random-bytes`
