# テストフィクスチャの形式

## DataWeave の golden (`.dwt`)

`test/fixtures/dw/<分類>/<名前>.dwt`。1 ファイルに 1 ケース。行頭が `%%% ` の行でセクションを区切る。

```
%%% note
由来: mulet test/mulet/string_test.clj の camelize
%%% script
%dw 2.0
import camelize from dw::core::Strings
output application/json
---
camelize(payload.s)
%%% input payload application/json
{"s": "customer_first_name"}
%%% output application/json
"customerFirstName"
```

| セクション | 意味 |
|---|---|
| `script` | DW スクリプト (必須)。`output` 指示子は必ず書く (既定の出力形式の差で揺れないように) |
| `input <name> <mime> [k=v ...]` | 入力。0 個以上。本文がそのままバイト列になる。`k=v` は reader のプロパティ |
| `output <mime>` | 期待出力 (成功時) |
| `error` | 期待エラー (失敗時)。本文は実 DW のメッセージの 1 行目 |
| `note` | 由来など。評価には使わない |
| `mask` | 本文の各行が正規表現 (Java と同じ)。期待と結果の一致部分 (グループがあればグループ 1) を `***` にしてから比べる。now()、uuid()、乱数、multipart の境界などの揺れる値に使う。期待値そのものはオラクルが書いた生の値のまま |
| `env` | 本文の各行が `NAME=VALUE`。環境変数をちょうどこれだけにして評価する (オラクルはこの環境の子の JVM で、dwt はプロセスの環境を入れ替えて)。envVars()・envVar()・TZ に依存する例に使う |
| `variants <n>` | オラクルの fill が n 回評価し、出た結果をすべて期待 (output / error) として書く。dwt と check はどれかに一致すれば通る。乱数で分岐する例に使う |

- 期待値 (`output` / `error`) は**人が書かない**。`tools/dw-oracle/dw-oracle fill <files>` で実 Mule の DataWeave (4.11.3 同梱の 2.11.2) に書かせる。
- `tools/dw-oracle/dw-oracle check <files>` で期待値と実 DW が食い違うものを報告する (DW の版を上げたときの確認用)。
- mulay 側の実行器 (src/mulay/cli/dwt.clay。`tools/dwt-all.sh` が全件を回す) は同じファイルを読み、`output` と完全一致するか、`error` なら失敗することを確かめる。エラー文言の一致は別の指標として数える。
- 本文の末尾の改行 1 つは区切りとして扱い、中身に含めない。

## アプリの golden シナリオ (`.scn`)

`test/fixtures/apps/<name>/` に Mule プロジェクト 1 つと、そのシナリオ `scenario.scn` を置く。
`templates/` のテンプレも、ここへの symlink (`apps/agent-harness` → `templates/agent-harness`、`apps/stat-models` → `templates/stat-models`) で同じ照合に入れる。
設定だけ違う照合は、テンプレの pom.xml・mule-artifact.json・src への symlink と自分の scenario.scn (`%%% jvm` の `-D`) を
持つディレクトリにする (`apps/agent-harness-summary`)。

```
test/fixtures/apps/<name>/
  pom.xml                 tools/mule-oracle/new-pom.sh <dir> http [apikit] [vm] [os] [file] ... で生成 (指定できる名前は new-pom.sh の先頭)
  mule-artifact.json
  src/main/mule/*.xml
  src/main/resources/*    config.yaml、api/*.yaml、dwl/*.dwl など
  scenario.scn
```

`.scn` は `.dwt` と同じく、行頭が `%%% ` の行でセクションを区切る。セクションは上から順に実行する。
1 ファイルに request / response の組をいくつでも書ける (状態を持つアプリ (ObjectStore、File、
round-robin) は、前の request の結果を前提にしてよい)。

```
%%% note
何を確かめるアプリか (README の代わり)
%%% port 18101
%%% mask
"timestamp": "([^"]*)"
%%% request POST /hello?x=1 headers=location log
Content-Type: application/json

{"x": 1}
%%% response 200
content-type: application/json; charset=UTF-8

{
  "timestamp": "***"
}
%%% log
INFO org.mule.runtime.core.internal.processor.LoggerMessageProcessor: Hello
```

