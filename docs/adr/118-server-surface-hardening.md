# 118 — 外から叩ける口の守り (公開前の点検)

状態: **採用** (2026-11-08、公開前の安全の点検で)

認証の無い要求でも、メモリ・ディスク・内部の宛先を使えないようにする。実 Mule と違うところは docs/compat/deviations.md に書く。

## 内部の状態のファイルは持ち主だけが読める

- Object Store・VM の待ち行列の記録 (`rt/persist/save`) と、本文と DW の出力の spool (`lib/spool`) は、ファイルを 0600、
  作るディレクトリを 0700 にする (`fs/create-new-private`、`fs/mkdirs-private`)。
- `mkdirs-private` は、作るディレクトリをすべて 0700 にし、既にある末端 (`<work>/<アプリ>/<種類>`) も 0700 に直す。
  途中の既にあるディレクトリ (`mulay.work.dir` そのものなど、人が決めた場所) の mode は変えない。
- clay の `io/open` は 0644、`io/mkdir` は 0755 で作り、mode を渡せないので、`open`・`mkdir`・`chmod` を defextern で呼ぶ。
  spool は `create-new-private` で空のファイルを作ってから `"rw"` で開く。
- File コネクタが書くファイル (`file:write` の CREATE_NEW など) と、Anypoint Monitoring の書き出し先は人が決めた場所なので、
  今までどおり (0666 から umask を引いた mode)。

## A2A のタスクの記録 (Object Store を使わないとき) に期限と上限

- 認証の無い `message/send` がタスクを作るので、メモリの記録 (`TASKS`) を次のように減らす (`a2a/evict-keys`、`sweep-tasks`)。
  - 最後に書き換えてから 1 日 (`TASK-TTL-MS`) で消す。実コネクタの既定の店 (persistent、1 日) と同じ期限。
  - 10000 (`TASKS-MAX`) を超えたら、終わったタスク (completed・canceled・failed・rejected・unknown) の古い順に消し、
    それでも多ければ終わっていないものも古い順に消す。新しい要求を断るより、古いものを捨てるほうが動き続ける。
- 見直すのは新しいタスクを足したときだけ (上限を超えたときと 256 件ごと)。毎回全部を見ない。
- Object Store を書いたサーバーは店の期限に任せる (変えない)。

## MCP サーバーのセッションに期限と上限

- セッション (`SESSIONS`) ごとに最後に使った時刻と期限を持つ (`SEEN`、`Seen [at idle]`)。期限は streamable-http の
  `sessionIdleTimeout` (既定 5 分)。旧式の SSE は 0 (期限なし。ストリームがつながっている間がセッション)。
- 引くたび (`session-ver`) に、期限を過ぎていれば消して「無い」と答え、過ぎていなければ時刻を今にする。
  期限ちょうどで消えるので、掃除の間隔に左右されない。
- 新しいセッションを作ったとき (全部で 10000 (`SESSIONS-MAX`) を超えたときと 256 件ごと) に `stale-sessions` で掃除する:
  期限を過ぎたものと、上限を超えた分を最も長く使われていない順に。つながっている旧式の SSE のセッションは上限でも消さない。
- 実 Mule (mcp 1.5.0) はメモリのセッションを消さない (sessionsObjectStore を書くと Caffeine の expireAfterAccess で手元から外すが、
  店から読み直すので続く)。test/fixtures/apps/mcp-sess で 2 秒の期限を 3 秒待っても続くことを記録していたが、
  その要求はシナリオから外した (実 Mule と違う振る舞いなので照合に入れない。期限の振る舞いは test/mcp/session_test が守る)。
  設定の文書 ("Timeout for idle sessions") のとおりに切るほうを選んだ。認証の無い initialize でメモリを使い切れないように。

## MCP サーバーは Origin を調べる

- MCP の仕様 (Transports、Security Warning) は「サーバーは Origin ヘッダーを検証しなければならない (DNS rebinding を防ぐ)」と言う。
  実 Mule (mcp 1.5.0) は見ない。SSE の応答 (streamable-http の SSE と旧式の SSE) には `Access-Control-Allow-Origin: *` まで付ける。
- DNS rebinding では Origin と Host が同じ (`evil.example`) になるので、「Origin と Host が同じなら通す」では防げない。許す一覧にする。
  - Origin が無い: 通す (ブラウザでないクライアント。curl、MCP の SDK、オラクル)。ブラウザは別の Origin への POST に必ず付ける。
  - Origin のホストが loopback (`localhost`、`127.x.x.x` の 4 つの数、`[::1]`): 通す (手元の開発の画面、MCP Inspector)。
  - `mulay.mcp.allowedOrigins` (カンマ区切りの完全一致、`*` はすべて) にある: 通す。
  - ほか (`null` を含む): 403。JSON-RPC の -32600 の本文で、直し方 (プロパティの名前) を書く。
- 調べるのは経路の入口 (`srv-respond`) で、streamable-http の POST・GET・DELETE と旧式の SSE の GET・POST の全部。
- `Access-Control-Allow-Origin: *` は実 Mule と同じく残す。通らない Origin は本文を受け取れないので、残しても読ませない。

## A2A のプッシュ通知は内側のアドレスに送らない

- 送り先の URL は要求を送った人 (認証の無い `message/send` の configuration や `tasks/pushNotificationConfig/set`) が決める。
  そのままでは、クラウドのメタデータ (`http://169.254.169.254/`) や、サーバーの手元だけで開いている管理の口へ、
  サーバーが POST する (SSRF)。
