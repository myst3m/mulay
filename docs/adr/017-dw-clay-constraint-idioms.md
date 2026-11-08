# 017 — Clay の制約を避ける書き方 (src/mulay/dw 直下)

状態: **採用** (2026-09-28 の初版から。BUILTINS の delay は 2026-10-11、8c3ea2f。HOOKS と型の番号は ecddec4、
共有の定数と小さい小数の Int 経路は 7e761b0、0..1023 の整数は 766feb3)

ここに挙げた書き方は、見た目を単純にすると不具合か性能の後退が戻る。直す前にこの ADR を読む。

## 決定

### スタックの深さ
- **パーサの入れ子の上限は `MAX-DEPTH` 400**。1 段あたり C スタックを 0.5KB ほど使う (-O2)。要求を処理する
  スレッドのスタックの下限は 1MB (clay の thread cache は RLIMIT_STACK を 1MB..64MB に収める) なので、その下限でも
  足りる値にする。実 DW (JVM) は配列の入れ子 200 段で StackOverflowError になるので、DW が読めるスクリプトは
  すべて読める。
- **連鎖 (演算子の連なり `a + a + ..`、後置の `.b`・`[0]`・`()`・`as T` など) も深さに数える** (2026-11-03)。パーサは
  ループで読むので C スタックを使わないが、木は左へ鎖の長さだけ深くなり、名前解決 (`dw/resolve` の `rx`)・評価・表示は
  それを再帰でたどる。ループの頭で、今の深さ + 左の鎖の長さが上限を超えたら、入れ子と同じ診断で止める。実 DW も
  `1 + 1 + ..` と `.a.a..` が 400 段では読め、1000 段で StackOverflowError (メッセージ null) になる。前は数えておらず、
  2 万段の式でプロセスごと落ちた (wasm のファジングで見つけた)。
- **パーサの再帰はすべて `p-expr` を通す**。`p-expr` が深さを数えて `p-level` を呼ぶ。深さを数えない再帰の経路を
  足さない (C スタックを使い切る)。上限で止まったら St の `dead` を立て、バックトラック (`restore`) でも戻さない
  (戻すと上限の診断を消したまま続きを読んでしまう)。
- **評価器の深さの上限は定数 `MAX-STACK`**。wasm では 1000、ネイティブは 3000 (2026-11-03)。wasm のスタックは V8 の既定で約
  1 MB で、Node 22 で測ると数えた段がおよそ 1500 (素直な再帰 1000〜1500 段、map を挟む再帰 300〜500 段) で
  "Maximum call stack size exceeded" になった。1000 ならどの書き方も上限のエラーで返る (test/fixtures/livenote/deep-recursion、
  tools/wasm/host_test.mjs)。ネイティブは閉包も段に数えるので、重い書き方ほど早く上限に当たり、要求のスレッドのスタックを
  使い切らない (2026-11-03 にサーバーへ深い JSON と再帰を送って確かめた)。
- **評価器は末尾でない呼び出しの深さに上限 3000 を設ける**。C スタックを使い切る前に
  "Stack Overflow. Max stack is 3000" で失敗にする。深さはどの式でも閉包の入口で調べる (失敗の位置は深さを超えて
  最初に評価した式)。末尾位置の呼び出しは `T` の「続き」として `call-def` のループで回し、深さを増やさない
  (実 DW は 10 万段の末尾再帰を回せる)。ただし関数の本体そのものが呼び出し (`fun f(n) = f(n + 1)`) なら末尾として回さず
  (`mulay.dw.eval/tx-body`)、深さが上限に届いて失敗する。実 DW もこの形は回さず 256 段で失敗する。以前は止まらなかった (2026-10-17)。
- 事前コンパイルの生成コード (`gencode`) は閉包と同じ所で同じだけ深さを増やす (`deep`)。スタックあふれの失敗の
  位置が実行の仕組みで変わらないようにするため。

### 参照カウントと共有
- **コンパイル済みの閉包の木は起動状態の def に入れて不死にする**。サーバでは全スレッドがこの木を読む。不死なら
  スレッドをまたいで読んでも参照カウントを書かず、原子的な増減がコア間で競合しない。
- **共有の定数** (def の値は不死。値は不変なので共有してよい):
  - `dwe/OK` (成功の DwErr、mulay.dw.err) と `dwe/NO-SPAN` (位置なし)。評価のたびに確保しない。
  - `ev/NO-FRAME`: 末尾位置の式が「続きなし」を返すときのフレーム。
  - `v/SMALL-INTS`: 0..1023 の整数 (`v/int-v` が使う)。
  - null と true/false (`v/null-v`、`v/bool-v`) はリテラルから作る。clay 0.51.9 から、定数だけのレコードは静的な
    データになり確保しない。名前空間も属性も無いキー (`v/str-v`、`v/field`) のリテラルの `[]` も確保しない (clay 0.51.4)。
  - `CKName` の `plain`: 名前空間も属性も無いオブジェクトのキーは、コンパイル時に 1 回作った Key を共有する。
    生成コードでは同じキーをモジュールの定数 `KEY<i>` にする (`gencode/key-const`)。
  - `rt/tail-mark`: 末尾呼び出しの続きに添える成功の値は、呼び出しの場所ごとに 1 つ作って使い回す。
