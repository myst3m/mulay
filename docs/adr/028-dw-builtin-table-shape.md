# 028 — 組み込み関数の表: (モジュール, 名前) ごとに 1 つ、型は番号で照合し、モジュールの定数も引数 0 の組み込みにする

状態: **採用** (2026-09-28、ce64f08 の初版から。型の番号と cand は ecddec4、pipe / fold と exact-index は 2026-10-04、957ac03)

docs/dw-eval.md §4 (Builtin と Overload、選択の規則、実装の置き場所) を補う。

## 決定
- **同じ (モジュール, 名前) の関数が複数のファイルにあれば、オーバーロードを登録順に 1 つの Builtin にまとめる**
  (`engine/merge-builtins`。例: Core の contains は配列版と文字列版が別ファイル)。モジュールの追加は
  `engine/all-builtins` に 1 行足す。
- **型は番号で照合する**。Overload は引数の型の名前 (`params`、表示用) と番号 (`tags`、`rt/type-tag`) を持つ。
  0 は Any、知らない名前は -1 (どの値にも当てはまらない)。和・積など番号の無い型は -2。
- **`cand`**: 最初の引数の型の番号ごとに、当てはまりうるオーバーロードの番号を上からの順で前もって持つ
  (`rt/builtin` が作る)。`rt/invoke` はこの候補だけを、変換なしで当てはまる最初のもの、無ければ変換して当てはまる
  最初のものの順に試す。変換しても当てはまりえないものは試さない。
- **`pipe` と `fold`**: 集計の合成 (eval の `cx-fold`、gencode の展開) の印。pipe は要素を 1 つずつ作れる生産側
  (dw::Core の map 1、filter 2)、fold は要素を 1 つずつ受けて計算できる集計 (dw::Core の sizeOf 1、sum 2、avg 3、
  max 4、min 5)。どの組み込み関数かは実行時にこの印で確かめる。
- **モジュールの定数 (Math::PI、Tree::OBJECT_TYPE など) は、引数 0 のオーバーロードを 1 つ持つ組み込みとして表す**
  (`rt/constant`)。resolve は定数の組み込みが値として参照されたら、その呼び出し (`RCallB bi []`) にする。
- `rt/exact-index`: 引数の型の番号から invoke が変換なしで選ぶオーバーロードを引く。invoke を通さずに計算した
  失敗 (集計の合成の、生産側と集計側の失敗) に invoke と同じ枠 (`native-frame`) を付けるために使う。

## 理由
- 型の名前の文字列を比べず番号で照合し、候補を最初の引数の型で絞るのは性能のため (ADR 017、ecddec4)。
- 定数を引数 0 の組み込みにした理由の記録は無い (コメントは「値として参照される」とだけ)。

## 場所
- `mulay.dw.engine/all-builtins`、`mulay.dw.engine/merge-builtins`
- `mulay.dw.rt/Overload`、`mulay.dw.rt/overload`、`mulay.dw.rt/Builtin`、`mulay.dw.rt/builtin`、`mulay.dw.rt/type-tag`、
  `mulay.dw.rt/invoke`、`mulay.dw.rt/constant`、`mulay.dw.rt/constant?`、`mulay.dw.rt/exact-index`
- `mulay.dw.eval/cx-fold`、`mulay.dw.gencode/fold-kind`
