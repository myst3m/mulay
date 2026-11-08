# 106 — 同じ関数を何度も呼ぶ組み込み関数は、呼び手を 1 回準備する

状態: **採用** (2026-10-26)

## 決定

- 組み込み関数が DW の関数を要素ごとに呼ぶとき (map、filter、reduce、集計の合成 fold-run、mapObject、pluck、filterObject、
  並びの map・filter・flatMap など)、ループの前に呼び手を作る: `rt/env-prep env f na` (引数の Vec)、`rt/env-prep2 env f`
  (引数 2 つ)、`rt/env-prep-ix env f` (要素と添字の Int)。
- 呼び手は `ev/prep-fnv`・`prep-fnv2`・`prep-ix` が作る。次の条件をすべて満たすときだけ、Frame を直接作って `ev/run-def` を呼ぶ:
  - スクリプトの関数である (組み込み関数ではない)。
  - overload の組 (alts) を持たない (組は引数の型で実行時に選ぶ)。
  - 渡す数が引数の数以上か、足りない分の既定値がすべて定数 (`CFn` の `consts`、R が RConst)。右に詰める束ね方 (bind-right) をする
    関数は除く。
  それ以外は今までどおり `call-fnv` に任せる。速い道は `call-fnv` → `call-def` (check なし) → `bind-loose` → `bind-args` と
  同じ Frame (引数を引数の数で切り、定数の既定値と null で slot の数まで埋める) と同じ深さ (d + 1) を作る。
- `env-prep-ix` は、関数が 2 番目の引数を読まない (`CFn` の `reads`: 本体と既定値の式に slot 1 の RSlot が無い) なら、
  添字を箱詰めせずに null を渡す。読まない slot の値は観察できない。
- `ev/run-def` は 1 回目の本体の評価を末尾呼び出しの数え (hd・hm) なしに行い、末尾呼び出しが起きたときだけ `run-hops` で数える。
- 二項演算 `ev/num-op-vals` は、両辺が Int のとき + - * と比較をその場で計算する。溢れるとき・mod・それ以外の型は
  `num-op-slow` (BigInt への昇格、文字列の ++、組み込み関数) に回す。gencode も同じ関数を呼ぶ (ADR 030 の同じ挙動)。
- R の子をたどる `kids` は `mulay.dw.rir` に置く (rir の構造の知識。eval・gen・gencode・purity が使う)。

## 理由

- 3,000 万要素の `sizeOf((1 to 30000000) map ($ + 1))` で、閉包の評価は 2.9 秒かかり、実 DW (JIT 後 1.2 秒) に負けていた。
  内訳は 1 要素ごとの Hooks の間接呼び出し・Dyn からの取り出し・overload の選択・引数の束ね・空の Vec の確保と解放で、
  どれも同じ関数を呼ぶ間は変わらない。準備を 1 回にし、算術をその場で計算して 1.18 秒にした (docs/todo.md の「性能」)。
- 呼ばれる側の挙動 (失敗の位置、深さ、末尾呼び出しの数え方) は変えない。速い道に入れない関数は元の道に回すので、型による
  overload の選択や式の既定値の評価の順は保たれる。

## 場所

- `mulay.dw.rt`: `Hooks` の `prep`・`prep2`・`prep-ix`、`env-prep`・`env-prep2`・`env-prep-ix`
- `mulay.dw.eval`: `prep-fnv`・`prep-fnv2`・`prep-ix`・`fill-slots`・`const-tail`・`run-def`・`run-hops`・`num-op-vals`・`num-op-slow`、
  `CFn` の `consts`・`reads` (`const-defaults`、`param-reads`、`reads-slot?`)
- `mulay.dw.lib.core_coll`: 呼び手を使う組み込み関数
- `mulay.dw.rir/kids`
