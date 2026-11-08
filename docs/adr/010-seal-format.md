# 010 — 埋め込む値は PBKDF2 で導いた鍵の AES-256-CBC で封じ、暗号化してから HMAC をかける

状態: **採用** (2026-10-08、50e666a)

## 決定

- `mulay build --encrypt` が埋め込む値は `mulay.lib.seal/seal` で封じ、実行時に `unseal` で戻す (docs/aot.md)。
- 形式: `"MS1"` + salt (16) + iv (16) + AES-256-CBC (PKCS7) の暗号文 + HMAC-SHA256 (32)。
- 鍵は PBKDF2-HMAC-SHA256 (10 万回) でパスフレーズから 64 バイトを導き、前半を暗号に、後半を HMAC に使う。
- HMAC は "MS1" から暗号文までにかける (暗号化してから HMAC)。確かめてから復号する。鍵が違うか壊れていれば `BAD-KEY`。

## 理由

- 確かめてから復号するので、違う鍵がパディングの偶然で通ることはない。

## 場所

- `mulay.lib.seal/seal`、`unseal`、`BAD-KEY`
