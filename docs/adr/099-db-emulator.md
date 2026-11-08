# 099 — livenote の DB のエミュレータ (db/emu) と、記録との組み合わせ

状態: **採用** (2026-10-24)

## 背景

ブラウザには素の TCP が無く (ADR 098)、手元の PC や中継サーバーも使えない。そこで livenote の例の中の DB の操作を
次のように扱う (ユーザーが選んだ組み合わせ、2026-10-24)。
1. 本物の形は記録で持つ (デプロイ先の実 DB で動かした応答。列名・型・エラーの文まで本物)。記録があれば記録が勝つ。
2. 記録の無い所は、mulay の中のエミュレータで流す。
3. 記録とエミュレータの結果の形 (列名と型) がずれていれば知らせる。

Mule の Database Connector は SQL を抽象化しない (JDBC の上の薄い層で、方言もエラーの文もドライバのまま) ので、
エミュレータは Oracle・PostgreSQL・MySQL の方言を読み、結果を各ドライバと同じ形で返す必要がある。

## 決定

- **エンジンは mulay の自前の SQLite** (lib/sqlexec、C のライブラリを使わない) のメモリの DB。DB の設定ごとに 1 つ。
  `emu/open kind schema seed` が作り、seed (DDL と INSERT。`;` で分ける、`--` のコメントは捨てる) を流す。
  schema は Oracle では接続のユーザー (大文字)、MySQL ではデータベース名 (エラーの文に出る)。
- **方言の読み替え** (`rewrite`、文字列リテラルの中は触らない):
  - Oracle: `NVL(` → `IFNULL(`、`SYSDATE`・`SYSTIMESTAMP` → `CURRENT_TIMESTAMP`、`FROM DUAL` を消す、`''` → `NULL`
    (Oracle では空文字は NULL。バインドした空文字も NULL にする)、`:1` → `?1`。
  - PostgreSQL: `x::type` → `CAST(x AS type)`、`ILIKE` → `LIKE`、`NOW()` → `CURRENT_TIMESTAMP`、`$1` → `?1`。
  - MySQL: `` `名前` `` → `"名前"`、`LIMIT a, b` → `LIMIT b OFFSET a`、`NOW()` → `CURRENT_TIMESTAMP`。
  - CREATE TABLE: 自動採番の列 (`AUTO_INCREMENT`・`SERIAL`/`BIGSERIAL`・`GENERATED .. AS IDENTITY`) は
    `INTEGER PRIMARY KEY AUTOINCREMENT` にし、MySQL の表の後ろの設定 (`ENGINE=..`) と `KEY`/`INDEX` の行は捨てる。
    元の型 (SERIAL は INTEGER、BIGSERIAL は BIGINT) は表ごとに覚えておく。
  - `INSERT .. RETURNING cols` はエンジンに無いので、挿入した行を rowid で読み直して返す。`UPDATE .. RETURNING` は
    WHERE に当たる行の rowid を先に読み、更新の後にその行を読む。`DELETE .. RETURNING` は消す前に読む (2026-10-24)。
    引数は番号付き (`?1`、PostgreSQL の `$1` を読み替えた物) なので、同じ引数のまま WHERE だけの SELECT に使える。
- **結果の形は各ドライバに合わせる** (`shape-rows`。覚えた列の型、式は推した型で):
  - 列名: Oracle は大文字、PostgreSQL は小文字 (関数は関数名、ほかの式は `?column?`)、MySQL は書いたとおり。
    `"引用符"` で書いた別名はそのまま。
  - 型 (mulay の本物のドライバの読み替えと同じ Cell): Oracle は NUMBER 系が Decimal、DATE が Timestamp (秒まで)、
    TIMESTAMP が oracle.sql.TIMESTAMP (11 バイト)、CLOB が Clob。PostgreSQL は int2/int4 が Int、int8 が Long、numeric が
    Decimal、boolean、date が Date、timestamp(tz) が Timestamp。MySQL は TINYINT(1) が Bool、INT が Int、BIGINT が Long、
    DECIMAL、DATETIME が LocalDateTime、TIMESTAMP が Timestamp。count は Oracle が NUMBER、ほかは BIGINT。
