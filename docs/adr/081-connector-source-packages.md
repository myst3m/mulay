# ADR 081: コネクタは本体と別のソースの package として配り、入り口のファイルが使うコネクタを並べる

日付: 2026-10-19。状態: 決定 (段 1 から順に進める)。ADR 049 (要素の名前付けの契約) と ADR 051 (コネクタの record) の続き。

## 背景

- ユーザーは、コネクタを本体と別に配り、後から足したい。
- `.so` を実行時に読み込む形はやめた (ユーザーと clay の判断)。理由は 2 つある。
  - 動的ロードはセキュリティの危険が大きい。
  - Clay は record の番号をプログラムごとに決めるので、本体と `.so` で型の並びを揃えるのに大きな変更が要る。
- 代わりに clay 0.94.0 の git 依存 (clay の ADR 111) を使う。
  - `clay.pkg` に `git: <url> <commit>` と書くと、ソースを取ってきて全体を 1 つのプログラムとして翻訳する。
  - commit は完全な hash だけを受け付ける。
  - 取ってきた package は、自分の checkout の外を読めない。

## 決定

1. **配る形**
   - コネクタの package は、Clay のソースの package (`clay.pkg` と `.clay`) にする。
   - 使う側の package (配布物) は、mulay の本体を `dep:` か `git:` で、コネクタを `git:` で並べ、全体を一緒にビルドする。
   - 型の並びや ABI の問題は起きない。
2. **コネクタの package は mulay の repository を git: で固定し、配布物も同じ url・同じ commit で mulay を書く**
   (2026-10-19 ユーザーの判断)
   - clay は、取ってきた package が読める module を次の 3 つに絞った (dc9acb9a)。
     - 自分の checkout の中
     - 自分の `clay.pkg` に `git:` で書いた package
     - stdlib
   - 上のプログラムの root にある module は読めない。前に確かめた、mulay を書かずに `mulay.rt.conn` を読む形は、もう通らない。
   - 1 つの url に使える commit はプログラム全体で 1 つなので、配布物とすべてのコネクタは、mulay の同じ commit を書く。
     - 配布物は mulay を `dep:` (path) でなく、コネクタと同じ url の `git:` で書く。path と git の両方にあると、同じ ns が 2 つの file になって誤りになる。
     - mulay にリリースの区切り (その commit) を作り、コネクタはそれに合わせて固定を上げる。
   - コネクタが使う口だけを小さい repository に分ける形は採らなかった。今の `rt/conn` は Event、DW の値、Mule のモデルをそのまま見せていて、分けるには大きな作り直しが要るため。外のコネクタが増えて、固定を揃える手間が問題になったら考え直す。
3. **入り口のファイルが、使うコネクタを並べる**
   - 起動の状態 `BOOT` は、入り口の ns の大域の def に置く。worker のスレッドが参照数を書かずに共有するためで、7742fa7 で入れた。
   - 処理の本体は `mulay.cli.boot` に置き、コネクタの列を引数で受け取る。
   - 入り口の ns は、`(def BOOT (boot/boot-from-argv CONNS))` と `(defn main Int [] (boot/main BOOT))` だけを持つ。
   - 本体の `src/mulay/cli/main.clay` は、組み込みの全部 (`mulay.conn.registry/all`) を並べる入り口のままにする。`clay build src/mulay/cli/main.clay`、`target/mulay`、mule-oracle、`tools/test.sh` は変わらない。
   - 配布物は自分の入り口のファイルを持ち、`mulay.cli.main` を `:require` しない。
4. **`Connector` は `conn/connector` で作り、残りは `assoc` で足す**
   - 外の package が位置引数の `->Connector` を使うと、`rt/conn` にフィールドを足すたびに壊れる。
   - 組み込みのコネクタも同じ書き方に揃え、`->Connector` を使うのは `rt/conn` の中だけにする。
   - 足すフィールドには、何もしない既定の値を付ける。
5. **コネクタの知識は、コネクタが持つ**
   - 今は本体の層に、コネクタごとの知識が直接書かれている。これを順に `Connector` のフィールドへ移す。
   - mule の層 (parse) は conn を `:require` できない。そこで呼ぶ側 (cli、app) が、コネクタの列から表を作って渡す。

   | 今ある場所 | 知識 | 移す先 |
   |---|---|---|
   | `mule/parse` の `GRPC-SOURCES` | grpc の source の要素名 | 今ある `Connector` の `uri` と `sources` から作る (uri → source の名前の表) |
   | `mule/parse` の `op-chain-names` | a2a の操作の中のプロセッサ列の名前 | `:op-chains` |
   | `mule/parse` の `op-each-child?` | validation:all / any の子ごとの経路 | `:op-each-child` |
   | `rt/error` の `SALESFORCE-COMPOSITE:*` | エラーの型の親 | `:error-parents` |
   | `app/run` の numberOfConsumers の既定 (`vm` は 4) | 並行に回す数の既定 | `:consumers` |
   | `app/run` の a2a・mcp・grpc・salesforce の oauth-callback | http:listener のポートに経路を足すソース (ADR 043) | 汎用の口 (経路と処理の関数) |
   | `mule/ignored` | XSD にあって実装しない属性 | 当面は本体に残す。`tools/ignored-attrs.py` が生成して `tools/test.sh` が検査するため。外のコネクタは名前で推す今の扱いになる |

