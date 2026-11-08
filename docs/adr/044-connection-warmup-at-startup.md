# 044 — Salesforce と Anypoint MQ の接続は起動のときに裏で用意し、最初の操作はそれを待つ

状態: **採用** (2026-10-12。f44c1a4 Salesforce、75c0cc7 Anypoint MQ)

## 決定
- 起動のとき (コネクタの init) に、設定ごとの接続を裏のスレッド (`future` を `future-detach`) で用意する。
  - Salesforce: セッション (トークンと、インスタンスとの TLS の接続)。認可コード (config-with-oauth-connection) は利用者の
    トークンが要るので取らない。jwt-connection の鍵も init で読んでおく (読めなければ接続のときに失敗する)。
  - Anypoint MQ: 送り直しの設定を読み、サービスレジストリ・トークン・ブローカーとの TLS を用意する。トークンは 1 回だけ試す
    (操作のときは 5 回)。
- 裏の仕事を始める前に「用意している」印を付ける (Salesforce は cache の `warming:<設定の名前>`)。その間に来た操作は、
  用意が終わるのを最大 15 秒待って、その接続を使う (トークンを 2 度取らない)。
- 用意の失敗は覚えない。操作のときに改めて取る。
- 接続 (セッション・トークン) は設定ごとにプロセスに持ち、期限切れ (Salesforce の INVALID_SESSION_ID、MQ の 401) なら
  取り直して 1 度だけ送り直す。

## 理由
- 実 Mule はデプロイのときに接続を確かめ (connectivity test)、その接続を操作で使うので、最初の操作でトークンを取りに行かない。
  mulay は最初の操作で取っていたので、その分だけ遅かった (max/core の /admin/reset で +300〜450 ms)。

## 注記
- Anypoint MQ の用意は docs/compat/deviations.md に「実 Mule とは照合していない」として載せてある。

## 場所
- `mulay.conn.salesforce/init`、`mulay.conn.sf_core/warm`、`mulay.conn.sf_core/warm-mark!`、`mulay.conn.sf_core/warming?`、
  `mulay.conn.sf_core/session-in`
- `mulay.conn.anypoint_mq/warm`、`mulay.conn.anypoint_mq/warming?`、`mulay.conn.anypoint_mq/connect`
