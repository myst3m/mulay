# 025 — resolve は slot の番号を再利用せず、値の位置は location の隠れた引数で渡す

状態: **採用** (2026-09-28、ce64f08 の初版から。location の隠れた引数は 2026-09-29、a64a183。update の case の lazy は 2026-10-12、d0962b0)

docs/dw-eval.md §1 (名前解決、関数の持ち上げ、slot の割り当て) を補う。

## 決定
- **ブロックの終わりでは束縛を n 個に戻すだけで、slot の番号は再利用しない** (`pop-binds`)。フレームの大きさは
  最大の slot 数になる。
- フレームは関数ごとに 1 つ。束縛は slot か「同じ do グループの関数 (sib)」。外側のフレームの束縛を参照すると、
  その関数 (グループなら、グループの捕獲リスト) の捕獲に加わる (`add-cap`、`lookup-caps`)。
- 初期化の前の参照を飛ばす判定は、同じフレームの中は書いた順に評価するので静的に決める (`lookup-ref`)。ただし
  update の case は実 DW では値を読むときに評価するので、case の外で宣言した do の var / fun は飛ばさない
  (St の `lazy` に解決中の case の位置を持つ)。
- **値の位置 (`location(x)` / `locationString(x)`) は、resolve が引数の式から値を作った式を形でたどり、その位置を
  隠れた 2 つ目の引数 (`{s, e}`、標準ライブラリの関数なら `{m, n}`、分からなければ `{}`) として足す**
  (`with-origin`、`origin-of`)。値そのものは位置を持たない。

## 理由
- slot を再利用しないのは、捕獲の整合を単純に保つため。
- mulay の値は位置を持たない (docs/compat/deviations.md「値のソースの位置」)。location が要るのは引数の式なので、
  resolve が形でたどれる範囲を静的に渡す。たどれないもの (関数の引数など) は "Unknown location" になる。

## 場所
- `mulay.dw.resolve/pop-binds`、`mulay.dw.resolve/add-cap`、`mulay.dw.resolve/lookup-caps`、`mulay.dw.resolve/lookup-ref`、
  `mulay.dw.resolve/St` (`lazy`)
- `mulay.dw.resolve/with-origin`、`mulay.dw.resolve/origin-of`、`mulay.dw.resolve/origin-node`
