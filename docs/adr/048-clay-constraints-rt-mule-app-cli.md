# 048 — Clay の制約を避ける書き方 (rt・mule・app・cli)

状態: **採用** (2026-10-14 の記録。各項目の導入日は項目ごとに書く)

rt・mule・app・cli のコードには、Clay の性能・スレッド・メモリの性質を避けるための書き方がある。
見た目は回りくどいが、単純にすると不具合か性能の劣化が戻る。

## 決定

### スレッドと参照カウント
- **`(c-flags "-DCLAY_PARALLEL")` を宣言する** (`mulay.app.run` の ns の後)。`future` が本当に別の OS スレッドで
  並行に走るのはこのときだけ。listener のポートごとの run-server、scheduler、scatter-gather / parallel-foreach の worker が
  これに頼る (2026-09-28)。
- **起動状態は def に置く**。`mulay.app.run/Server` (経路の表・実行文脈・scheduler のフロー) と `mulay.cli.main/Boot`。
  def の値は不死になり、全スレッドが読んでも参照カウントを書き換えない。共有された値の参照カウントを原子的に
  増減するとコア間で競合する (7742fa7、2026-09-28)。
  - def は main の前に 1 回だけ計算される (clay 0.80.0、clay の ADR 092)。そのため `Boot` を作る式はアプリを読むかを
    引数から決める。読むのは main が起動に進む引数のときだけで、それ以外は server が空。**`mulay.cli.opts/serves-app?` は
    `mulay.cli.main` の振り分け (`main`) と揃えておく**。ずれると、起動しないコマンドでアプリを読む (または起動するのに読まない)。
- **Event を別スレッドへ渡してよい**。DW の評価器は大域の可変状態を持たず、Clay の参照カウントは run-server のある
  プログラムでは atomic だから (`mulay.rt.engine/run-parallel`。docs/design.md §6.2 が「rt/engine の注記」として指していたもの)。
- **スレッドの数に上限を置く**。要素ごと・要求ごとにスレッドを作ると、作れなくなったところでプロセスごと落ちる
  (Clay 0.69 ではプロセスごと終わった)。
  - `mulay.rt.engine/MAX-PAR-WORKERS` = 256: maxConcurrency の無い parallel-foreach / scatter-gather の worker の数
    (`par-workers`)。参考: 実 Mule は共有のスレッドプール (UBER) で動かし、その大きさはコア数 + (メモリ − 240MB) / 5MB
    程度 (8 コア・1GB で約 160) (b7bcc86、2026-10-04)。
  - `mulay.rt.ops/MAX-BACKGROUND` = 512: 待たない仕事 (async、batch:job、A2A の通知、chunked 応答の書き手) の
    別スレッドの数。超えた分は呼び出し側のスレッドで動かして流量を抑える (`spawn-bg-in`。1d68dcc、2026-10-04)。
    数え `cnt` は、上限を超えた試みの間だけ一瞬 mx + 1 以上になるが、別スレッドの数は mx を超えない
    (先に増やし、超えていたら減らしてこのスレッドで動かす)。
- **セマフォは swap! 1 回で取れたかを知る** (`mulay.rt.engine/sem-acquire`)。`swap!` は新しい値しか返さないので、
  空きがあれば数を増やすのと同じ swap! で自分の番号のしるし (`key#通し番号`) を表に置き、返った表にしるしがあるかで
  取れたかを判断してから消す。取れなければ 1 ms から倍にして 8 ms まで眠って試し直す (622ff0d、2026-09-30)。

### 文字列とメモリ
- **アキュムレータは渡したら使わない** (`mulay.rt.deferred/elems`)。`json/arr-elem` に渡した `acc` をその後も使うと、
  渡すたびに断片全体をコピーする (8b675c9、2026-10-03)。
- **プロセッサに渡した Event は、その後で読まない** (`mulay.rt.engine/run-procs`)。失敗のときの flow stack は、
  プロセッサが返した Event (`e2`) の frame と callers から作る (flow-ref は失敗のときも両方を戻す)。
  渡す前の Event を読むと、プロセッサごとに Event を写す。プロセッサ 90 万回のフローが 0.100 秒から 0.089 秒になった (2026-10-23)。
- **よく出る小さな値は定数で共有する** (`mulay.rt.engine/CM-MAP` などの class のメタデータ)。java のメタデータは値の節ごとに
  付けるので、節ごとに作ると割り当てが 3 倍になる (5793c63、2026-10-03)。
- **読み終えたカーソルは Source を捨てる** (`mulay.rt.stream` の `dead-src`)。Source の閉包が掴んでいる大きな値を、
  登録から消す (leave) まで持たないため (f6eabff、2026-10-03)。
