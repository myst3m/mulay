# 001 — Clay の制約を避ける書き方 (mulay.lib)

状態: **採用** (2026-09-28 の最初の取り込みから 2026-10-11 までの各コミット。項ごとに分かるものは書き添える)

## 決定

mulay.lib の次の書き方は Clay の不具合・性能・制約を避けるためのもの。見かけを「単純」にしない。

### 値の共有を切ってから書き換える (写しを避ける)

- **assoc の前に読む**。`mulay.lib.inflate/deflate-fixed` はハッシュ連鎖の表 `hd` の古い先頭を assoc の前に読む。
  assoc の後で読むと `hd` が共有されたままになり、assoc が全体の写しになる (2026-09-28)。
  `mulay.lib.crypto/md2` も、状態 `xx` の `(nth xx j)` を assoc の前に let で読む (2026-10-23)。
  clay は、assoc が範囲外で失敗しうるので、この読みを自動では前に出さない (clay ADR 120)。
- **Pager は塊に分けて持つ**。`mulay.lib.sqlbtree/Pager` はバイト列のページと読み解いたページを `CH` (64) ページずつの
  塊の Vec で持つ。Pager は値なので、前の版を持つ者 (文の取り消し、トランザクション) がいると書き換えで写しが要るが、
  写すのは塊 1 つと外側の並びだけで済む (0672fec、2026-10-11)。
- **取り出してから替える**。`chunk-set-str`・`chunk-set-pg`・`chunk-add-str`・`chunk-add-pg` は塊を取り出し、外側の
  その位置を空にしてから替える。他に持つ者がいなければその場で替わる。`take-pg` は読み解いたページを Pager から取り出し、
  その場所を空にする (セルの並びを他と共有せずに変えられる。書き戻すのは呼び出し側)。`table-insert` もセルの並びを
  ページから抜いて (`:cells` を空にして) 変える。`ins-at` は末尾に足してから後ろへずらす (並びを他に持つ者がいなければその場で)。
- **DynMsg の欄も取り出してから足す**。`mulay.lib.protobuf/put-vals` は `:vals` を取り出して空にし、その中の 1 欄も取り出して空にしてから
  足す。`add-unknown` は `:unknown` を、`decode-into` は分けて来たメッセージのフィールドの断片 (`pend` の 1 欄) を同じように取り出す。
  record に残したまま読んで足すと、足すたびに並び全体を写し、繰り返しのフィールドの数の 2 乗になった (2 万個で 448 ms が 3 ms、2026-11-08)。
  知らないフィールドの並べ替え (`unknown-sorted`) は番号・wire の型・来た順で比べるマージソート (前は番号ごと・型ごとに全体をなめる 2 乗で、
  2 万個を書くのに 2.0 秒、30 万個で 41 ms)。
- **Pager を DB に残したまま書かない**。`mulay.lib.sqlexec/exec-insert` は Pager を DB から取り出して書く (DB に残すと共有になり、
  書くたびに写しが要る)。書いた後は元の Pager を使わない (使うと write-row に渡した Pager が共有になる)。
- **要らない前の版を持たない**。`mulay.lib.sqlexec/exec-stmt` は、`simple-insert?` (1 行の VALUES だけの INSERT、副問い合わせなし)
  なら文を元に戻すための前の DB を持たない。行を書く前にしか失敗しないので要らず、持つと Pager の書き換えのたびに塊の写しが要る
  (a0cfa23、2026-10-11)。
- **戻すかもしれない更新は、確かめてから行う**。`mulay.lib.sqlexec/exec-update` は、制約を確かめる `row-conflict` (Pager を
  借りるだけ) を先に呼び、通った時だけ `put-row` で行を消して書く。確かめる時は、書き換える行の rowid (Option) を除いて主キーと
  UNIQUE を見る。前は行を消してから確かめ、OR IGNORE で飛ばす時に消す前の Pager に戻すため、行ごとに Pager を写していた
  (2026-10-31、clay build --copies が名指した所)。
- **残すかどうかを引数で渡し、返った値をいつも使う**。`mulay.lib.xml/parse-entity-decl` は、宣言を覚えるかどうか (supportDtd) を
  `keep` で受け、覚えない時は渡された表をそのまま返す。呼ぶ側が「覚えない時は渡す前の表を使う」と分けると、渡す前の表が生きて
  いるので宣言ごとに表をまるごと写し、宣言の数の 2 乗になる (2 万個で 2,232 ms が 9 ms になった。2026-10-31)。
