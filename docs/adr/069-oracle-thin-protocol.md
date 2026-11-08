# 069 — Oracle は 23ai 以降だけを相手にする純 Clay の thin で、手順は python-oracledb 26、値と文言は ojdbc11 23.8 に合わせる

状態: **採用** (2026-09-30、a48b0c6・5014d30・0e659ad。thin で書く決定は docs/design.md §6.5)

## 決定
- 接続の手順とメッセージの形は python-oracledb 26 の thin の実装を読んで書く。値の Java の型、失敗の文言、SQLState と
  例外の class は ojdbc11 23.8 (Mule のアプリが使う JDBC ドライバ) に合わせる。
- 対象は ACCEPT で応答の終わりの印 (EOR) と FAST_AUTH が付く 23ai 以降のサーバ。それより前の版は接続のときに断る。
  FAST_AUTH 1 回で PROTOCOL + DATA_TYPES + 認証の 1 段目を送る。
- 送る定数は python-oracledb 26 と同じにする: DATA_TYPES の表 (型、変換先、表現の 322 組)、能力 (compile-time 55 バイト、
  runtime 11 バイト。7 番目は TTC の版で交渉で下げる、40 番目の 0x20 が EOR)、define の緩衝の大きさ (NUMBER 22、
  LOB 112、BOOLEAN 4)。CONNECT は版 319〜300、SDU / TDU 8192、OOB は使わない。記述子が 230 バイトを超えたら続く
  DATA パケットに入れる。
- 接続は値のレコード (`Conn`) で、呼び出しの番号 (1〜255 を回る) と次の実行の前に閉じるカーソルを持つ。実行する関数は
  更新した Conn を戻り値の最後に返す。閉じるカーソルは次の要求の前置き (piggyback) で送る。
- 応答の読み取り: EOR を送るサーバでは、印の付いたパケットまで溜めてから 1 回だけ parse する (ADR「Clay の制約を避ける書き方 (src/mulay/db)」)。
- 自動コミット (Mule の既定)。セッションの時間帯は実行環境の既定の地域 (認証の AUTH_ALTER_SESSION で設定する)。
- 失敗の文言はサーバの "ORA-nnnnn: .." に "\n\nhttps://docs.oracle.com/error-help/db/ora-nnnnn/" を続けたもの。

## 理由
- OCI / Instant Client に頼らず依存なしで配布するため (design.md §6.5、2026-09-30 の決定)。
- 19c 以前の手順 (PROTOCOL / DATA_TYPES を別に送る)、TCPS、ネットワーク暗号化は持たない (docs/connectors.md の未対応)。

## 注意
- O5LOGON の AES-CBC は常に詰め物を足す (16 の倍数でも 16 バイト)。サーバの応答 AUTH_SVR_RESPONSE を combo の鍵で
  解くと 16〜32 バイト目が "SERVER_TO_CLIENT" になることを確かめる。
- AUTH_SESSKEY は 32 か 48 バイトであることを、使う前に確かめる (ADR「Clay の制約を避ける書き方 (src/mulay/db)」)。
- マーカー (BREAK) を受けたら RESET を送り、RESET のマーカーが来るまで読み捨ててから立て直す。RESEND を受けたら同じ
  CONNECT をもう一度送る。

## 場所
- `mulay.db.oraproto/connect-packets`、`mulay.db.oraproto/fast-auth`、`mulay.db.oraproto/RCAPS`、`mulay.db.oraproto/DATA-TYPES`、
  `mulay.db.oraproto/close-cursors`、`mulay.db.oracle/Conn`、`mulay.db.oracle/next-seq`、`mulay.db.oracle/prefix`、
  `mulay.db.oracle/define-of`、`mulay.db.oracle/call`、`mulay.db.oracle/reset-after-break`、`mulay.db.oracle/open-conn`、
  `mulay.db.oracle/enc-pad`、`mulay.db.oracle/verifier`、`mulay.db.oracle/server-ok?`、`mulay.db.oracle/ora-message`