| セクション | 意味 |
|---|---|
| `note` | 自由記述。先頭の note にそのアプリで何を確かめるかを書く |
| `port <n>` | request の既定の宛先ポート (必須)。アプリごとに 18xxx 台で重ならないように決める。全アプリを 1 つの実 Mule に載せるので、アプリの http:listener-connection のポートも他のアプリと重ねない (mule-oracle は起動の前に `%%% port` と数で書いた listener のポートの重なりを調べて止まる)。2 つ目以降の `port` は宛先ではなく、アプリが開く他のポートで、起動を待つだけ (複数の listener-config を持つアプリで、request の前にすべてのポートが開いているようにする) |
| `request <METHOD> <target> [opt...]` | 送る要求。`<target>` はパス + クエリ (パーセントエンコード済みでそのまま送る)。`:<port>/path` と書くと別ポートへ送る。本文はヘッダ行、空行、ボディ。先頭が空行ならヘッダ無し。空行が無ければボディ無し |
| `response <status> [crlf\|base64]` | 期待応答。**人が書かない** (オラクルが書く)。本文は記録したヘッダ行、空行、ボディ |
| `log` | 期待ログ (request に `log` を付けたときだけ)。オラクルが書く。request に `logwait=<秒>` を付けると、ログを集める前に少なくともその秒数待つ (非同期の source のフローが後から書くログ) |
| `mask` | 本文の各行が正規表現。以後のすべての応答 (ヘッダ値・ボディ・ログ) で一致部分を `***` に置き換えてから記録・比較する。グループがあればグループの部分だけを置き換える。揺れる値 (now()、random()、UUID、Java のオブジェクトのハッシュ、ephemeral port) に使う |
| `capture <NAME> header:<ヘッダ名>` / `capture <NAME> regex:<正規表現>` | 直後の request の応答 (mask をかける前の生の値) から値を取って NAME に入れる。regex はボディに探し、最初のグループ (無ければ一致全体) を取る。見つからなければ空。以後の request の `<target>`・ヘッダ・本文にある `{{NAME}}` をその値に置き換えて送る (MCP の Mcp-Session-Id のように、応答ごとに揺れる値を次の request へ渡すため)。取る値が揺れるなら `mask` で応答の記録からは伏せる |
| `wait <ms>` | 次へ進む前に待つ |
| `oracle mulay` | 期待を実 Mule ではなく mulay で記録するアプリ (実 Mule と意図して違う振る舞いだけを確かめるもの。今は gRPC のクライアントのストリーミング)。`fill` / `check` はビルド (XSD の検査) だけして実行しない。期待は `mule-oracle mulay --record <app>` で書き、中身は人が確かめる |
| `jvm <引数>...` | 実 Mule の JVM に足す引数 (`-Dmule.http.service.implementation=NETTY` など)。引数が違うアプリは別々の Mule で順に走らせる。mulay には `-Dk=v` だけを `k=v` として渡す (`mulay run <app> k=v`) |
| `request ... stream=<名前>` | 応答が閉じない (SSE) request。応答の先頭 (ヘッダと、届かなくなるまでに届いた本文) を記録し、接続は開けたままにして次へ進む。`capture` は先頭の本文に効く |
| `read <名前> [wait=秒]` | `stream=` で開いた接続に、前回から新しく届いた本文 (少なくとも `wait` 秒 (既定 0.3) 待ち、届かなくなるまで待つ)。期待の応答 (`response 200`) が続く |
| `close <名前>...` | `stream=` の接続を閉じる (シナリオの終わりにも閉じる) |
| `emptydir <path>...` | そのディレクトリを消して空で作り直す (File コネクタのアプリの作業場所) |
| `mkfifo <path>...` | 名前付きパイプを作る (既にあれば消して作り直す)。git に置けない特殊なファイルの試験用 |
| `rawserver <port> <mode>` | 127.0.0.1:port に、要求を読み終えてから壊れた応答を返す TCP の相手を立てる (シナリオの終わりまで)。コネクタの接続の失敗の文言を記録するため。mode は `close` (何も返さずに閉じる)、`reset` (RST で閉じる)、`garbage` (`HELLO WORLD` を返して閉じる)、`nocolon` (コロンの無いヘッダ行)、`short` (Content-Length 100 に 5 バイトだけ返して閉じる)、`chunked-cut` (最後の chunk を送らずに閉じる)、`status-4096` / `status-4097` (状態行の長さ、CRLF を除く)、`head-8192` / `head-8193` (ヘッダ行の長さの合計、各行の CRLF を除く)。ポートは `port` と同じく他のアプリと重ねない |
| `symlink <target> <link>` | link を target への symlink にする (既にあれば消して作り直す) |
| `grpcserver <port>` | 127.0.0.1:port に、h2c (prior knowledge) で受ける gRPC のスタブを立てる (シナリオの終わりまで)。gRPC のクライアント (`grpc:unary-call`) の応答の扱いを記録するため。振る舞いはメソッド名 (パスの最後) で決まり、メッセージはバイト列のまま扱う: `Echo` (要求の最初のメッセージを返す)、`Headers` (要求のヘッダを `名前: 値` の行にしてフィールド 1 で返す)、`Fail` (grpc-status 5、パーセント符号化した grpc-message)、`TrailersOnly` (最初の HEADERS に grpc-status 7)、`Garbage` (枠の壊れた本文)、`BadProto` (protobuf として読めないメッセージ)、`Http503`、`NoStatus` (trailer 無し)、`Empty` (メッセージ無しの成功)、`Two` (メッセージ 2 つ)、`Bare` (grpc-status 13 で grpc-message 無し)、`Odd` (grpc-status 99)。ほかの名前は grpc-status 12 | ストリーミングのメソッド (Ticks、TicksSlow、TicksFail、TicksDeny、Sum、SumEarly、Chat、ChatFail) もある (一覧は tools/mule-oracle/mule-oracle の GrpcServer)。環境変数 `MULE_ORACLE_GRPC_TRACE=<ファイル>` を付けると、スタブが受けた出来事 (呼び出しの開始、メッセージ、終わり) を時刻付きで書く
| `send <名前> [end=1] [raw=1]` | `request GRPC .. stream=<名前>` で開いた gRPC の呼び出しに、本文のメッセージ (1 行に 1 つの JSON) を同じストリームで送る。`end=1` で要求の側を閉じる。応答は前回から新しく届いたメッセージと、届いていれば trailer |
| `protoset <file.desc>` | gRPC の要求 (`request GRPC`) のメッセージを JSON と protobuf で行き来させる記述子 (protoc の `--descriptor_set_out`。パスはアプリのディレクトリから) |
| `request GRPC :<port>/<pkg.Service>/<Method> in=<要求の型> out=<応答の型> [raw=1]` | h2c (prior knowledge) で gRPC の要求を 1 つ送る (Python の h2)。本文は 1 行に 1 つのメッセージの JSON (`stream=<名前>` なら呼び出しを開いたままにし、`end=0` なら要求の側も閉じない。続きは `send` / `read [wait=秒]` / `close`。応答の頭がまだ来ていなければ `response pending` と記録し、来た時の `send` / `read` がその status とヘッダーの行を記録する。空なら `{}` を 1 つ。`raw=1` なら base64 のバイト列。`frame=0` なら本文の base64 をそのまま DATA で送り、5 バイトの枠を付けない。空なら DATA を送らない)。ヘッダ行は要求のメタデータ。応答は `%%% response <HTTP の status>` に、ヘッダ (`date` などを除く全部) と trailer (`名前 (trailer): 値`)、本文は受けたメッセージを 1 行に 1 つ (out の型の JSON、キーは proto のフィールド名で並べ替え。読めなければ `base64 ..`、gRPC の枠にならない残りは `rest ..`) |
| `sfauth <org> <path>` | OAuth の認可コードの手順を自動で通す。sf CLI の org (別名) のセッションで Salesforce にログインした状態 (frontdoor.jsp) を作り、アプリの `<path>` (認可の口) からリダイレクトをたどってアプリのコールバックまで行く (Salesforce が https から http のコールバックへ戻すときの `window.location.replace(..)` のページも、アプリのポートの localhost 宛てならたどる)。最後の応答を request と同じく記録・比較する (`%%% response` が続く) |
| `requires <path>...` | アプリのディレクトリからの相対パスのファイルが要る (認証情報のようにリポジトリに入れないもの)。無ければ、app を指定せずに走らせたときはそのアプリを飛ばす |
| `tls <port> [cert key]` | そのポートへの request を TLS で送る (サーバの証明書は検証しない、ALPN は http/1.1。`h2=1` の request は h2)。cert / key (アプリのディレクトリからの相対パス、PEM) があればクライアント証明書を出す |
| `startdir <path>...` | アプリを起動する前に、そのディレクトリを消して空で作り直す (書いた順)。file:listener が見るディレクトリのように、起動の時点で要るもの |
| `sftpdir sftp://<user>:<password>@<host>:<port> <path>...` | `startdir` の SFTP 版。アプリを起動する前に、SFTP サーバーの上でそのディレクトリを消して空で作り直す (書いた順。lftp を使う)。sftp:listener は起動の時点でディレクトリが無いと止まるため |
| `startsql <PostgreSQL の URI>` | アプリを起動する前に、本文の SQL を psql で流す (失敗したら止まる)。db:listener が見る表のように、起動の時点で要るもの |

