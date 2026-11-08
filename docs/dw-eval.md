# DataWeave 評価器の設計

`Script` (AST) → **resolve** → `Prog` (解決済み IR、`dw/rir.clay`) → **eval** → `Val`

評価器は 1 つだけ (design.md §2)。

## 1. resolve が行うこと

1. **名前解決**。参照ごとに行き先を 1 つに決める:
   - `RSlot(i)`: 自分のフレームの引数または局所変数
   - `RCap(i)`: クロージャが捕獲した値
   - `RGlob(i)`: スクリプトの最上位にある var。最上位の fun は FnDef の番号で直接呼ぶ (`RCallG`) か関数値にする (`RClosure`)
   - `RBuiltinRef(id)` / `RCallB(id, args)`: 組み込み関数 (ネイティブ実装) を値として参照 / 直接呼ぶ
   - `RInput(i)`: payload、vars、attributes などの入力
   - 解決できない名前は、parse エラーと同じ形式の診断にする (実行時まで持ち越さない)。
   - 初期化の前の参照 (実 DW の ForwardReferenceValidationPhase): 名前が同じスコープ (do・using・関数・ラムダ・match と
     update の case・最上位) の宣言を指し、var ならその初期化の式の中、fun なら宣言より前にあればコンパイルエラー
     "Variable: `x` is not yet initialized."。
   - スコープが違っても、同じフレームで宣言より前 (前の var の初期化の中) の参照はまだ値が無い。実 DW は実行時に名前で
     外側の変数 (外の do の var、引数、最上位の var と fun。入力・import・組み込み関数は入らない) を探すので、resolve も
     その束縛に解決し、無ければ実行時に "There is no variable named 'x'" で失敗する `RNoVar` にする。
2. **import の意味**。暗黙に import されるのは dw::Core だけ。他のモジュールの関数は、`import` するか完全修飾名で書いたときだけ見える (mulet の「全関数が 1 つの名前空間」は採らない)。
3. **暗黙のラムダ化**。`$`、`$$`、`$$$` を含む式を引数の位置に置くと、ラムダに包む。範囲はその引数の式全体。
4. **演算子を関数呼び出しに変える**。DW の `+`、`-`、`++`、`>>` などは dw::Core でオーバーロードされた関数なので、`BinOp` を `RCallB(op, [l, r])` に変換する。ただし `and`、`or`、`default` は短絡評価が必要なので、専用のノードとして残す。dw::Core の `+ - * mod == != < > <= >=` は `RNumOp` にする。両辺が Number のときだけ評価器が直接計算し、それ以外は組み込み関数に回す (結果は `RCallB` と同じ)。
5. **関数の持ち上げ** (lambda lifting)。すべての関数を `FnDef {name, params (型、既定値), nslots, ncaps, body, sp, alts}` にして、モジュール単位の表に置く。これには最上位の fun、do の中の fun、ラムダが含まれる。
   - 関数値は IR の `RClosure(def, caps)` で作り、値としては `v/FnV {def, caps: Vec(Val), host: Option(Host), arity}` で表す。捕獲した値はコピーして持つ。
     名前は def から CProg (組み込み関数は表) で引く。評価の外へ出た関数は host を持つホストの関数になる (ADR 108)。
   - do の中の fun はグループとして捕獲リストを共有する。同じ do の fun (自分自身を含む) を参照する場合は、クロージャを作らずに自分の捕獲をそのまま使う (`RSibling(def)`)。こうすると**クロージャが自分自身を参照する循環が生まれない**。Clay は参照カウントで GC が無いので、循環があるとリークする。
6. **slot の割り当て**。フレーム内の局所変数 (do の var、match の束縛、update の束縛) に番号を振る。フレームは `Vec(Val)` で、大きさは固定。

## 2. 値

`mulay.dw.val/Val` (design.md §4)。補足:

