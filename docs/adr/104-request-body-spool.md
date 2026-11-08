# 104 — listener の大きな要求の本文は流して受け、512 KB を超えた分はファイルに逃がす

状態: **採用** (2026-10-25 に HTTP/2 で branch に。2026-10-26 に clay 0.100.0 (ADR 132) で HTTP/1.1 にも広げて main に入れた)

## 決定

- **流して受ける要求**: HTTP/1.1 と HTTP/2 で、Content-Length が 512 KB (`rt/bodies/IN-MEMORY`) を超えるか、Content-Length が無くて
  本文を持ちうる method (GET・HEAD・OPTIONS・DELETE・TRACE 以外。HTTP/1.1 の chunked を含む) の要求は、clay の body-stream? で
  流して受ける (`app/run/body-streamed?`)。
  それ以外は今までどおり clay が全部受けてから渡す (小さい要求の速さを変えない)。gRPC の mount の経路の判定とは OR でつなぐ。
- **溜め方** (`mulay.lib.spool`): 初めの 512 KB はメモリに、超えた分は `mulay.work.dir/<アプリ>/spool/<pid>/body-<n>` のファイルに書く (プロセスごとに分ける。同じ作業ディレクトリで同じアプリを 2 つ動かしても、名前がぶつからず、起動時の片づけが他のプロセスの分を消さない)。
  実 Mule の EE の既定 (repeatable-file-store-stream、inMemorySize 512 KB) と同じ。512 KB 以下なら今までどおり RAW の payload。
- **payload**: 512 KB を超えたら PIPE の TypedValue にする。中身は spool を読む rt/stream の cursor で、読み直せる
  (`rt/bodies/open`、file:read の大きなファイルと同じ)。PIPE を読む所 (DW の `pipe-raw` と並びの読み手、file:write) は `stream/fork` で
  頭から読む読み手を開き、読み終えたら捨てる (`stream/discard`)。listener の応答へのこだま (piped-resp) は、持ち主になった cursor を読む。何度でも読め、読み終えた分はメモリに残らない。
  file:write は 64 KB ずつ写す (メモリは一定)。DW で読むと、その式の間だけ全部をメモリに持つ (実 Mule の `as String` と同じ)。
- **ファイルを消す時**: 元の cursor が閉じた時だけ消す。cursor の持ち主は要求の rid (handle-app で `stream/adopt`)。
  async と batch は rid の持ち主の数を増やすので、要求の後も読める。listener の応答へのこだまは、piped-resp が持ち主になる。
  flow まで届かない要求 (404・405・400) は、仮の持ち主 `spool-<n>` が抜ける時に消える。
  起動時に、自分の pid のディレクトリと、もう動いていないプロセスのディレクトリ (`/proc/<pid>` が無いもの) と、pid でない名前のものを消す
  (`rt/persist/clear-spools`。止まったプロセスが残したもの)。動いている他のプロセスの分は残す。
- **上限**: `mulay.http.maxRequestBody` (バイト、既定 0 = 上限なし。実 Mule と同じ)。超えたら 413。
  経路の無い要求の本文は溜めない、などの守りは ADR 118。
  本文が 30 秒届かなければ 408、途中で切れたら 400 (どちらも接続を閉じる)。
- **HTTP/2 の payload の mime**: 実 Mule 4.11.3 は HTTP/2 で受けた要求の payload を Content-Type に関係なく `*/*` にする
  (`app/exchange/request-event`、test/fixtures/apps/http2-payload)。

## 理由

- 前は clay が要求を全部メモリに受け、1 MiB (max-body) を超えると 413 だった。実 Mule は 200 MB の本文も受ける (2026-10-25 に確かめた)。
- 本文を全部 1 つの文字列にすると、本文の大きさだけメモリを使う。ファイルに逃がせば、読まない flow・ファイルに書く flow・
  こだまはメモリが一定になる (200 MB の h2c で、読まない flow は 37 MB、file:write は 34 MB)。
- PIPE は「届いた分から読めて読み直せる本文」(ADR 052) で、扱う所が揃っている。新しい state を足すと、raw を本文と思って読む
  所 (bytes、persist、ostore など) を全部直す必要がある。
- 読み直しを cursor の行の保持 (stream/all の DONE) に頼ると、全部をメモリに持つ。fork なら読むたびにファイルから読む。

- 計測 (2026-10-26、clay 0.100.0): 200 MB を HTTP/1.1 でこだますると、Content-Length でも chunked でも 0.25〜0.28 秒、RSS 46〜48 MB
  (応答の sink の背圧、ADR 132 段 4 で途中で切れなくなった)。200 MB のファイルの `sizeOf(payload as String)` を 2 回で 0.13 秒 (実 Mule 0.40 秒)。

## 残ること

- http:request の本文に PIPE を使うときは、まだ全部をメモリに組み立てる。

## 場所

- `mulay.lib.spool`、`mulay.rt.bodies`、`mulay.app.run`: `handle-in`、`drain-body`、`body-streamed?`、`handle-app` (adopt と PIPE)、`serve` (起動時に空にする)
- `mulay.rt.stream`: `open-repeatable`、`fork`、`discard`、`repeatable?`
- `mulay.rt.event/pipe-raw`、`mulay.conn.file` の file:write
- 試験: test/spool、test/rt/stream_test (fork)、test/fixtures/apps/http-request-body (HTTP/1.1 と h2c と TLS の 20 MB、2 回読む、file:write の後に読む)