request のオプション:

- `headers=a,b` — `content-type` に加えて記録・比較する応答ヘッダ。`headers=*` は全ヘッダから揺れるもの (`date`、`content-length`、`transfer-encoding`、`connection`、`keep-alive`) を除いたもの。`framing=1` を足すと `content-length` と `transfer-encoding` も残す (chunked かどうかを確かめる用)。
- `log` — その request の間にアプリのログに出た `LoggerMessageProcessor` の行を記録する。`log=*` は全カテゴリ、`log=cat1,cat2` はそのカテゴリだけ。1 行の形は `<LEVEL> <category>: <message>` (複数行のメッセージは続けて書く)。
- `timeout=<秒>` — 応答待ちの上限 (既定 30)。応答が無ければ `response none` と記録する。
- `crlf` / `base64` — 要求ボディの表記 (下記と同じ)。
- `repeat=<N>` — 要求ボディを N 回繰り返して送る (大きな本文を確かめる用。シナリオに書くのは 1 回分)。
- `h2=1` — HTTP/2 で送る (Python の h2)。平文のポートは h2c (prior knowledge)、`tls` のポートは ALPN で h2 だけを申し出て、h2 が選ばれなければ `response none` になる。本文は相手の流れの制御の窓に従って分けて送る。

### 送り方 (mulay 側の実行器も同じにする)

