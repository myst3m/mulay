# 050 — 式はロード時にコンパイルし、参照する入力を字句で調べて必要なものだけ読む

状態: **採用** (2026-09-28。payload の遅延 parse とメタデータだけの参照は 2026-09-29 a231e46、vars.名前 の記録は 2026-10-06 bb01b71)

## 決定
- **式の形**: 値全体が `#[` で始まり `]` で終わるものを DW 式とする。中身がヘッダ付き (`%dw` で始まる、または
  `output import var fun ns type input` の指示子で始まり `---` を含む。`#[output text/plain --- payload]`) ならそのまま
  スクリプトとして、そうでなければ `%dw 2.0\n---\n<式>` に包んでコンパイルする。
- **値の途中の `#[..]`** (`"Hello #[vars.x]!"`) は補間しない。実 Mule と同じく起動はでき、評価すると MULE:EXPRESSION で失敗する。
  その失敗を再現する式にコンパイルする (`pval`)。logger の message と parse-template だけは文字列と式の部品に分け、実行時につなぐ。
- **式が必須の属性** (when の expression、foreach の collection など) は `#[ ]` が無くても式として扱う (`pval-expr`)。
- transform の `resource="x.dwl"` は資源から読み、`${}` の置換はしない。利用者の DW モジュール (`import mymod::Utils`) は
  アプリの資源の `mymod/Utils.dwl` から読む (`module-loader`)。
- コンパイルの失敗は `file:line: ...` として diags に積み、起動しない。文言には実 Mule (要素の行とメッセージだけ) より多く、
  スクリプトの抜粋と位置を付ける。
- **参照する入力** (`ExprSrc` の `uses`) は字句だけで調べる (`input-refs`): 文字列とコメントは飛ばし、文字列の中の `$(..)` と
  `$name` は式として見る。セレクタやキー (直前が `.` `^` `@` `#`、`.?` `.*` の後、直後が `:` で `::` でない) は参照に数えない。
  - `vars.名前` は名前ごとに記録する (出力形式の推論がその変数の mime を引くため)。
  - payload のメタデータ (`^mimeType`、`^encoding`) だけを読む参照は `payload^` として数える。
  - m/BINDINGS 以外の名前もそのまま記録する。
- **実行時は参照される入力だけを読む** (`mulay.rt.engine/inputs`、`vars-val`):
  - payload は式が参照するときだけ parse する。`payload^` だけなら parse せず、値の代わりにメタデータだけを渡す (DEFER も読まない)。
  - RAW の変数は読むときに parse し、parse した TypedValue を Event に戻す (次の式で読み直さない)。読めない変数は、式がその変数を
    名前で参照しているときだけ失敗にする (実 Mule は変数を読む時に parse する)。
  - deferred の変数は、式が名前 (`vars.x`) で参照するときだけ読む (読めるのは 1 回だけ)。
  - vars を名前の無い形 (`vars[k]`、vars 全体) で読むときは、出力形式の推論では Java として数える。

## 理由
- 実行時に DW を parse しない (mulet の負債 D)。
- 実 DW も値を読むまで parse しない。使わない payload を parse すると、実 Mule では起きない失敗や、読めるのが 1 回だけの
  ストリームの消費が起きる。

## 場所
- `mulay.mule.parse`: `DIRECTIVES`、`pval`、`pval-expr`、`template-parts`、`module-loader`、`input-refs`、`value-ref?`、
  `meta-only-ref?`、`add-var-ref`、`add-raw`、`with-where`
- `mulay.mule.model`: `ExprSrc`、`BINDINGS`
- `mulay.rt.engine`: `inputs`、`vars-val`、`infer-mime`
