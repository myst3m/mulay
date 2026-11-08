# 059 — mulay inspect / validate は、名前が秘密らしいプロパティと属性の値を **** と表示する

状態: **採用** (2026-09-28。secure:: と、名前が key / pass で終わるものは 2026-10-10 baad712)

## 決定
- 読み込み結果の表示 (`mulay inspect`、`mulay validate`、`mulay inspect --props`) では、プロパティと属性のうち名前が秘密らしいものの
  値を `****` にする。値の出どころ (コマンドライン、ファイル名、環境変数、global-property、built-in) はそのまま表示する。
- 秘密らしい名前 (大文字小文字を区別しない):
  - password、secret、token、credential、apikey、api.key、passphrase を含む
  - `secure::` で始まる (secure-properties の暗号化して置く値)
  - key、pass、passwd で終わる (`llm.key`、`x.apiKey`、`db.pass`)

## 理由
- 秘密の値を表示に出さない。判断は名前だけで行う。2026-10-10 に出どころの表示を足したとき、secure:: と、名前が key / pass で
  終わるものを規則に足した (baad712)。

## 場所
- `mulay.mule.dump`: `secret-key?`、`props-lines`、`dump-props`、`dump-app`