## 段ごとの記録

- 段 3 (2026-10-19): `Connector` の `:source-elems`・`:op-chains`・`:each-child` を `conn/parse-hints` が `m/Hints` にし、`LoadOpts` で parse に渡す (ADR 049 にも書いた)。
- 段 4 (2026-10-19):
  - エラーの型の親は、コネクタが `:error-parents` (`"NS:ID" "親"` を並べた列) に書く。`rt/error` の `PARENTS` には `MULE:` の型だけを残した。
  - `err/parent` は、`err/matches?` などの奥で引数なしに使われる関数なので、コネクタの表は `rt/error` の大域の Atom (`CONN-PARENTS`) に置く。`app/run` の `prepare` が、コネクタの `init` (ADR 044 の裏の接続の用意) より前に書き、`en/new-ctx` も同じ値を書く (単体テストのため)。書くのは起動の時だけで、その後は読むだけになる。
  - numberOfConsumers の既定は `:consumers` (既定は 1、vm は 4)。
  - `rt` にまだ残っているコネクタの知識は 2 つある。これらは、外のコネクタが要るようになった時に移す。
    - `rt/error` の `HTTP` の例外のクラス名
    - `rt/event` のカーソルの失敗の既定 (`DB:QUERY_EXECUTION`)
  - (2026-10-20) 上の 2 つも移した。rt はコネクタの名前を持たなくなった。
    - 例外のクラス名は、コネクタが `:error-classes` (`"NS" "クラス"` を並べた列) に書く。`CONN-PARENTS` と同じ形で、`rt/error` の Atom (`CONN-CLASSES`) に `prepare` と `en/new-ctx` が書く。`err/exception-class` は、cause、`MULE:EXPRESSION` の次にこの表を引く (前の `HTTP` の行と同じ位置)。
    - カーソルの失敗の型は、カーソルを作るコネクタが `ev/tv-cursor-typed` (db) か `ev/tv-cursor-of` (grpc) で渡す。型の無いカーソルは `MULE:UNKNOWN` にする。今カーソルを作るのは db と grpc だけで、どちらも型を渡すので、振る舞いは変わらない。
- 段 5 の口 (2026-10-20): `Connector` の `:mounts` (`Fn(m/App Values(Vec(Mount) Vec(Str)))`、既定は何も足さない) を足した。
  - `Mount` は listener の設定の名前、経路、メソッド、basePath の下に付けるか (`:base`。grpc は付けない)、要求の本文を流して読むか (`:stream`)、処理 (`Fn(Host At hm/Request hm/Response)`) を持つ。
  - `app/run` が listener の設定を引いてポート・basePath・TLS を決め、無ければ今と同じ "Listener config 'x' not found" を起動の誤りにする。
  - `Host` は Ctx を要る関数だけ (フローを番号で動かして記録する `run`、式を評価する `eval`・`eval-tv`・`eval-str`) を持つ。`app/run` の `serve-port` がポートごとに 1 回作る。Ctx を要らない関数 (`en/java-str` など) は、コネクタが `rt/engine` を直接 `:require` して使う。
  - 処理を呼ぶのは `handle-app` の中で、405 の検査の後、`ops/enter`/`leave` の内側にする (停止中の 503 と運用の端点は今と同じ)。listener の経路だけが行う `stream/enter`、`mt/flow-dispatched`、`am/record!`、x-correlation-id は呼ばない。
  - 経路の順は、listener (フローの順)、コネクタの列の順の mount になる。`find-route` は点が同じなら先のものを選び、起動の誤りもこの順に並ぶ。
  - 同じコネクタの mount が同じ listener の誤りを出すときは 1 つにまとめる (salesforce・a2a・mcp は 1 つの設定から経路を 2 つ足し、前も誤りは設定ごとに 1 つだった)。