- **大きな値の共有**。Clay の値は参照カウントで管理される。評価器は Val を借用 (`&Val`) で渡し、新しい値は組み立てて返す。そのため、同じ Val を複数の場所から参照しても複製は起きない (更新しなければコピーされない)。
- **var の評価**。最上位の var と do の var は宣言の順にその場で評価する (実 DW と同じ。使わない var の失敗も起きる)。
  最上位の var は依存の順に並べ替えない。初期化の前の最上位の var を読むと "There is no variable named 'x'" で失敗する。
- **範囲**。`1 to n` は `VRange` として表し、必要になるまで実体化しない。
- **数**。Int に収まる整数は `VInt`、それ以外 (小数、Int を超える整数、`1E+2` のような負の scale) は `VNum`。
  数の値は必ず `v/num-v` で作るので、`VNum` に `num/NInt` が入っていることは無い。数を扱うパターンは
  `VInt` と `VNum` の両方を見る (`v/num-of` で Num を取り出せる)。VInt は 1 レコードなので整数の算術は確保が 1 回。

## 3. エラー

- 評価器の関数はすべて `Values(Val DwErr)` を返す。成功のときは DwErr の `(:kind e)` が `""` になる。
- `DwErr {kind, msg, sp, frames: Vec(StackF), pend, origin}` (`dw/err.clay`。値 (dw/val) の遅延した並びも DwErr を返すので、値より下に置く)。`kind` は DW のエラーの分類 (`CoercionException`、`KeyNotFound` など。実 DW のメッセージに合わせる)。
- **Mule 側への変換**。`MULE:EXPRESSION` にしてから rt へ渡す。DW の `fail()` と `dw::Runtime::try` / `orElse` もこの経路を使う。
- Clay の実行時 abort (`nth` の範囲外など) は**評価器のバグ**とみなす。入力から起こりうる失敗は、abort ではなく必ず DwErr にする。

## 4. 組み込み関数

- `Builtin {name, module, overloads: Vec(Overload), cand, pipe, fold}` (`dw/rt.clay`)
- `Overload {params: Vec(Str), tags: Vec(Int), run: Fn(Env Vec(v/Val) Values(v/Val DwErr))}`
- **オーバーロードの選択**。実 DW と同じ規則で選ぶ。引数の実行時の型を上から順に照合し、最初に一致したものを使う。Null の扱いも DW の定義に従う (多くの関数は `Null` 版を持ち null を返す)。
- **実装の置き場所**。`src/mulay/dw/lib/<module>.clay` に書き、そのモジュールの `builtins` (`Vec(rt/Builtin)` を返す) に並べる。dw/engine の `all-builtins` がそれらを集めて表にする。関数一覧とシグネチャは `docs/dw-stdlib-catalog.md` を正とし、実 DW の `core-modules` の .dwl から取る。
- **DW で書かれた関数**。実 DW の標準ライブラリには、DW 自身で書かれた関数が多い。ライセンス上可能であれば、その .dwl の定義を移植してネイティブ実装の量を減らす (要確認)。できない場合は、同じ意味をネイティブで実装する。

## 5. 性能の方針

