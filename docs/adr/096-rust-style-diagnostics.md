# 096 — 開発者に見せるエラーを Rust 風にする (Mule の文言は error.description にだけ残す)

状態: **採用** (2026-10-24)

## 背景

これまでは、エラーの文言を実 Mule と一字一句同じにしていた。ただ、Mule の文言は場所を示さず (`Unable to resolve reference of: `itmes`.`)、
直し方も言わない。ユーザーは、開発者が読む表示は Mule に合わせなくてよいので、Rust のように「何が・どこで・おそらくこう直す」が
分かる形にしたいと決めた (2026-10-24)。

ただし `error.description` はアプリから読める値で、API の応答にそのまま出ることがある。エラーの型 (HTTP:NOT_FOUND など) は
error-handler の振り分けに使う。この 2 つは実 Mule に合わせたまま残す (ユーザーが選んだ範囲)。

## 決定

- **データと表示を分ける。** `DwErr.msg`・`MErr.description`・DW の golden (`%%% error` の 1 行目) は今のまま Mule の文言。
  Rust 風の文は、表示するときに、持っている位置 (span) から作る。エンジンの中では作らない (失敗する要求のたびに作ると、負荷が高いときに遅くなるため)。
- **表示は `mulay.lib.diag` の 1 か所で作る。** `Report` は level・code・見出し・ファイルとソース・ラベル (主は `^`、副は `-`)・note・help を持ち、`render` で文字にする。
  - 印は端末の桁で揃える (`lib/uni/width`: East Asian の Wide と Fullwidth は 2 桁、結合文字は 0)。タブは 4 桁にする。CRLF の CR は出さない。
  - 離れた行の間は `...`。1 行だけ離れているときは、その行を出す。複数行にまたがるラベルは最初の行の終わりまで印を付ける。
  - 色は ANSI。端末に出すときだけ (stderr が tty で、`NO_COLOR` が無いとき)。
  - 「もしかして」は `closest` (OSA の編集距離。大文字小文字を区別しない。語の長さの 3 分の 1、少なくとも 1 まで。1 文字の語には出さない)。
- **DW のエラーの読み替えは `mulay.dw.explain`。** Mule の文言を型で見分け、見出しを短い英語にし、元の 1 行目は `note: DataWeave: ..` に残す (公式の文書を探すときの手がかり)。
  help は直し方がはっきりしているときだけ付ける。
  - 名前が見つからない: 近い名前 (スクリプトの var・fun・引数・入力・組み込み関数)。`mulay dw` で payload などが無いときは、入力の渡し方。
  - 定義より前で使った変数: 後ろの定義を副ラベルで示し、上へ動かすよう言う。
  - 予約語のキー: 引用符で囲む。
  - 書き出しの option の名前違い: 近い option。位置はスクリプトの中でその名前を探す (writer のエラーは位置を持たないため)。
  - 関数の引数の型違い: 受け取った型と受け付ける組み合わせ。`+` に String なら `++`、Null なら `default`。組み込み関数の中で起きたら「(inside `sum`)」。
  - String から Number への変換の失敗、Null の変換: 確かめ方と `default`。
  - 構文のエラー: 文の `expected ..` をラベルにする。
  - 綴りを間違えたフィールド (`$.prise`) は DW ではエラーにならず null になるので、ここでは見分けない。Null のエラーの help で「綴り違いでは」と添える。
- **出す場所の順番:** `mulay dw` (この ADR の最初のコミット) → XML の中の DW (validate・ログ・`mulay test`・livenote。ADR 091 の属性の値の位置で、スクリプトの位置をファイルの位置に直す) → ログ。
  ログの例外の枠を変えるときは、mule-oracle の比較を「同じ事実 (メッセージ・エラーの型・要素・行・FlowStack) を持つか」に変え、`docs/compat/deviations.md` に書く。

- **XML の中の DW** (2026-10-24): parse が式の元の位置 (`ExprSrc` の file と base) を入れる。属性は要素の行から「名前=」を探して
  引用符の中で、本文 (CDATA など) は要素の行から後ろで、式の文字を探す。実体 (`&quot;` など) やプロパティの置き換えで
  元の文字と違えば -1 で、行だけを示す。読み込みの DW のエラーは `Diag` の `rep` に Report を持ち、validate と run の起動で出す
  (`Diag` の msg は今のまま。munit などが読む)。
- **ログの例外** (2026-10-24): `MErr` は DW のエラーの場所 (`DwX`: 文・ファイル・バイト位置・式) だけを持ち、ログを書くときに
  `App` の `texts` (読み込んだ XML の文字) から Report を作る (`rt/explain/exc-report`)。DW 以外のエラーは、要素の行の開きタグ
  (`<raise-error`) に印を付ける。note に element と flow stack を置く (mule-oracle はこの 2 つと見出しの型・メッセージで比べる)。
  ログのファイルには色を付けない。

- **`mulay test`** (2026-10-24): 端末に出す失敗とエラーを Rust 風にする (`app/munit/failure-report`)。`--golden` のファイル
  (munit-oracle が実 MUnit と比べる) は今のまま。見出しは「expected 5, but got 4」(MUnit の Expected/but の行から型の
  メタデータと ` at (root)` を除く)、期待したエラーとの食い違いは「expected the error APP:BOOM, but MULE:EXPRESSION was
  raised」など。印は、エラーの要素の開きタグ (`rt/explain/located`)。MUnit の元の行は note に残す。色は stdout が tty の時だけ。

- **場所の付かない DW のエラー** (2026-10-24 に調べた): ストリーミングで流す式 (`run-streamed`) は、失敗すると最後まで評価する
  道 (`run-script-whole`) に戻るので、場所 (dx) が付く。`deferred=true` の途中の要素のエラーは、実 Mule でもエラーにならず、
  読む側に途中までか空の出力が届くだけ (fixture dw-deferred)。場所を付けるエラーが無く、ログを足すと実 Mule と違う
  ので、何もしない。

## 場所

- `mulay.lib.diag` (`Report`・`report`・`with-src`・`label`・`note`・`help`・`render`・`edit-distance`・`closest`)、`mulay.lib.uni/cp-width`・`width`
- `mulay.dw.explain` (`Ctx`・`explain`・`compile-report`・`run-report`・`candidates`)、`mulay.dw.engine/run-text-full`
- `mulay.app.munit/failure-report`、`mulay.rt.explain/located`、`mulay.cli.boot` の `cmd-dw`・`finish`、`mulay.mule.parse` の `locate`・`compile-script-at`、`mulay.rt.explain` (`dw-x`・`exc-report`)、`mulay.rt.engine` の `log-error`
- `tools/mule-oracle/mule-oracle` の `exc_facts`・`norm_log`
- テスト: `test/munitout/munitout_test.clay`、`test/diag/diag_test.clay`、`test/diag/explain_test.clay`、`test/uni/uni_test.clay` (display-width)