- 送る直前 (`post-push`) に調べる。設定を受けるときに断ると JSON-RPC の答えが実コネクタと変わるので、受けるのはそのまま。
  1. URL の名前を引く (`mulay.lib.netaddr/resolve`、clay.net/resolve)。数字の形 (`2130706433`、`[::1]`) も同じ道で数に直る。
  2. 引いたアドレスに 1 つでも内側のもの (`netaddr/internal?`: 0/8、10/8、100.64/10、127/8、169.254/16、172.16/12、192.0.0/24、
     192.168/16、198.18/15、224/3、::、::1、fc00::/7、fe80::/10、ff00::/8、それに IPv4 を埋め込んだ ::ffff:0:0/96・::/96・64:ff9b::/96・2002::/16)
     があれば送らず、WARN を出す。1 つでもとするのは、名前が公のものと内側のものを混ぜて返すとき、どちらにつながるか分からないため。
  3. 送るときは、調べたアドレス (IPv4 があればそれ) を URL に書いてつなぎ、Host ヘッダーと TLS の SNI (証明書の照合も) は元の名前にする。
     調べた後に名前の向き先を変えても (DNS rebinding)、調べていないアドレスにはつながない。
  4. `:max-redirects 0`。リダイレクトの先は調べていないので追わない。
- `mulay.a2a.allowPrivatePushUrls=true` で内側にも送る (手元の受け手で試すとき。シナリオ a2a-push、a2a-push-opts、agent-harness)。
  そのときは URL のままつなぐ (localhost が ::1 と 127.0.0.1 の両方を返すとき、clay の接続に任せる)。
- 名前を引くのは clay 0.115.0 の `clay.net/resolve` (clay の接続と同じ引き方で、期限の下では別のスレッドで引く。返る
  アドレスのバイト列だけを使う)。`::ffff:a.b.c.d` の形は `netaddr/internal?` が IPv4 として調べる。clay 0.114 までは
  getaddrinfo を defextern で直に呼んでいた。wasm には名前を引く道が無いので、失敗を返す。

## listener: 経路の無い要求の大きな本文は読まない

- 流して受ける本文 (ADR 104: 512 KB を超えるか長さの無いもの) は、前は経路を決める前に全部を spool (512 KB を超えた分はディスク) に
  受けていた。だれでも、どのパスにでも本文を送ってディスクを埋められた。
- 本文を受ける前に経路を引き (`unrouted?`: 対象の誤り、経路なし、method 違い)、当たらなければ本文を読まずに 400 / 404 / 405 を返す。
  文言は今までと同じ。
  - HTTP/1.1: 読んでいない本文が残るので、答えた後で接続を閉じる (`:close true`)。curl で 20 MB を送っても 404 が届く。
  - HTTP/2: 閉じない。閉じると、同じ接続の他の流れ (並行の要求) まで切れた (curl `--parallel` で確かめた)。clay は答えた流れの残りを捨てる。
- mount (MCP・A2A など) の経路とストリームの mount はそのまま (経路がある)。

## listener: ディスクの空きが少なければ本文を溜めない

- 本文の spool は要求ごとの上限 (`mulay.http.maxRequestBody`、既定 0 = 上限なし。実 Mule と同じ) しか無く、並行に送れば
  ディスクを埋められた。要求ごとの既定の上限は、接続の数 (最大 10000) を掛けると守りにならず、実 Mule が受ける大きな本文 (200 MB) も断る。
- そこで、本文の切れ端をディスクに書くたびに (`drain-body`、メモリからファイルに移るときも)、spool の置き場のファイルシステムの空き
  (`fs/disk-space`、statvfs の f_bavail × f_frsize) を見て、`mulay.http.spoolMinFree` を下回れば 503 で閉じ、溜めた分を消す。
  - 既定 (-1) はファイルシステムの 10% と 1 GiB の小さいほう。0 で調べない。全部の要求の合計に効く (同じファイルシステムを見る)。
  - 1 MiB ごとに見ると、並行の要求の数 × 1 MiB だけ超えうるので、毎回見る (statvfs は数マイクロ秒)。
- 503 にするのは、要求が悪いのではなくサーバーの置き場が足りないため (413 は要求ごとの上限のとき)。

## 変えなかったこと

- 本文の待ち時間の合計の期限: 実 Mule の listener の readTimeout (既定 30000) と connectionIdleTimeout (既定 40000) は、どちらも
  読みと読みの間の時間 (HTTP コネクタ 1.11.3 の `HttpListenerProvider$ConnectionParams`)。mulay の 30 秒 (`BODY-IDLE-MS`) も切れ端ごとに
  数え直すので同じ。合計の期限を足すと、遅い回線の正しい大きな送信を切る。少しずつ送って接続を持ち続ける相手は、接続の数の上限
  (clay の 10000) で止まる。
- 1 つの接続がメモリに持つ本文 (512 KB まで。ADR 104) × 接続の数は変えていない (実 Mule の inMemorySize と同じ)。
- MCP の Origin: ブラウザは同じ Origin の GET に Origin を付けないので、DNS rebinding で同じ Origin になったページは、
  旧式の SSE の `GET /sse` (on-new-session-listener のフローが走る) を開ける。その後の `POST /message` は Origin で断る。

## 上限を超えたときの掃除は 9 割まで減らす

- A2A のタスクと MCP のセッションは、上限を超えて掃除するとき上限の 9 割まで減らす。上限ちょうどまでにすると、
  あふれさせ続ける相手の要求ごとに 10000 件の並べ替えが走り、守りが CPU を食う口になる。9 割なら約 1000 件ごとに 1 回。