- **整数は 1 レコードの `VInt`**。数の値は必ず `v/num-v` で作り、`num/NInt` を `VNum` に入れない。整数の算術の
  確保が 1 回で済む。

### 閉包と確保を作らない呼び出し
- **組み込み関数が関数値を呼ぶ入口 (`rt/Env`) は閉包を持たない**。関数は定数の `ev/HOOKS`、評価器の文脈は Dyn で
  包んで渡し、Env は文脈と深さだけを持つ (`ev/env-of`)。以前は呼び出しごとに閉包を 3 つ作っていた。
- **オーバーロードの照合は型の番号 (Int) で行う** (`rt/type-tag`、`rt/val-tag`)。型の名前の文字列を比べない。
  `rt/invoke` は引数が 3 つまでなら型の番号を変数に持ち、4 つ以上のときと変換を試すときだけ Vec を作る。
- **予約語の判定 (`lex/kw-code`) は先頭の文字で分けて `span-is?` で比べる**。名前 1 つごとに呼ばれるので、
  予約語の def の Vec を引かない (def の Vec は参照のたびに作られる)。`span-is?` は部分文字列を作らずに比べる。
- **Range の要素は添字から計算する** (生成コードの map などの展開、`gencode/emit-hof`)。要素の Vec を作らない。
- **小さい小数の加減乗算は Int で計算する** (`num/small`、`small-addsub`、`small-mul`)。unscaled が Int に収まる
  間は bigint を経由しない。桁あふれしそうなら ok = false を返し、呼び出し側が Dec で計算し直す。

### 起動
- **組み込み関数の表 `engine/BUILTINS` は delay にし、初めてコンパイルするときに作る**。clay 0.80.0 から def は
  main の前に計算されるので、そのままだと `mulay version` のように DataWeave を使わないコマンドの起動でも表を作る
  (起動の命令 1,660 万 → 800 万)。

### 可変の状態と循環
- resolve は状態 St を引数で回し、各関数は `Values(結果 St)` を返す (Clay に可変の状態は無い)。
- do の中の fun はグループとして捕獲リストを共有し、同じグループの関数は `RSibling` で自分の捕獲から作る。
  クロージャが自分自身を参照する循環を作らない。Clay は参照カウントで GC が無いので、循環はリークする。

## 理由
- Clay の値は参照カウントで、共有中の値への書き込みや Vec・閉包の確保がそのまま実行時間になる。実 Mule より速く
  することが条件 (計測は各コミットのメッセージ: nested -8%、compute -4%、bench compute 123 → 325 req/s など)。
- C スタックの大きさはスレッドで決まり、溢れはプロセスごと落ちる。深さの上限で DwErr にする。

## 場所
- `mulay.dw.parse/MAX-DEPTH`、`mulay.dw.parse/p-expr`、`mulay.dw.parse/restore`、`mulay.dw.parse/too-deep`
- `mulay.dw.eval/so`、`mulay.dw.eval/cx`、`mulay.dw.eval/tx`、`mulay.dw.eval/call-def`、`mulay.dw.eval/NO-FRAME`、
  `mulay.dw.eval/HOOKS`、`mulay.dw.eval/env-of`、`mulay.dw.eval/CKey` (`CKName`)
- `mulay.dw.gencode/deep`、`mulay.dw.gencode/key-const`、`mulay.dw.gencode/emit-hof`
- `mulay.dw.err/OK`、`mulay.dw.err/NO-SPAN`、`mulay.dw.err/tail-mark`、`mulay.dw.rt/Hooks`、`mulay.dw.rt/Env`、
  `mulay.dw.rt/invoke`、`mulay.dw.rt/type-tag`
- `mulay.dw.val/SMALL-INTS`、`mulay.dw.val/int-v`、`mulay.dw.val/null-v`、`mulay.dw.val/bool-v`、`mulay.dw.val/num-v`、
  `mulay.dw.val/str-v`、`mulay.dw.val/field`
- `mulay.dw.lex/kw-code`、`mulay.dw.lex/span-is?`
- `mulay.dw.num/small`、`mulay.dw.num/small-addsub`、`mulay.dw.num/small-mul`
- `mulay.dw.engine/BUILTINS`
- `mulay.dw.resolve/St`、`mulay.dw.resolve/rx-fun-group`、`mulay.dw.rir/Rx` (`RSibling`)
