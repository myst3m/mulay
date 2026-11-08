# 108 — DW の関数の値が評価の外へ出る時は、ホストの関数 (実 Mule の WeaveFunctionWrapper) にする

状態: **採用** (2026-11-01)

## 問題

- DW の関数の値 (`v/FnV`) は、その評価の CProg の中の関数の番号 (`def`) と捕獲した値しか持たない。番号は作った評価の
  表でしか意味を持たない。
- Mule の変数・payload に入った関数を別の式から呼ぶと、呼んだ側の表を同じ番号で引いていた。表に無ければ clay の `nth` が
  範囲外で止まり (要求は 500 の "internal error"、エラーハンドラーで拾えない)、表にあれば別の関数を呼んだ
  (`[1, 2] map ((v) -> vars.inc([v]))` は自分を呼び続けて Stack Overflow になった)。

## 実 Mule 4.11.3 の挙動 (test/fixtures/apps/dw-function-values、2026-11-01 に記録)

- 式の結果が Java になる所 (set-variable、set-payload、ee:transform の application/java) で、関数はオブジェクトや配列の中も含めて
  `org.mule.weave.v2.module.pojo.function.WeaveFunctionWrapper` になる。名前付きの関数も組み込み関数 (`upper`) も同じ。
- それを別の式から読むと、名前が AnonymousFunction、引数が `rhs: Array` 1 つの関数になる。配列の要素を元の関数の引数にして呼ぶ
  (`vars.inc([41])` は 42、`vars.z([])` は 7、既定の引数も効く)。引数の数が違えば "Too many arguments (2) for function with
  parameters (rhs)." / "Not enough arguments (0) ..."、型が違えば "You called the function 'AnonymousFunction' with these
  arguments: .. But it expects arguments of these types: 1: Array"。場所は呼ばれた式 (`vars.inc(41)` なら `vars.inc`)。
- 要素は Java を通って戻る: 数は `3 as Number {class: "java.lang.Integer"}` のように class の印を持ち、関数は同じく
  WeaveFunctionWrapper になる (引数に渡したラムダは、中で呼ぶと配列を要求する)。戻り値も同じ (関数を返す関数の戻り値は
  配列を要求する)。
- 要素が多ければ余りは捨てる (`vars.inc([1, 2])` は 2)。少なければ元の関数の "Not enough arguments (1) for function with
  parameters (a, b)." で、抜粋は元の式のその関数全体、Trace はその関数 (AnonymousFunction) の後に呼んだ側の main。
- 元の関数の中の誤りは、元の式の行と桁で抜粋を示し、Trace は元の式の中の段 (ラムダは AnonymousFunction) の後に呼んだ側の段が続く。
- WeaveFunctionWrapper をもう一度変数に入れても包み直さない (`inc2 = #[vars.inc]` の `vars.inc2([[1]])` は `[1, 1]`)。
- 変数から読んだ関数の印は、ほかの Java の値と同じく `{encoding, mediaType, mimeType, class}` で、class は
  `org.mule.weave.v2.module.pojo.function.WeaveFunctionWrapper`。入れ子の関数は class だけ。表示は `(rhs:Array) -> ???`。
  application/dw で書いても raw は出ない (Object・Array の raw と同じ)。
- HTTP の応答の本文にすると Java の toString (`org.mule.weave.v2.module.pojo.function.WeaveFunctionWrapper@<16 進>`、
  content-type は application/java)。
- `[1, 2] map vars.inc` が "Cannot coerce Function to String" になるのは包みのせいではない。実 DW は map・filter などの右辺が
  ラムダのリテラルでなければ `($, $$) -> 右辺` にするので、結果が関数の並びになって書けない。

## 決定

- `v/FnV` の `name` を消し、`host: Option(Host)` を置く。`Host` は名前・引数の名前と型・呼び出しの閉包を持つ。
  - name は def と CProg (組み込み関数は表) から引けるので、FnV に持たなくてよかった。読んでいたのは core_coll の
    `dollar-fn?` だけで、その規則 (暗黙の `$` のラムダの `$$` の既定は reduce の初期値にしない) は eval の `param-default-of` に移した。
  - clay の ADR 104 で、数える欄が 2 つまでの record は箱にならない C の値になる。FnV は caps と name の 2 つで、name を残して
    host を足すと 3 つになり、関数の値を作るたびに箱を作る。Host は数える欄が 4 つで箱になり、Option(Host) は印と箱への
    ポインタなので、FnV は caps と host の 2 つのまま。`(->None)` は箱を作らない (生成される C で確かめた)。