- 1 request ごとに新しい TCP 接続で HTTP/1.1 を送る。付けるヘッダは `Host: localhost:<port>`、シナリオに書いたヘッダ (書いた順)、ボディがあるか method が POST/PUT/PATCH なら `Content-Length`。**それ以外は付けない** (User-Agent、Accept、Accept-Encoding も付けない。エコーするアプリの応答が変わるため)。
- 同じアプリの request は順に送る。アプリ同士は並行に走らせてよい。

### 比較の正規化

- **ステータス**: 数値の一致。reason phrase は比べない。
- **ヘッダ**: 名前は小文字にして記録・比較する。値は前後の空白を除いて完全一致。記録するのは `content-type` と `headers=` で指定したものだけ (指定したヘッダが応答に無ければ記録しない = 「無い」ことを期待する)。同名ヘッダが複数あれば受け取った順に複数行。
- **ボディ**: mask を適用したあと、バイト列として完全一致 (JSON の整形・インデント、XML 宣言、CSV の末尾改行まで含めて比べる)。`.dwt` と同じく、セクション本文の末尾の改行 1 つは区切りでボディに含めない。
  - UTF-8 として読めない、または制御文字を含むボディは `response <status> base64` とし、本文を base64 で書く (mask は効かない)。
  - 改行がすべて CRLF のボディは `response <status> crlf` とし、LF で書く。
- **ログ**: mask を適用したあと、行の並びを完全一致で比べる。

