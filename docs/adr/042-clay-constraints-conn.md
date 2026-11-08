# 042 — Clay の制約を避ける書き方 (conn)

状態: **採用** (2026-09-30〜2026-10-12。項目ごとに導入コミットの日付を書く)

src/mulay/conn/ の中で、Clay (言語・runtime・clay.http・clay.tls) の制約や性能を避けるために選んだ書き方。
見た目は回りくどいが、素直な形に「単純化」すると不具合か遅さが戻る。

## 決定

### 並行と排他
- **VM のキューは、キューと取り出し中の message を同じ Atom に置き、先頭を 1 回の `swap!` で取り出しの欄 (番号ごと) へ移す**。
  移した後で欄から読んで消す。listener は numberOfConsumers 本 (既定 4) が並行に取り出すので、「先頭を読む」と「先頭を消す」を
  別の操作にすると同じ message を 2 本が取る。(2026-09-30、dc82dbf)
- **ファイルへの書き込みを 1 つずつ順にするために、2 つの Atom (`ticket` と `serving`) で番号札の待ち合わせ (ticket lock) をする**。
  番号を `swap!` で取り、自分の番まで `sleep-ms 1` で待つ。ObjectStore の persistent の店と VM の PERSISTENT のキュー。(2026-09-30、8d15968)
- **A2A のイベントの記録の送り出し (broadcast) とつなぎ直し (resubscribe) は、Atom の比較と交換で取るロック (`lock!` / `unlock!`) で
  順に実行する**。つなぎ直しが「これまでのイベント」を送る間に新しいイベントが割り込むと、抜けるか重なる。(2026-10-07、b19acb5)
- docs/clay-capabilities.md が並列の道具として挙げるのは `atom` (`swap!`・`reset!`) とチャネルで、上の 3 つはどれも Atom の上に作った。

### http:request の streamResponse
- **応答の本文を届いた分から流すには、clay.http の `ChunkStream` を別のスレッド (`future`) で受け、頭と本文をチャネルに積む**。
  頭は `chan-buf 1`、本文は `chan`。PIPE のストリーム (rt/stream) の Source がチャネルから 1 断片ずつ読む。Source を閉じると
  チャネルを閉じ、受ける側の `>!` が false になって `http/->Stop` で要求を止める (接続を閉じる)。頭が届かないまま終われば、
  頭のチャネルに status -1 の応答 (理由句にエラーの文言) を積む。(2026-10-09、588c98c)

### clay.http・clay.tls の既定に任せない所
- **http:request は HTTP/1.1 だけを出す**。clay.http の既定は h2 も出すが、実 Mule の http:request は HTTP/1.1 だけ。(2026-10-02、5156bb0)
- **nonProxyHosts は mulay で照合し、clay.http には非 proxy の一覧を空で渡す**。clay.http は `*x` / `x*` のワイルドカードを解釈するが、
  実 Mule (http-proxy の記録) はコンマで分けた項目とホスト名の完全一致 (大文字小文字を区別) で、ワイルドカードは働かない。(2026-10-09、772ac75)
- **WSC の Content-Type の折り返し (`\r\n\t`) は空白 2 つにする**。clay.http はヘッダーの値に改行を許さない。(2026-10-10、a753700。deviations.md にも記載)
- **tls:context から clay.tls へは、使う版のスイートだけを渡す**。clay.tls は protocols に合うスイートが無いと設定の誤りにするので、
  スイートに TLS1.3 のものが無ければ TLSv1.3 を、TLS1.2 のものが無ければ TLSv1.2 を外してから渡す。スイートの表は clay.tls が持つ
  ECDHE と AEAD の 9 つ (clay 0.86.1)。(2026-10-12、399995d)
- **接続の失敗の文言は、clay.http / clay.tls の文言を実 Mule の文言に写す**。頼っている文言は clay の版で変わってきた:
  "http: no response" (0.78.0 から)、応答の枠の誤り (0.79.0、clay の ADR 091)、Content-Length の値と最初の行の付記 (0.79.1 から)、
  TLS の "tls: the server's certificate: x509: untrusted: .." (0.86.0 から clay.tls.engine)。clay を上げたら https-test で確かめ直す。

### 性能
- **A2A の JSON の読み取りは、列 (行の始まりからの文字数) を進めた分だけ足していく**。値ごとに行の始まりから数え直すと、改行の無い
  1 行の大きな JSON で O(n^2) になる (320KB に 19.5 秒)。A2A のサーバーは authorization-listener より前にこれで読むので、
  認証なしの要求で CPU を使わせられた。読み取りの状態 `P` に、行の始まりから今の位置までの文字数 `lc` を持つ。(2026-10-04、50b662c)
- **DB の結果の class のメタデータは定数 (`CM-INT` などと `CM-ROW`) を共有し、列名の Key は結果ごとに 1 回作る**。行ごと・セルごとに
  作ると割り当てが何倍にもなる (SQLite 100 万行: 1.2 秒 1.3GB → 0.66 秒 0.55GB)。(2026-10-03、d84df24)

## 理由
- 上の各項に書いた。どれも消すと、並行の取り違え・止まらない要求・clay の既定による挙動の違い・二次の時間のどれかが戻る。

## 場所
- `mulay.conn.vm/Q`、`mulay.conn.vm/take-msg`、`mulay.conn.vm/save`
- `mulay.conn.os/St`、`mulay.conn.os/save`
- `mulay.conn.a2a/lock!`、`mulay.conn.a2a/unlock!`、`mulay.conn.a2a/broadcast`、`mulay.conn.a2a/resubscribe`
- `mulay.conn.http/pump`、`mulay.conn.http/pipe-next`、`mulay.conn.http/fetch-stream`
- `mulay.conn.http/run-request` (HTTP/1.1)、`mulay.conn.http/bypass?`、`mulay.conn.http/proxy-of`、`mulay.conn.http/conn-fail-text`、`mulay.conn.http/FRAME-ERRS`
- `mulay.conn.wsc/mime-ct`
- `mulay.conn.tls/limits`、`mulay.conn.tls/SUITES-13`
- `mulay.conn.a2a_spec/P`、`mulay.conn.a2a_spec/col`
- `mulay.conn.db/class-meta`、`mulay.conn.db/CM-ROW`、`mulay.conn.db/col-keys`、`mulay.conn.db/rows-val`