- **JAR から起動したとき、JAR のバイト列を持たない** (`mulay.mule.load/jar-res`、`jar-skip?`)。アプリの資源だけを展開して
  メモリの表にする。max-core の JAR は 73 MB のうち 70 MB 余りが repository/ で、JAR のまま持つと RTF で RSS が 140 MB に
  なった (8e52f4b、2026-10-12)。
- **待ち受けの前に `sys/free-os-memory` を呼ぶ** (`mulay.app.run/serve`)。clay は手放した大きな塊を既定で 10 秒後に OS に
  返すので、RTF の Pod で READY の時点の RSS が JAR の大きさだけ多く見える。max-core の JAR で 103 MB → 34 MB
  (d9a37ed、2026-10-13、clay 0.86.4)。
- **OTel の送り出しのスレッドには Running を引数で渡さず、`RUNNING` の atom から読む** (`mulay.app.otel/start`)。
  `future` の引数は Dyn として渡るので、clay 0.87.0 は「どの Dyn も Running (App と、Atom(Dyn) を捕まえた閉包を持つ)
  でありうる」とみなし、Atom(Dyn) に書く所すべて (25 か所) で循環の警告を出した。実際には引数はどこにも格納されないが、
  Running を Dyn にしなければ警告は根から消える (2026-10-17)。

### clay.http と clay.sys
- **run-server の `local-port` で要求を受けたポートを知り、経路はポートごとに引く** (`mulay.app.run/handle-app`。clay 0.51.2)。
- **1 つの `http/ServerOpts` の Server (外から止める口) は 1 回の run-server 専用**。ポートごとに新しく作る
  (`mulay.app.run/port-opts`)。
- **run-server が bind できるのは "" (全インターフェース) と IPv4 の数字だけ**。`localhost` は `127.0.0.1` にし
  (`mulay.app.run/bind-host`)、それ以外の名前は run-server が起動の失敗にする。挙動の違いは docs/compat/deviations.md
  (bec8edf、2026-10-04)。
- **READY は全ポートが待ち受けを始めてから** (`mulay.app.run/wait-listeners`、clay 0.86.3 の `http/wait-listening`)。
  開けなかった理由は wait-listeners だけが言う (`serve-port` でも言うと 2 度出る)。f271218、2026-10-12。
- **終了のシグナルは、スレッドを作る前に `sys/block-signals` で全スレッドから止め、専用のスレッドで受ける**
  (`mulay.app.run/serve`、`watch-signals`)。watch-signals は最後にプロセスを終える (戻らない) ので future-detach で
  起こして待たない。止められて run-server が戻ったら、後始末は watch-signals のスレッドに任せる (29bd000、2026-09-30、clay 0.58)。
- **chunked で返す本文が手元にあって 1 MB 以下なら、future を立てずにハンドラの中で sink に書いて閉じる**
  (`mulay.app.run/chunked-resp`、`INLINE-CHUNKED`)。sink は 4 MiB までためられるので止まらない。clay 0.88.0 の run-server は
  接続ごとの green task で、`future` は別のスレッドへの受け渡し (futex) になる。DW の出力 (AUTO で chunked) の要求ごとに
  future を立てていたため、bench の echo が 90k から 42k req/s に落ち、strace で要求 1 件あたり futex が約 3.7 回出た
  (2026-10-17)。大きい本文は今までどおり別の task で書く。

## 理由
- どれも、単純に書き直すと過去に実際に起きた不具合 (プロセスの異常終了、RSS の増加、割り当ての増加、2 乗のコピー、
  コア間の競合、準備完了の前の要求の Connection refused) が戻る。コメントを消すと理由が分からなくなるので、ここに残す。

## 場所
- `mulay.app.run`: ns の `c-flags`、`Server`、`serve`、`port-opts`、`bind-host`、`wait-listeners`、`serve-port`、`handle-app`、`watch-signals`
- `mulay.cli.main/Boot`、`mulay.cli.opts/serves-app?`
- `mulay.rt.engine`: `run-parallel`、`par-workers`、`MAX-PAR-WORKERS`、`sem-acquire`、`CM-MAP`
- `mulay.rt.ops`: `MAX-BACKGROUND`、`spawn-bg-in`
- `mulay.app.run`: `chunked-resp`、`INLINE-CHUNKED`
- `mulay.rt.deferred/elems`
- `mulay.rt.stream` (`dead-src` を使う所)
- `mulay.mule.load`: `jar-res`、`jar-skip?`
- `mulay.app.otel/start`