### オラクル (`tools/mule-oracle/mule-oracle`)

```bash
tools/mule-oracle/mule-oracle fill                    # 全アプリの response / log を実 Mule で書き直す
tools/mule-oracle/mule-oracle fill core-try http-test # 一部だけ
tools/mule-oracle/mule-oracle check                   # 食い違いを表示 (終了コード 1)
tools/mule-oracle/mule-oracle run core-try            # デプロイして止まる。手で叩いて調べる用 (Ctrl-C で停止)
tools/mule-oracle/mule-oracle clean                   # 私的ランタイムとビルド物を消す
```

- アプリを `target/mule-oracle-build/<name>/` へ複製して `mvn -q -o package -DskipTests` でビルドする (前回より新しいファイルが無ければ飛ばす)。
- 実 Mule 4.11.3 (`~/srv/mule-enterprise-standalone-4.11.3`、`MULE_ORACLE_HOME` で変えられる) は**読むだけ**。起動は私的なコピー `target/mule-oracle-runtime/` で行う (lib・services・server-plugins はハードリンク、bin・conf は複製。`wrapper.conf` からはユーザー独自の javaagent や `mule.verbose.exceptions` を除き、全アプリを 1 つの JVM に載せるため `MaxMetaspaceSize` を 2048m にしてある。既定の 256m では 30 本ほどで `OutOfMemoryError: Metaspace` になる)。apps・logs・.mule は毎回作り直す。
- 全アプリを 1 回の起動でまとめてデプロイし、`apps/<name>-anchor.txt` ができ listener のポートが開いたら request を送る。デプロイの失敗理由はログから拾って表示する。
- 終了時 (例外・Ctrl-C を含む) に Mule のプロセス (wrapper と、別プロセスグループの java) を必ず止める。
- 所要時間の目安 (2026-10-16、92 アプリ・2,574 request、`check` 全体で約 6 分): 既定の JVM の 84 アプリは、ビルド 11 秒 (変更が無ければ 0 秒)、
  起動とデプロイ 79 秒、request 128 秒。`%%% jvm` の違う 8 組は 1 アプリずつ起動し直し、それぞれ 15〜35 秒。
- アプリのログは次の実行まで `target/mule-oracle-runtime/logs/mule-app-<name>.log` に残る。

### mulay で同じシナリオを動かす (`mule-oracle mulay`)

```bash
tools/mule-oracle/mule-oracle mulay [-v] [-j N] [--lazy|--lazy-local] [app...]
```

- `target/mulay` を使う (無いか、src より古いか、作った clay の版 (`target/mulay.clay-version`) が今の clay と違えば `clay build src/mulay/cli/main.clay -o target/mulay` で作り直す。`MULAY_BIN` で別のバイナリを指定すればそれをそのまま使う)。
- アプリごとに `target/mulay run <app dir>` を起動し、`%%% port` のポート (2 つ目以降も) が開くまで最大 10 秒待つ。開かない・途中で終了したときは、そのプロセスの出力の末尾を表示して FAIL にする。
- request の送り方と比較の規則はオラクルの `check` と同じ (mask、`headers=`、`emptydir` なども同じに効く)。記録済みの response / log と比べるだけで、`.scn` は書き換えない。
- ログ: mulay は `INFO  2026-09-28 12:00:00,123 [[app].flow] <category>: <message>` の形で出す (レベルは 5 桁に詰める。複数行のメッセージは次の行以降にそのまま続く。WARN/ERROR は stderr)。stdout と stderr の両方を読み、`<LEVEL> <category>: <message>` に直して比べる。どのカテゴリを比べるかは `log` / `log=*` / `log=cat` の指定どおり。
- 出力は `PASS <app> (n/m) <秒>s`、または `FAIL <app> request #k: <METHOD> <target>: <差分の要約>` (`-v` で差分の全文)。最後に通った request の数/全数を出し、1 件でも落ちれば終了コード 1。
- 既定ではアプリを 1 つずつ順に動かし、終わるたびに (Ctrl-C のときも) プロセスグループを止める。`-j N` は `%%% jvm` が同じアプリ
  (実 Mule の照合では 1 つの Mule に載せて同時に回すもの。ポートが重ならないことはオラクルが確かめている) を N 個まで同時に回し、
  `%%% jvm` が違う組は順に回す。同じ外のサービス (Salesforce・Anypoint MQ・DB・SFTP。アプリの XML の要素の接頭辞で見る) を使う
  アプリは、そのサービスごとの 1 つの列で順に回す (Pub/Sub やストリーミングの通知、キューのメッセージを他のアプリと取り合うため)。
  `--lazy` は各アプリを `MULAY_DW_LAZY_ALL=1` でも回す (`<app> [lazy]` と出し、最後の行は `mulay:` と `mulay lazy:` の 2 つ。列の中は
  通常を全部回してから遅延を回す。同じアプリを続けて回すと、前の回が受け取り途中だった MQ のメッセージが配り直されて届く)。
  `--lazy-local` は遅延を外のサービスを使わないアプリだけで回す。確認一式 (`tools/gate.sh`) は `-j 4 --lazy-local`、`--full` で `--lazy`。