- 実行は閉包コンパイル (2026-09-28 から)。読み込み時に `ev/compile-prog` が IR (r/R) を閉包の木 (`C`: 閉包と
  式の位置) に変え、要求ごとにはそれを呼ぶ。木を歩く評価器は持たない (実行の仕組みは 1 つ)。
  - 式を含む構造 (オブジェクトの項目、セレクタ、match の case、update、引数の既定値) は、R を C にした
    写しの型 (CEntry、CSel、CCase、CUpd、CFn) にする。
  - 関数本体は末尾位置のコンパイル (`T`) をし、末尾呼び出しは「続き」(関数の番号とフレーム) を返して
    call-def のループで回す。
  - 二項演算子 (RNumOp) は被演算子が slot か定数なら、子の閉包を呼ばずに読む専用の閉包にする。キー選択
    (`a.b`) も専用の閉包。
  - 深さの上限はどの式でも入口で調べる (木を歩いていたときと同じ位置で失敗する)。
  - Clay 0.51.8 から、閉包の捕獲値の読み出しと `Fn(&Ctx &Frame ..)` の借用の引数が参照カウントを書かない。
    それより前の Clay では閉包のほうが木を歩くより遅かった。
  - 文字列の `++` も RNumOp に載せる (NUM-OPS の 11)。文字列 ++ 文字列と文字列 ++ 数はその場でつなぎ、
    ほかの組み合わせは組み込み関数を呼ぶ (2026-10-04)。
  - 名前空間も属性も無いオブジェクトのキーは、コンパイル時に作った Key を共有する (CKName の plain)。
  - **集計の合成** (cx-fold、2026-10-04): 集計 (dw::Core の sizeOf / sum / avg / max / min) の引数が map / filter の
    呼び出し (`sum(xs map f)`) なら、途中の配列を作らずに要素を 1 つずつ作って集計する (core_coll の fold-run、
    1 歩は fold-add)。どの組み込み関数かは実行時に `rt/Builtin` の印 (pipe、fold) で確かめ、合わなければ普通の
    呼び出しと同じに評価する。src が Array か Range でない、f が関数でないときも普通の呼び出しに回す。
    失敗は要素の順に最初のものを返す。実 DW も要素を 1 つずつ取りながら集計するので、`sum(xs map f)` で
    f(x0) が数でなければ、f(x2) の失敗より先にそちらが出る (fold_test の記録)。合成しない形 (たとえば
    `var ys = xs map f --- sum(ys)`) は map を先に全部評価するので、この順が実 DW と違うことがある (map の遅延評価は
    まだ)。事前コンパイル (gencode) も、map / filter を展開したループの中で同じ fold-add を呼ぶ。
- **準備した呼び手** (2026-10-26): 同じ関数を何度も呼ぶ組み込み関数 (map、filter、reduce、集計の合成、mapObject、pluck、
  filterObject、並びの map など) は、ループの前に `rt/env-prep` (引数の Vec)、`env-prep2` (引数 2 つ)、`env-prep-ix`
  (要素と添字) で呼び手を 1 回作る。スクリプトの関数で、overload の組が無く、渡さない引数の既定値がすべて定数なら
  (`CFn` の `consts`)、呼び手は Frame を直接作って `ev/run-def` を呼ぶ (Hooks の間接呼び出し、`call-fnv`、`pick-def`、
  `bind-args` を通らない)。それ以外は `call-fnv` に任せる。`env-prep-ix` は、関数が 2 番目の引数を読まないなら
  (`CFn` の `reads`。本体と既定値の式に slot 1 の読みがあるか) 添字を箱詰めしない。`run-def` は末尾呼び出しが
  起きたときだけ数える Vec を作る (`run-hops`)。
- **整数の算術** (2026-10-26): `ev/num-op-vals` は両辺が Int なら + - * と比較をその場で計算する。溢れるときと
  それ以外は `num-op-slow` (BigInt への昇格、組み込み関数) に回す。gencode も同じ関数を呼ぶ。
- **JSON の数** (2026-10-26): 指数が無く 18 桁以内の数は、JSON の読み手が Int で読み、`num/of-scaled` で
  `num/parse-lit` と同じ値 (整数は NInt、小数は末尾の 0 を落とした Dec) を作る。BigInt を経ない。
- 計測の台: `tools/dw-bench/run.sh` が 7 つの式を、実 DW (JIT 後の中央値、`DwBench`) と mulay の閉包・事前コンパイル
  (`dwt -r N`) で比べる。最新の値は docs/todo.md の「性能」。
- 残りの候補: Obj の索引、関数呼び出しのフレームの確保 (Frame と slot の Vec で 2 回)、map の遅延評価
  (`(xs map f)[0]` は実 DW では他の要素を評価しない。ADR 105)、バイトを読む `nth` の inline (clay に依頼済み)。
- 比較の基準は実 Mule の数値。当初は mulet の native 版の数値 (アーカイブした mulet の `docs/benchmarks`) とも比べた。
- サーバではコンパイル済みの木を全スレッドが読む。起動状態を def に置いて不死にし、参照カウントの原子的な
  増減がコア間で競合しないようにしている。最新の計測は docs/todo.md の「性能」 (2026-10-05 より前の計測と経緯は、git の履歴にある docs/todo.md の旧版)。