- ホストの関数 (host が Some) の def は -1。呼ぶ入口は `ev/call-fnv` で、そこが host を先に見る (組み込み関数の 0 番として
  扱わない)。def が負のとき call-fnv を通らずに組み込み関数として読む所は純粋さの判定だけで、`env-pure?` は host なら偽。
- DW がホストの関数を呼ぶ時は、引数の数と型を Host の宣言で確かめ (ユーザーの関数と同じ文言。数が負なら確かめない)、
  呼ぶ側の評価の関数を外へ出す 2 つの道具 (`v/Caller`: Ctx の wrap による包み (`export-fn`) と、そのまま呼ぶ包み
  (`plain-export`)) を渡して閉包を呼ぶ。どちらで引数の関数を出すかはホストの関数が決める (WeaveFunctionWrapper は前者、
  dw::Runtime の間の関数は後者。呼ぶ側の Ctx の wrap で決めると、`mulay run` の中の eval の関数が Java の包みの意味になる)。この時の誤りの場所は呼ばれた式 (`call-val-at`、
  `call-sp`)。同じ評価の中の関数の呼び出しは今までどおり呼び出し全体 (実 DW は同じ評価の中の誤りを静的に出すので、実行時の
  場所を記録できない)。
- 評価の外へ出す包み方は、評価を作る側が Ctx の `wrap` (Option) に渡す。None (`NO-WRAP`) は、元の評価でそのまま呼ぶだけの
  ホストの関数 (`plain-host`) にする (形は変えず、別の評価の表を引くことだけを無くす)。その中の誤りは、元の評価の Srcs で
  抜粋と段の位置を描いてから返す (`plain-rehome`)。引数と戻り値は遅延した並びを読み切ってから出す (並びの中の関数が元の
  評価の外で作られないように)。rt は実 Mule の WeaveFunctionWrapper の意味の包み (`mule-wrap`) を、式の評価
  (`run-script-whole`) と遅延した出力 (rt/deferred) に渡す:
  - 結果が Java になる所 (`java-out`) で関数を包む。class の印を付ける歩き (`java-meta`・`java-nested`・`java-inner`) が値を
    作り直すので、その中で包む (別に歩くと、20 万要素の Java の結果で命令が 1 割増えた)。印を付けない時は `dev/export-val` で、
    これは関数が無ければ値をそのまま返す (`has-fn?`。作り直さない)。
  - 包んだ関数を呼ぶと、要素を Java に通して (関数は呼ぶ側の評価で包み、class の印を付ける) 元の評価の Ctx で `call-fnv` し、
    戻り値も Java に通す (関数は元の評価で包む)。
  - 元の評価で起きた誤りは、元の式の ExprSrc と Srcs で抜粋 (`origin`) と段の位置 (`where`) を描いてから返す (`rehome`)。
    場所の無い誤り (引数の数) は、その関数の定義の範囲と、その関数の段を足す。元の式の main の段は、その関数の名前の段にする。
  - すでにホストの関数なら包まない。
- dw::Runtime の `eval`・`run` は別にコンパイルしたスクリプトを走らせる。実 DW では、eval の結果の関数も、入力の値に渡した
  関数も、ふつうの関数として呼べる (test/fixtures/dw/runtime_eval_test。前は表の番号がずれて abort した)。runner に渡す入力の値は
  呼ぶ側の評価で、eval の `result.value` は中の評価で、そのまま呼ぶ包みにする (読み切ってから)。
- 開発者向けの診断 (ADR 096。`mulay run` のログと `mulay dw`) は、誤りが別の源 (`origin` がある) なら、その式の中の呼び出しの
  場所を指す。
- 包んだ関数は元の評価の Ctx (入力の値を含む) を閉包に持つ。Ctx は包んだ関数を持たないので、数え直しの輪はできない。
- HTTP の本文などでバイト列にする時、Java の型の関数は Java の toString と同じ形にする (16 進は乱数。シナリオは mask)。

## 場所

- `mulay.dw.val/FnV`・`Host`・`Caller`、`mulay.dw.eval/call-fnv`・`call-host`・`export-fn`・`plain-export`・`plain-host`・`plain-rehome`・
  `export-val`・`NO-WRAP`・`call-val-at`・`Ctx` の `wrap`・HOOKS の runner、`mulay.dw.engine` の run-script、
  `mulay.dw.engine/eval-compiled-w`・`stage-fn-w`、`mulay.rt.engine/java-out`・`mule-wrap`・`rehome`・`CM-FN`、
  `mulay.rt.event/bytes`、`mulay.rt.explain/dw-x`、`mulay.dw.explain/run-report`、`mulay.dw.fmt.dw` の `fn-params`・`meta-fields`
