# 072 — Clay の制約を避ける書き方 (src/mulay/db)

状態: **採用** (2026-10-14 の記録。各項の導入コミットは項に書く)

## 決定
次の書き方は Clay の値の共有・コピー・abort の振る舞いを避けるためのもの。見た目を「単純化」して戻さない。

1. **Oracle の応答の行は Resp の外の Vec に積む** (`mulay.db.oraproto/parse-loop`、`mulay.db.oraproto/parse`)。
   行はループの引数 `rows` に `conj` し、読み終えてから 1 回だけ `(assoc r :rows rows)` する。Resp の中の Vec に `conj`
   すると、その Vec は Resp と共有されているので毎回複製になる (6e4e001、2026-10-03)。
2. **Oracle の応答は終わりの印 (EOR、データフラグ 0x2000) の付いたパケットまで溜めてから 1 回だけ parse する**
   (`mulay.db.oracle/call`)。パケットが来るたびに溜めた全体を頭から parse し直すと、大きな応答で 2 乗の時間になる。
   1 と 2 を合わせて、10 万行の読み出し (fetch 5000 行) が 14 s から 0.29 s になった (6e4e001)。
3. **SQLite の DB と接続は、使う前に atom の表 (`State` の dbs・conns) から `dissoc` で抜き、終わったら `assoc` で戻す**
   (`mulay.db.sqlite/step`)。表に残したまま使うと値が共有になり、DB を書き換えるたびにページの塊の写しが要る。
   bulk-insert 10 万行が 0.55 s から 0.33 s (ec59b7b、2026-10-11。clay の swap! の修正 b0213f78 と合わせて)。
4. **Oracle の認証は、サーバの値と導出した鍵の長さを、`subs` で切り出す前に確かめる** (`mulay.db.oracle/verifier`)。
   `subs` は範囲外で abort するので、AUTH_SESSKEY が 32 か 48 バイトでないとプロセスごと落ちた。AUTH_SESSKEY を先に
   確かめ ("malformed AUTH_SESSKEY from the server")、復号と PBKDF2 の結果も使う前に確かめる (2796192、2026-10-04)。
5. **乱数が取れなかったときも、長さの合う代わりの値で計算を最後まで進め、最後に失敗にする** (`mulay.db.oracle/verifier`
   の `bb`)。空のまま後の `subs` に渡すと範囲外で落ちる (6610a7c、2026-10-04)。

## 理由
- Clay には例外が無く、`subs` の範囲外は回復できない abort になる。Vec と Map は参照カウントで共有され、共有された値を
  書き換えると全体を写す。上の形はそれを避ける。

## 場所
- `mulay.db.oraproto/parse-loop`、`mulay.db.oraproto/parse`、`mulay.db.oracle/call`、`mulay.db.sqlite/step`、
  `mulay.db.oracle/verifier`