- 段 5 の salesforce (2026-10-20): oauth-callback-config の authorize と callback の経路を、`mulay.conn.salesforce` の `oauth-mounts` に移した。設定は経路を作る時に引いて処理が持つ (前は要求ごとに設定の名前で引き直していた)。
- 段 5 の grpc (2026-10-20): サーバーの経路と処理 (単項・server-streaming・client-streaming・双方向) を `mulay.conn.grpc` の `server-mounts` と `srv-*` に移した。処理は、フローの名前・source の子・式を経路を作る時に持つ (`Served`)。
  - `Connector` に `:routed` (経路で動くので polling しない source の名前) を足し、`app/run` の `polled-flows` は grpc の名前でなくこれを見る。
  - 本文を流して読む経路は `Mount` の `:stream` で決める (前は grpc の経路だけを `grpc-stream-paths` が集めていた)。
  - 同じ listener の誤りは 1 つになる (前はメソッドごとに同じ誤りが並んだ)。
- 段 5 の mcp (2026-10-20): サーバーの経路と処理 (tool・resource・prompt・on-new-session、SSE の旧い形) を `mulay.conn.mcp` の `server-mounts` と `srv-*` に移し、`mulay.conn.mcp_client` の `"mcp"` のコネクタ (クライアントの操作と同じ名前空間) の `:mounts`・`:routed` に付けた。処理は Host とアプリのフローの列 (`SrvEnv`) を受け取る。
- 段 5 の a2a (2026-10-20): task-listener ごとの JSON-RPC とカードの経路、処理 (認可・通知の設定・非同期・ストリーム) を `mulay.conn.a2a` の `server-mounts`、`task-mounts`、`srv-*` に移した。
  - a2a の経路は、前は listener の経路とフローの順に混ざっていたが、今は listener の経路の後に並ぶ (経路の順の決まりのとおり)。
  - listener の設定の誤りと、カードの能力の誤りが両方あるとき、前は listener の誤りだけを出したが、今は能力の誤りだけを出す (経路を作らないので listener を引かない)。
  - これで `app/run` の `Route` は listener と mount の 2 種だけになり、`app/run` はコネクタの名前を知らない。
- 段 5 の後の測り直し (2026-10-20、h2load、移す前の HEAD 70d5c6b と比べる): http:listener (HTTP/1.1、並行 64) は 1 秒あたり約 13.9 万件で前と同じ (14.0 万)。gRPC の単項 (h2c、並行 64 × 10) は交互に 3 回ずつ測って 33.7〜33.9 万件 (前 33.7〜35.1 万)、server-streaming (並行 128) は 5.2〜5.6 万件 (前 5.4〜5.6 万)。要求ごとの関数の呼び出しを 1 つ挟んでも、測れるほどは遅くならない。
- 段 6 (2026-10-19、clay 0.94.0): 見本のコネクタ `templates/connector` (`toy:shout`) と `tools/pkg-check.sh` を足した。
  - script は、見本を一時の git の repository にして mulay の HEAD を `git: file://` で固定し、配布物 (同じ url・同じ commit の mulay と見本) をビルドする。そのうえでアプリを動かし、要求を 1 つ送る。
  - 取ってきた package (`$CLAY_CACHE/pkgs/<commit>`) は、script が作ったものだけを消す。
  - 見本は、mulay の中の自分で固定した module だけを読むので、clay が塞いだ後 (dc9acb9a) の規則でも通る形になっている。0.94.1 が出たら回し直す。
  - 段 5 より先にした。外のコネクタの形を早く確かめるためで、段 5 は http:listener に経路を足すコネクタにしか効かない。
  - 段 5 の後 (2026-10-20) に、見本に `toy:ping-listener` (`:mounts` で listener に経路を足し、`Host` の `run` でフローを動かす) を足し、script はその経路にも要求を送る。

## 進める順

段はどれも振る舞いを変えない。1 段を 1 コミットにし、単体テストと全シナリオを通してから次に進む。

1. この ADR。
2. 入り口を分ける: `mulay.cli.boot` を作り、`app/run` の `prepare` がコネクタの列を引数で受け取るようにする。
3. parse の表をコネクタから作る: 5 つ目の決定の表のうち、parse の 3 つ。parse の引数が変わるので、test/mparse と inspect / validate も同じコミットで直す。
4. エラーの親と、並行に回す数の既定。
5. (済み) HTTP の経路で動くソースを、汎用の口に移す。コネクタ 1 つを 1 コミットにし、小さい順に進める (salesforce の oauth-callback、grpc、mcp、a2a)。
   - `app/run` の `Route` から、a2a・mcp・grpc のフィールドを除く (済み)。
   - 移したら、http と grpc を h2load で測り直し、要求ごとの間接の呼び出しで遅くなっていないことを確かめる (済み)。
6. (済み) 外のコネクタの証明: 小さいコネクタ (mulay を `git: file://` で固定する) を、同じ url と commit で mulay を書いた配布物に組み込み、シナリオを 1 つ回すテストを置く。

## 決めていないこと

- `mulay build` (アプリを埋め込んだ実行ファイルを作る) は、ADR 082 で決めた (2026-10-20)。入り口の package の stub を差し替えて、配布物の入り口をビルドする。