- **clay build --copies が名指すが、残す所** (2026-10-31。前の値が意味の上で要り、写すものの大きさに上限がある):
  - `mulay.lib.regex/run` の先読み・後読み (2 か所)。中の VM に捕獲の Vec を渡した後、外は前の捕獲を使う (否定の先読みや失敗の時は
    そのまま、成功の時は `merge-caps` が戻すための記録を積むのに前の値を見る)。写すのは 2 × (グループ数 + 1) 個の Int で、
    パターンで決まり、入力では決まらない。
  - `mulay.lib.time.fmt/parse-range` の幅を指定した項目。`parse-item` が成功した後で、幅の終わり (`endp`) と合わなければその項目を
    無かったことにし、前の文脈 (`PCtx`、欄が数個の record) に戻す。
  - `mulay.lib.sqlbtree/index-delete` の内側の節で鍵が当たった時。前の葉までの道筋 (`lpath`) と、その節までの道筋 (`path`) の
    両方を使う。写すのは木の深さほどの Step の Vec で、削除 1 回に 1 度。
- **型紙を共有する**。`mulay.lib.sqlexec/with-vals`・`table-row` は行の scope の値だけを替え、列の名前などは型紙と共有する。
- **Atom から取り出して持ち主を 1 人にする**。`mulay.lib.sftp/take-st` は Sess の状態の Atom を空にして値を取り出し、
  取り出した値だけが持つようにしてから更新し、`put-st` で戻す (91be748、2026-10-11)。`mulay.lib.ssh/no-conn` は record の欄を
  一時的に空けるための値 (`mulay.lib.sftp/dead-st` が使う)。
- **pop で写さない**。`mulay.lib.xml/build-dom` は DOM を明示のスタックで組む (再帰しない)。開いている要素は深さで引く並列の Vec に、
  終わった子は `pend` に積み、親が終わるときに切り出す。どちらも論理的な長さを持つので、pop で写さない
  (書いた当時の Clay の `pop`/`butlast` は全体を写した。clay 0.107.0 では、ほかから参照されていない Vec の `pop` はその場で縮み、
  `butlast` は無い)。要素の行番号の木 (`lp`/`ls`) も同じ (2026-09-28)。
- **next-event に渡した reader は、その後で読まない**。`mulay.lib.xml/build-dom` は、行番号を数える文字列 (`src`) を
  `next-event` の前に束ねておく。`src` は実体参照の展開で入れ替わるので、返った reader (`r2`) から読んではいけない。
  渡した後で `r` を読むと、イベントごとに reader を写す。20 万要素 (6.8 MB) の XML を読む時間が 0.51 秒から 0.38 秒になった (2026-10-23)。
- **parse-attr-value に reader を書き換えて渡さない**。`mulay.lib.xml/read-start` は実体の展開の数え (`nexp`・`nbytes`) を
  引数で渡し、reader は借りて読むだけにする。前は属性ごとに `(assoc r :nexp ..)` で渡していたが、r はその後も使うので
  属性ごとに reader を写していた。20 万要素 (属性 2 つずつ) の XML で命令数が 2.76G から 2.53G になった (2026-10-24)。
- **data を写さない**。`mulay.lib.hash/finish-on` は buf が空の状態に data を足した要約を、data を写さずに求める
  (`(finish (feed s data))` と同じ値)。
- **バイトは Vec(Int) に積んでから Str へ移す**。`mulay.lib.inflate/inflate-codes` はブロックの出力を `pend` (Vec(Int)。1 バイト
  足すのに確保が要らない) に積み、64 KiB ごとに Str の `out` へ移す。後方参照はどちらからも読む (2026-09-28)。

### Str はアキュムレータに積む

- `mulay.lib.sqlfile/encode-record` はヘッダの格納型を積み、本体を同じ文字列へ続けて積む。`add-varint`・`add-body`・`add-be` は
  out の後ろに足す (0672fec の「encode-record は 1 つの文字列に積む」)。

### Int は 64 ビットで、溢れると wrap する

- `mulay.lib.bigint/add-ov?`・`sub-ov?`・`mul-ov?` で溢れを検知する (CERT INT32-C の判定。除算は溢れない形だけを使う)。
- Int と BigInt の変換 (INT-MIN を含む) は clay.bigint の `int->bigint`・`bigint->int` に任せる (ADR 002)。
- `mulay.lib.time.num/add-exact`・`mul-exact` (Java の Math.addExact 相当) で、time の溢れうる加算・乗算を検査する。
- `mulay.lib.time.local/ldt-plus-seconds` は秒とナノ秒を先に日へ寄せてから足す。`ldt-until` の時間系は
  「日数 × 1 日の単位数 + 日内の差」と Java と同じ組み立てにして溢れを避ける。
- `mulay.lib.time.zoned/instant-epoch-milli` は負の秒を Java と同じく `(s+1)*1000 + (ns/1e6 - 1000)` で計算して溢れを避ける。
- `mulay.lib.time.civil/fdiv`・`fmod` は床除算・床剰余。Clay の `/` と `mod` は 0 方向へ切る。

### メモリと深さの上限

- Clay は確保に失敗するとプロセスごと終わる。`mulay.lib.dec/MAX-DIGITS` を超える桁を作る演算は作る前に `TOO-BIG` で失敗させる
  (利用者から見た違いは docs/compat/deviations.md の「指数の大きい数を展開する演算」)。
