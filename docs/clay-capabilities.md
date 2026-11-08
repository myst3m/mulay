# Clay の現状能力(mulet ポーティング設計用)

調べた時点: 2026-09-28、clay 0.51.1(`~/projects/clay`、main `19882e2a`)。
分類: **標準** = 言語か stdlib にある / **FFI** = `c/` で C を呼べば可 / **自作** = 無いので Clay で書く / **不可**。
stdlib は `~/projects/clay/src/clay/*.clay`(計 約 6,100 行)。以下のパスはリポジトリからの相対パス。

**これは調査時点の記録。** 本文は全面には更新していない(一部の行に日付と版を付けて追記した)。今の版は clay 0.86.5。
その後 Clay に入ったもので mulay が使っているもの(版は clay の `Release` のコミット、mulay のコミット、CLAUDE.md による):

- `clay.httpmsg`(0.51.3):HTTP の要求と応答の値。mulay の conn/salesforce・app/run などが使う。
- `clay.charset`(0.53.0):java.nio.charset に合わせた文字集合の変換。mulay の lib/xml・dw/fmt/xml・db/oracle などが使う。
- record のフィールドをキーワードで読む `(:status r)`(0.72.0)。
- `clay.crypto` の要約・AES・ChaCha20(0.82.0)、SHA-3(0.83.0)、公開鍵暗号(X25519、Ed25519、RSA、P-256。0.84.0)。mulay の lib/crypto・lib/hash・lib/ssh・lib/sshkey が使う。
- `clay.pkix`(0.85.0。PEM と PKCS#8 の鍵、PKCS#12 は 0.86.5 で使い始めた):mulay の lib/crypto が RSA の署名と .p12 の鍵に使う。
- `clay.io` の File(pread・pwrite・sync・truncate・バイト範囲のロック。0.85.0)。mulay はまだ使わない(docs/sqlite.md)。
- `clay.tls` が純 Clay になった(0.86.5)。mulay は OpenSSL をリンクせず、libc と libm だけになった。listener のクライアント証明書の検査(mTLS)は 2026-09-29 から clay.tls の設定にある(mulay の conn/http)。
- `str/lower-case`・`str/upper-case` が clay.string に入った(0.86.2。ASCII のまま)。

---

## 0. 要約(mulet の観点)

- **そのまま使える**: HTTP/1.1 と HTTP/2 のサーバとクライアント(TLS・SSE 込み)、JSON、CSV、TLS クライアントとサーバ、green スレッド・チャネル・deadline、プロセス起動、端末 TUI、PostgreSQL(最小限)、SHA-256・HMAC・Base64。
- **自作が要る**: XML(パーサと生成器)、YAML、DataWeave のパーサ(PEG やコンビネータの部品は無い)、BigDecimal、日付時刻とタイムゾーン、正規表現の拡張(`|` なし)、JWT、RSA などの暗号(OpenSSL の FFI で可。AES は 0.82.0 から標準。RSA などの公開鍵暗号は 0.84.0 から標準)、WebSocket、gRPC、FTP/SFTP、MySQL/Oracle/SQLite のドライバ。
- **設計上の注意**: 例外は無い(失敗は戻り値で表す)。コレクションは永続データ構造ではない(共有された Map への `assoc` は複製になる)。GC は無い(参照カウントで、所有権はコンパイラが推論する)。動的な値は `Dyn` に入れる。

---

## 1. 言語の基本

| 項目 | 状態 | 内容 |
|---|---|---|
| 型システム | 標準 | 静的型。ローカル変数は推論し、関数の戻り値型と引数の型は書く: `(defn f Int [x: Int s: &Str] ..)`(`&` は借用)。ジェネリクス(型変数 `a`)は単相化で展開する。`Dyn` は JSON のような動的な値の入れ物で、Dyn を期待する所では値が自動で箱に入る(ADR 037)。空の `[]`/`{}` の型は同じ定義の中の使い方から決まる(実験 110)。 |
| データ構造 | 標準 | `Vec(T)`、`Map(Str T)`(キーは Str)、`Set`、`defrecord`、`defvariant`(タグ付き共用体)、`deftype`(ゼロコストの別名型)、`Values(A B)`(多値)、lazy seq(`range-inf`・`iterate`・`map`)。**永続(HAMT)ではない**: 参照カウントが 1 ならその場で書き換え、共有されていれば複製する(Perceus)。大きな Map を複数の所で持ちながら更新すると O(n) になる。 |
| パターンマッチ | 標準 | `match` は defvariant の網羅検査付き。`case` はリテラル、`cond`、`let` と引数の分解(`[a b]`)。core.match のような任意の構造への照合は無い。 |
| エラー処理 | 標準(設計) | **例外は無い**。失敗しうる関数は `Values(T Str)` を返す(ADR 012)。`get!` などは失敗すると呼び出し側へ戻って巻き戻す(ADR 024)。HTTP ハンドラの失敗は 500 になり、リークしない。`try/catch` は無い。 |
| マクロ | 標準(限定) | `defmacro` はテンプレート型のみ(`` ` `` と `~`/`~@`)。任意のコードを実行するマクロは無い。 |
| モジュール | 標準 | `(ns a.b (:require [clay.json :as json]))`。修飾名での呼び出しが必須。`defn-` で非公開。 |
| パッケージ | 標準(簡素) | ディレクトリに `clay.pkg` を置き、`dep:` でローカルパスを指定。git 依存は未実装。中央リポジトリは無い。 |
| 成果物 | 標準 | 単一のネイティブバイナリ(C 経由、clang)。hello は 82KB(strip 後 77KB)で、起動は約 0.7ms。約 3.8 万行のプロジェクト A は 7.5MB。対象: Linux x86-64(標準)、Windows `.exe`(mingw でクロス)、armv6、裸の x86、`.wasm`(純粋な計算のみ)、`.o`、`.c`。 |
| 数値 | 標準 | Int は 64 ビットで、溢れは wrap(ADR 016)。Float は double。BigInt は `clay.bigint` (0.99.0 から、NTT の乗算)。BigDecimal は無い (mulay.lib.dec)。`fmt-fixed`・`parse-long`・`parse-double`。 |
| 文字列 | 標準 | バイト列(UTF-8 をそのまま持つ)。`count` はバイト数。UTF-8 の文字単位の処理は `clay.term` の `utf8-len`・`utf8-at`・`char-width` 程度で、Unicode の正規化や大文字小文字の表は無い(`upper-case` は ASCII。0.86.2 から `str/lower-case`・`str/upper-case` として clay.string にある)。 |

参照: `docs/current-state.md`、`docs/development/decisions/`(ADR 012・016・021〜037)、`README.md` の「The language」。

## 2. 並行性

| 項目 | 状態 | API |
|---|---|---|
| green スレッド | 標準 | `clay.async`: `go`・`run`・`blocking`・`go-dyn`・`cancel`/`cancelled?`。M:N で、I/O は park する(epoll、Windows は WSAPoll)。`clay.async` を require すれば有効になる(`c-flags` はモジュール側が宣言済み)。 |
| チャネル | 標準 | `chan`・`chan-buf`・`chan-dropping`・`chan-sliding`・`close!`・`alts!`(clay.async / core) |
| deadline・タイマー | 標準 | `async/deadline-in`・`deadline-at`・`now-ms`、`sleep-ms`。deadline は connect・read・DNS に効く。定期実行のスケジューラ(cron のようなもの)は無いので、`go` とループと `sleep-ms` で作る。 |
| OS スレッド並列 | 標準 | `pmap`・`pfold`・`future`・`pcalls`・`atom`(`swap!`・`reset!`)。スレッド安全は par-safety 検査がある。 |
| io_uring | 標準(サーバ用) | `clay.uring`・HTTP サーバの `-DCLAY_SERVER=uring` バックエンド。 |
| プロセス | 標準 | `clay.sys`: `run`・`spawn`・`wait-pid`・`wait-any`・`kill-tree` |

## 3. データ形式

| 形式 | 状態 | 内容 |
|---|---|---|
| JSON | 標準 | `clay.json`: `parse`(→ `Values(Dyn Str)`)・`stringify`・`pretty`・`escape`。値は Dyn(配列は Vec(Dyn)、オブジェクトは Map(Str Dyn))。ストリーミングの読み書きは無い。 |
| XML | **自作** | パーサも生成器も無い。名前空間・ストリーミングも自作。 |
| YAML | **自作** | 無い。 |
| CSV | 標準(列単位) | `clay.csv`: `read-col`・`read-cols`・`write-cols`(数値列向け)。一般的な CSV(引用符・改行入り)の行単位パーサは自作。 |
| EDN | 標準 | `clay.edn/read` |
| 正規表現 | 標準(簡素) | core の `re-find`・`re-matches?`・`re-test?`・`re-split`・`re-replace`・`re-pattern`。自前のバックトラック実装で、`^ $ . [..] \d \w \s * + ? ( )` がある。**`|`(選択)・後方参照・名前付きグループ・Unicode クラスは無い**。DataWeave の regex 関数を全部満たすには拡張か自作(または PCRE2 を FFI)。 |
| 日付・時刻 | **ほぼ自作** | `now-ms`・`now-us`・`epoch-ms->iso8601` のみ。タイムゾーン・書式・解析・期間の計算は自作。tzdata は FFI(libc の `localtime_r` など)でも可。 |
| Base64 | 標準 | `clay.base64/encode`・`decode` |
| ハッシュ・HMAC | 標準(一部) | `clay.crypto`: `sha256`・`hmac`(SHA-256)・`nonce`、SCRAM 用の関数。(2026-10-11、clay 0.82.0)MD5・SHA-1・SHA-2 の全部(`md5`・`sha1`・`sha224`・`sha384`・`sha512`・`sha512-224`・`sha512-256`)が runtime の C(CPU に SHA 命令などがあればそれ)で入り、途中の状態から続ける `X-blocks`・`X-finish`・`X-iv` と `bytes/pack-words` もある。(2026-10-11、clay 0.83.0)SHA-3・SHAKE(`sha3-224`〜`sha3-512`、`shake128`・`shake256`、`keccak-iv`・`keccak-blocks`・`keccak-finish`)、`bytes/xor`・`bytes/unpack`(組み込み)・`bytes/unpack-words` も入った。(2026-10-11、clay 0.84.0)公開鍵暗号: `x25519`・`x25519-base`、`ed25519-public`・`ed25519-sign`・`ed25519-verify`、`rsa-verify`(n e は大きい順のバイト列、hash は "sha256" など)、`RsaPrivate` と `rsa-sign`、`modexp`、`p256-verify`。64 ビットの論理右シフトは `unsigned-bit-shift-right`(`bit-shift-right` は算術シフト)。 |
| JWT | 自作 | HMAC-SHA256 と Base64 があるので HS256 は書ける。RS256 などは OpenSSL を FFI で。(clay 0.85.0)mulay は clay.pkix で鍵を読み clay.crypto の `rsa-sign` で署名する(OpenSSL は使わない)。 |
| 暗号(AES・RSA) | 標準(AES)/ FFI(RSA) | (2026-10-11、clay 0.82.0)`clay.crypto` に AES(`aes-key`、ECB・CBC(詰め物なし)・CTR・GCM。秘密のバイトで表を引かない portable 版と AES-NI)、ChaCha20・Poly1305・ChaCha20-Poly1305 が入った。RSA・ECDH などは TLS 用にリンクされる OpenSSL を `c/EVP_*` で呼ぶ(zeta の Web Push が実例: `~/projects/zeta/platform/kairos/webpush.clay`)。(clay 0.84.0)RSA・X25519 などは clay.crypto に入り、(clay 0.86.5)clay.tls も OpenSSL を使わなくなった。mulay は OpenSSL をリンクしない。 |

## 4. ネットワーク

| 項目 | 状態 | 内容 |
|---|---|---|
| HTTP/1.1 サーバ | 標準 | `clay.http/run-server`(opts に `"port"`、`"cert"`/`"key"` で TLS)、`ring-serve`。バックエンドは threaded(既定)と uring を `CLAY_CFLAGS=-DCLAY_SERVER=..` で選べる。chunked の本体、keep-alive、読み取りの idle 5 秒。性能は fasthttp と同等以上(ADR 029、TLS h1 で 417k req/s)。 |
| HTTP/2 | 標準 | `clay.h2`(サーバとクライアント、HPACK は `clay.hpack`)。TLS の ALPN で h2 を選ぶ。 |
| HTTP クライアント | 標準 | `clay.http/request`(opts の Map とイベントのコールバック)、`get`・`post`。TLS、リダイレクト、`"timeout-ms"`・`"connect-timeout-ms"`、SSE を受けられる。 |
| TLS | 標準 | クライアント(`clay.tls`、SNI、既定の CA)。サーバは run-server の cert/key。**mTLS(クライアント証明書)は未実装**(`runtime/parts/clay_srv.h` の OpenSSL 設定に足す必要)。(2026-09-29)サーバでクライアント証明書を求めて検査できるようになり(clay.tls の client-auth と client-ca。mulay の conn/http が使う)、(clay 0.86.5)clay.tls は純 Clay になった。 |
| SSE | 標準 | クライアントで受信(`gates/sse-check.sh`)。サーバから送るのは chunked 応答で書く。 |
| WebSocket | **自作** | 無い(HTTP の upgrade とフレーミングを書く)。 |
| gRPC | **自作** | h2 はあるが、protobuf と gRPC のフレーミングは無い。 |
| FTP/SFTP | **自作** | 無い。SFTP は mulay が純 Clay で書いた (lib/ssh、lib/sftp。公開鍵暗号は clay.crypto 0.84.0)。FTP は `clay.net` の上に自作できる。 |
| 生の TCP | 標準 | `clay.net`: `connect`・`listen`・`accept`・`read`・`write`・`close`。 |

## 5. DB

| DB | 状態 | 内容 |
|---|---|---|
| PostgreSQL | 標準(最小) | `clay.postgres`: 純 Clay の v3 プロトコル、SCRAM-SHA-256、TLS。`connect`・`exec`・`query-col1`・`query-csv`・`close`。**パラメータ付きの問い合わせ・全列の型付き取得・トランザクションの API・プールは無い**ので拡張が要る。 |
| SQLite | 自作 | mulay が純 Clay で書いた (lib/sqlparse・sqlexec・sqlbtree、db/sqlite。2026-10-11、libsqlite3 の FFI から差し替え)。ファイルは clay.io の File を使う予定。 |
| MySQL | 自作 / FFI | プロトコルを純 Clay で書くか、libmariadb を FFI で。mulay は純 Clay で書いた(db/mysql、db/mywire)。 |
| Oracle | 自作 / FFI | python-oracledb(Oracle 公式、UPL/Apache 2.0)の thin mode を参照して純 Clay で書くか、ODPI-C を FFI で(Instant Client が必要)。mulay は純 Clay の thin で書いた(db/oracle、db/orawire、db/oraproto)。 |
| H2 | 不可 | Java 専用。SQLite で代用するか、H2 の PostgreSQL 互換モードを使う。 |
| JDBC 相当の共通層 | 自作 | 無い。「関数を入れた record」で DB ごとの実装を差し替える形が素直(clay に interface/protocol は無い。`defmulti` は簡易的なもの)。 |

## 6. パーサ構築

- PEG・パーサコンビネータ・Instaparse 相当の**ライブラリは無い(自作)**。
- 手書きの再帰下降が実績のある書き方です。clay のコンパイラ自身がそうで(`src/clayc/syn.clay` の読み取り器、`src/clayc/resolve.clay`)、JSON(`src/clay/json.clay`)と EDN も同じです。
- 部品として使えるのは `str-nth`(バイト値)・`subs`・`str/index-of-after`・`defvariant`(AST)と `match`。
- DataWeave の文法は、手書きの再帰下降と Pratt(演算子の優先順位)で書くのがおすすめです。

## 7. テスト・ベンチ・プロファイル

| 項目 | 状態 | 内容 |
|---|---|---|
| ユニットテスト | 標準 | `(deftest name (is expr) ..)` をパッケージ内に書き、`clay test <dir>` で実行する。1 テスト 1 プロセスで、ASan/LSan 付き(リークを検出する)。 |
| 統合テスト | 慣行 | clay 本体は `gates/*.sh`(シェルスクリプト、151 本)で検証している。 |
| ベンチ | 自作 | 専用の枠組みは無い。`now-us` で測るか、外部ツール(hyperfine、wrk、`~/.cache/httpbench`)を使う。 |
| プロファイラ | 外部 | ネイティブバイナリなので perf・callgrind・ASan をそのまま使える(`clay build --asan`)。生成 C の各関数の前に `/* clay: ns/name */` がある。 |

## 8. 端末

- `clay.term`(630 行):raw モード、ESC シーケンス、キーとマウスのイベント(`read-event`・`read-key`)、UTF-8 の幅、色(256 色と RGB)、ボックスや罫線、spinner や sparkline、画面サイズ、リサイズの検知。Windows コンソールにも対応。green タスクの中では park する。
- **行編集(readline 相当)は無い**:履歴・補完・カーソル移動を持つ入力行は自作。プロジェクト A の TUI と `src/clay/console.clay`(nREPL/REPL の入力)が参考になります。

## 9. 既知の制約・落とし穴

1. **例外が無い**:mulet の try/catch、エラーハンドラ、`on-error-continue` は、`Values(T Str)` とエラー値の受け渡しで作り直す。
2. **永続コレクションではない**:Clojure の「元のまま共有」を前提にした書き方(大きな Map を複数の所に持って、それぞれ少しずつ変える)は複製の費用が出る。更新するのは 1 か所にする。
3. **動的な値**:DataWeave の値(型が実行時に決まる)は `Dyn` で表す。Dyn から読むには `dyn->int` などで変換し、種類が違えば止まる(ADR 023/036、緩い読み出しは無い)。`get-in` と既定値を使う。
4. **型注釈の文法**:`(fn Int [x: Int] ..)` のように戻り値の型が必須。
5. **互換性より設計を優先する方針**:clay は API を積極的に改名・廃止する(`docs/renames.md`、エラー文が移行先を案内する)。版を固定するか、追従する前提で。
6. **XML・YAML・日時・正規表現・BigDecimal** は mulet の核なのに無い。ここが一番大きな自作の塊。
7. **ライブラリの生態系は小さい**:npm/Maven のようなものは無い。C ライブラリの FFI(`c/名前`、宣言は clang に問い合わせる。`(c-include ..)`・`(c-flags ..)`)が逃げ道。FFI の呼び出しは `unsafe` の中に置く(ADR 018)。C が返すポインタと `char*` は `Option(Addr)`・`Option(Str)` で、NULL は None。C に NULL を渡すのは `(->None)`(clay 0.109.0、clay の ADR 143。前は `(nil->addr)`)。
8. **ビルド時間**:コンパイラ自身(約 6 万行の C)で cold 35 秒ほど。単位ビルドのキャッシュがあるので、編集後は速い。
9. **wasm は純粋な計算のみ**:OS の機能(ネット・ファイル)は無い。

## 10. 参考プロジェクトと文書

- 別の社内プロジェクト A(約 3.8 万行、`clay.pkg` あり):HTTP・TLS・JSON を多用する CLI と TUI、エージェント。移行の実績がある。`compat.clay` に Dyn の読み出しの補助。
- 別の社内プロジェクト B(約 7,900 行):取引基盤。HTTP サーバ、PostgreSQL、Web Push(OpenSSL の FFI で AES-GCM・ECDH)、green スレッド、io_uring。
- 別の社内プロジェクト C(約 1,400 行)
- clay 本体の `examples/`(`quote-aggregator`・`term-demo`・`os`)
- 文書:
  - `README.md`(言語の概要)
  - `docs/current-state.md`(現状の一次資料)
  - `docs/development/decisions/`(ADR 004〜037)
  - `docs/development/plans/`
  - `docs/development/experiments/`
  - `docs/renames.md`(廃止名と移行先)
  - `docs/book/`(OS を作る手順書)
  - `docs/core-audit.md`
- API の一覧:`src/clay/builtins.clay`(REPL 補完用の全名)、`src/clayc/builtins.decl`(組み込みの型署名)、`src/clayc/forms.decl`(特殊形式)

---

### mulet 移植での自作の大きさ(目安)

| 部品 | 規模感 | 備考 |
|---|---|---|
| XML パーサと生成器(名前空間つき) | 中 | Mule XML の読み込みと DataWeave の XML 出力に必須 |
| DataWeave パーサ | 大 | 手書きの再帰下降と Pratt |
| DataWeave 標準ライブラリ 約 310 関数 | 大 | 日時・正規表現・BigDecimal に依存 |
| 日時とタイムゾーン | 中 | tzdata の扱いを決める(FFI か同梱か) |
| BigDecimal | 中 | Int のリム列で任意精度 |
| 正規表現の拡張 | 小〜中 | `|` と名前付きグループ、または PCRE2 を FFI |
| YAML | 中 | 設定ファイル用なら部分集合でよい |
| DB 共通層と各ドライバ | 中〜大 | PostgreSQL を拡張、SQLite は FFI、Oracle は最大(SQLite は後で純 Clay に差し替えた。docs/sqlite.md) |
| WebSocket・gRPC・SFTP | 各 中 | 必要なものだけ |