## MUnit のテスト (`test/fixtures/munit/<name>`)

fixture は MUnit のテストを持つ Mule のアプリ (pom.xml、src/main/mule、src/test/munit/*.xml)。
期待は `expected.txt` で、人は書かない (オラクルが書く)。

```
suite basics-test.xml
test a02-equal-num FAILURE
| java.lang.AssertionError:  at file: [basics-test.xml], line: [24]
| Expected: 5
|      but: 4 as Number {encoding: "UTF-8", ...} at (root)
test a01-equal-ok SUCCESS
```

- suite の名前、テストの名前の順に並べる。結果は SUCCESS / FAILURE / ERROR / SKIPPED。
- 失敗の文言は surefire の報告の先頭から、スタックの行 (`\tat ..`) と `Caused by:` の手前まで。各行の末尾の空白は落とす。
- `tools/munit-oracle/munit-oracle fill [name...]`: fixture をコピー (target/munit-oracle/<name>) して実 MUnit (`mvn test`、munit-maven-plugin 3.7.4、MULE_EE 4.11.3) を回し、expected.txt を書く。
- `tools/munit-oracle/munit-oracle mulay [-v] [name...]`: `mulay test <fixture> --golden <tmp>` の結果と expected.txt を比べる (MULAY_BIN で mulay を替えられる)。


## DW の XML の読み手のスナップショット (`test/fixtures/xml-read`)

`docs.lp` は文書の集まり、`expected.lp` はそれを DW の XML の読み手で読んだ結果。どちらも「長さ (10 進のバイト数)、改行、中身、改行」を
並べた形で、中身に任意のバイト (制御文字や壊れた UTF-8) を置ける。試験は test/fmt/xml_snapshot_test。

- 文書: test/xml の塊の試験 (DOCS)・expat の試験・test/fmt の遅延の試験 (LAZY-DOCS) の文書、名前空間・属性・空白だけのテキスト・
  深さと属性の数の上限・ベンチと同じ形を突く文書、xml_fuzz_test の文書と注文の文書を 1 バイトずつ壊した文書 (2026-10-30 に作った)。最後の 6 つ (空白だけのテキストが注釈や処理命令を
  はさんでテキストの後に続く文書) は読み手を書き換えた後に足したので、期待は書き換え前のコード (6bbd7602) で作った。
- 記録: 文書ごとに読み手のプロパティ 6 通り (無し、nullValueOn empty・none、maxAttributeSize 3、supportDtd、supportDtd と
  maxEntityCount 2) で、全部を読んだ結果 (writeAttributes 付きの JSON か `ERR 誤りの文言`) と、塊の大きさ 1・2・3・7・64・1000000 で
  遅延して読んだ結果を 1 文字ずつ (`L` 全部を読んだ結果と同じ、`N` 遅延にしない、違えば `D:` と遅延の結果)。
- 期待は読み手の動きを意図して変えた時だけ作り直す: `MULAY_XML_SNAPSHOT_WRITE=1 clay test test/fmt` (今のコードの結果を書く)。