- **エラーの文は各 DB の形** (`map-error`): 一意 (ORA-00001 は 23ai の「violated on table .. columns (..)」の形、
  PostgreSQL は Detail に値、MySQL は Duplicate entry)、NOT NULL (ORA-01400 など)、表が無い (ORA-00942、
  PostgreSQL は Position)、列が無い (ORA-00904 など)。SQLState・コード・例外のクラスも各ドライバの値。
  - 制約の名前: Oracle は CONSTRAINT の名前、無ければ `SYS_C` と 7 桁の連番 (本物の番号とは違う)。PostgreSQL は
    `<表>_pkey`・`<表>_<列>_key`、MySQL は `PRIMARY`・列名。値は INSERT の VALUES のリテラルか引数から取る。
  - Oracle の ORA-00001 の 2 行目 (ORA-03301 の値の行) は出さない。
- **エミュレータで流せないものはアプリのエラーにしない**: 知らない関数、読めない SQL (構文のエラー)、ストアドプロシージャと
  PL/SQL のブロック (`BEGIN .. END`・DECLARE・CALL・EXEC・MERGE) は SQLState `EMU01` の DbErr で返し、呼ぶ側は held にする。
  構文のエラーは、利用者の書き間違いか方言の未対応かを見分けられないので、こちらに入れる。

- **conn/db への組み込み**: 接続の種類に `HEmu` (設定名・DB の種類・スキーマ) を足す。`set-emulator! seed` (設定名から
  seed の SQL を返す関数) を差すと、acquire は本物の接続を開かず HEmu を返し、exec はその設定名のエミュレータ
  (`EMUS`、無ければ seed で作る) で流す。`reset-emulator!` で全部捨てる。引数のバインド・結果の読み替え・エラーの型は
  本物と同じ道を通る。select は HOra・HSqlite のときだけストリームにする (前は DB の種類で選んでいた。HEmu は種類が
  oracle でも全部読む)。ストアドプロシージャは EMU01。`EMU01` の DbErr は `db-fail` で MULAY:HALT にする (held)。
- **note**: DB の操作は、記録があれば再生。無くて `livenote/db/<設定名>.sql` があればエミュレータで流し、状態を
  `emulated` (エラーなら `failed`、EMU01 なら `held`) にする。どちらも無ければ今までどおり held。例を流すたびに
  エミュレータを作り直す (seed から始めるので結果が毎回同じ)。
  - wasm (2026-10-24): clay は wasm の clay.net を「届いたらコンパイルで止める」形にした (clay のユーザーの判断)。
    そこで conn/db がソケットを使うドライバを呼ぶ所を `conn/db_net` にまとめ、wasm ではドライバに届かない版 (失敗を返す)
    にした。wasm では HPg・HOra・HMy の接続を作らない (note はエミュレータか再生) ので、その版は呼ばれない。
    SQLite とエミュレータは Clay だけなので wasm でも同じ。conn/db の接続待ちの sleep のため、wasm は
    `env.clay_wasm_sleep_ms` も import する (tools/wasm/host.mjs は何もしない関数を渡す。エミュレータの道は待たない)。

- **記録とエミュレータのずれ** (`compare-shapes`): 記録があり seed もあるとき、記録を返したうえでエミュレータでも流し、
  結果の最初の行の列名 (大文字小文字を区別) と値の JSON の種類 (number・string・boolean・object・array。日時は string、
  null は比べない) を突き合わせる。ずれていれば、そのステップのトレースに `warnings` (1 文、英語) を付ける。状態は
  replayed のまま。DataWeave が本物の形 (記録) に向けて書かれているかと、seed がそれに合っているかの両方の手がかりになる。
  エミュレータ側で失敗したとき (EMU01 を含む) は比べない。

## 場所

- `mulay.db.emu` (`open`・`run`・`rewrite`・`split-statements`・`close`)
- `mulay.conn.db_net` (ドライバの呼び出しの wasm の分け)、`mulay.conn.db` (`HEmu`・`set-emulator!`・`reset-emulator!`・`clear-emulator!`)、`mulay.note.run` (`emulated`・`db-connector`)
- テスト: `test/dbemu/dbemu_test.clay` (oracle・postgres・mysql・unsupported-statements-are-not-app-errors)、`test/note/note_test.clay` (db-emulator-runs-when-there-is-no-recording・recording-and-emulator-shapes-are-compared、fixture は test/fixtures/livenote/dbapp)
