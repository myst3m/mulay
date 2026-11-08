# 029 — キー選択の結果は、キーの属性と名前空間をメタデータ `@attrs` / `@ns` で包んで運ぶ

状態: **採用** (2026-09-28、ce64f08 の初版から)

## 決定
- DW の値 (`v/Val`) は位置も親も持たない。`.k` で選んだ値からキーの属性 (`.@a`) と名前空間 (`.#`) を読めるように、
  **キーに属性か名前空間があれば、選んだ値を `VMeta` で包み、メタデータ `"@attrs"` (属性の Object) と `"@ns"`
  (名前空間の値) に入れる** (`sel/with-key-attrs`)。属性も名前空間も無いキーなら包まない。
- 属性の選択 (`.@name`、`.@`) は、値が Key ならキーの属性、`@attrs` を運ぶ VMeta ならそのメタデータを読む
  (`attrs-of`)。`@attrs` を運ぶ値が Array でも、属性はキーのもの (`key-attrs?`)。
- `.#` は Key なら直接、キー選択の結果ならメタデータから名前空間を読む。
- `@` で始まるメタデータは内部のもので、エラーの文言に載せるメタデータの表示からは除く (`coerce_time` の表示)。
- セレクタや演算は VMeta の中身を透過的に見る (`v/unmeta`)。

## 理由
- 実 DW でも `payload.root.@id` は「root というキーの属性」を指す。mulay の値はキーへの参照を持たないので、
  選択の結果にキーの属性を添えて運ぶ。VMeta はセレクタや演算から透過なので、値の意味は変わらない。

## 場所
- `mulay.dw.sel/with-key-attrs`、`mulay.dw.sel/attrs-of`、`mulay.dw.sel/key-attrs?`、`mulay.dw.sel/attr-sel`、
  `mulay.dw.sel/all-attrs-sel`、`mulay.dw.sel/first-field-val`、`mulay.dw.sel/ns-sel`
- `mulay.dw.val/VMeta` (`Val` の腕)、`mulay.dw.val/unmeta`