- `mulay.lib.regex/MAX-STACK`: 後戻りの記録は 100 万件 (1 件 4 Int、32MB) まで。VM のスタックは入力に比例して伸び、1MB の入力の
  `(a|b)*x` で 300MB、10MB の入力なら GB 単位になった (1a33ba9、2026-10-04)。`run` は超えれば -3 を返す。
- `mulay.lib.regex/run`: 先読み・後読みと atomic group は sub-VM で走らせる。その深さはパターンの入れ子で決まり、入力では決まらない。
- `mulay.lib.yaml/enter`: 構造の解析は再帰下降で、深さは YOpts の max-depth で抑える。
- `mulay.lib.jsonschema/resolve`: `$ref` は循環に備えて 64 段までたどる。

### 再帰する variant

- `mulay.lib.sqlparse/Node` は `Ex` (defvariant) を包む record。コメントの原文は「Node は Ex を包む (再帰する variant のため)」
  (847aae8、2026-10-11)。Ex の腕は子を Node で持つ。clay 0.107.0 では、variant の腕が自分の型を直接持てる
  (`(defvariant Ex (Lit n: Int) (Add kids: Vec(Ex)))` が通る) ので、再帰のために包む必要はもう無い。Node は今は木の深さ (`h`) も持つ。

### コード生成の不具合

- `mulay.lib.dec/inf?`: 大きな浮動小数点リテラルは clay のコード生成が壊すので、無限大は `x*2 = x` (0 以外) で判定する。

### 閉包

- `mulay.lib.sqlexec/index-comparer`: 照合順序と降順の並びは、借用した Index のフィールドをそのまま `fn` に捕まえる。
  clay は捕まえるときに参照カウントを増やすので、Index が先に解放されても閉包は使える (clay に確認、2026-10-16、0.86.5)。
  以前は写してから捕まえていたが、写す必要は無かった。閉包が受ける Str の引数 (`a: Str`) は所有なのでリークしない。

### OS スレッドと参照カウント

- `mulay.lib.time.tz/rules-cache`: 読んだ規則は大域の atom 1 つ (ID → ZoneRules) にキャッシュする。green スレッド間では安全。
  OS スレッドを使うビルド (CLAY_PARALLEL か run-server) では clay が CLAY_THREAD_SAFE (原子的な参照カウント) にする。

### runtime と stdlib の範囲

- `mulay.lib.random/random-bytes`: clay の `prim/random-bytes` は 1 回に 1 MB までなので、それを超える長さは分けて取る (fdd352f、2026-10-11)。
- `mulay.lib.sqlfunc/ARITY`: Clay に無い libm の関数 (log2、mod、atan2、acos、asin、atan、双曲線関数) は名前を知っていて、
  呼べば "unsupported" で失敗する (11a1ee0、2026-10-11)。
- `mulay.lib.numparse/int-or`・`flt`: clay 0.51.2 で `parse-long`・`parse-double` が `(values x err)` を返すようになった (不正な
  入力を黙って変な値にしない)。既定値を決めてよい場所のための薄い補助。

## 理由

- どれも消すと、次に読む人が「単純化」して不具合か性能の劣化が戻る。
- 写しの回避の効き目: 0672fec で SQLite の INSERT (索引 1 つ) は 1 行あたり約 105 万命令から約 3 万命令になった (callgrind)。
- 確保の失敗は回復できない (プロセスごと終わる)。上限は「作る前に断る」ために置く。

## 場所

- `mulay.lib.inflate/deflate-fixed`、`mulay.lib.inflate/inflate-codes`
- `mulay.lib.sqlbtree/Pager`、`CH`、`chunk-set-str`、`chunk-set-pg`、`chunk-add-str`、`chunk-add-pg`、`take-pg`、`ins-at`、`table-insert`
- `mulay.lib.sqlexec/exec-stmt`、`simple-insert?`、`exec-insert`、`with-vals`、`table-row`、`index-comparer`
- `mulay.lib.sftp/take-st`、`put-st`、`dead-st`、`mulay.lib.ssh/no-conn`
- `mulay.lib.xml/build-dom`
- `mulay.lib.hash/finish-on`
- `mulay.lib.sqlfile/encode-record`、`add-varint`、`add-body`、`add-be`
- `mulay.lib.bigint/add-ov?`、`sub-ov?`、`mul-ov?`
- `mulay.lib.time.num/add-exact`、`mul-exact`、`mulay.lib.time.local/ldt-plus-seconds`、`ldt-until`、
  `mulay.lib.time.zoned/instant-epoch-milli`、`mulay.lib.time.civil/fdiv`、`fmod`
- `mulay.lib.dec/MAX-DIGITS`、`TOO-BIG`、`inf?`
- `mulay.lib.regex/MAX-STACK`、`run`
- `mulay.lib.yaml/enter`、`mulay.lib.jsonschema/resolve`
- `mulay.lib.time.tz/rules-cache`
- `mulay.lib.sqlparse/Node`、`Ex`
- `mulay.lib.random/random-bytes`、`mulay.lib.sqlfunc/ARITY`、`mulay.lib.numparse/int-or`、`flt`
