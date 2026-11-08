# 111 — dw::test (Tests・Asserts) は mulay が持つ DataWeave のモジュールとして書き、等しさの差分だけ Clay の組み込みにする

状態: **採用** (2026-11-02)

## 実 DW の挙動 (data-weave-testing-framework 2.11.0-20251202、test/fixtures/dw/dwtest に記録)

- `"名前" describedBy [..]` は suite、`"名前" in do { .. }` はテスト。結果は TestResult (name・time・status・tests・errorMessage・location)。
  suite の status は中のテストが落ちても "OK"。
- テストの status は MatcherResult の matches で OK か FAIL、評価の誤りは ERROR。errorMessage は、reasons があればそれを改行でつなぐ
  (空なら "")、無ければ description。配列を返すテストは最初に合わなかったもの、全部合えば最後のもの。ERROR は
  "<kind>:<message> at:\n<try の location>"、キーの順は name・status・time (OK・FAIL は name・time・status)。
- `x must matcher` は matcher の結果に " From `<locationString(matcher)>` at line N of <sourceIdentifier>.dwl." を付ける
  (description と reasons の各行)。中置で呼ぶので右辺は ($, $$, $$$) -> 右辺 に包まれ (ADR 108 の後の 3a631861)、呼ぶと matcher
  そのものが返る (test/fixtures/dw/infix_lambda_test/function-rhs-wrapped.dwt)。条件 (Boolean を返す式) は
  "Assertion `..` failed with value ..."。`x must [..]` は要素ごとに包まれ、最初に合わなかったものを From を付けずに返す。
- `@Skip` を付けても飛ばさない (実 DW の記録)。
- equalTo の理由は、値・型・配列の長さ・無いキー・余計なキー・XML の属性の種類ごとに決まった文で、後ろの要素の違いから並ぶ。

## 決定

- dw::test の jar にはライセンスの記載が無いので、DWL を写さない。公開の API (関数の名前と引数) と、実 DW で記録した結果だけから
  書き直す。jar は golden を作る時にだけ使う (tools/dw-oracle/fetch-testfw.sh が target/dw-testfw に取り、DW_ORACLE_EXTRA_CP で渡す)。
- mulay が持つ DataWeave のモジュールの仕組みを作る: 元は tools/dwl/<モジュールのパス>.dwl、`tools/gen-dwl-modules.py` が
  `src/mulay/dw/stdmods.clay` の文字列にする (tools/test.sh がずれを見つける)。engine の load-modules は、`dw::` で始まる名前のうち
  stdmods にあるものだけを、ユーザーの読み手より先にここから読む (ほかの `dw::` は今までどおり Clay の組み込み)。
- equalTo の差分 (入れ子をたどる再帰) は Clay の組み込み `dw::test::internal::Native::equalityReasons` にする。解釈する DWL の再帰より
  速く、文言の形を 1 か所で持てる。値を DW の書式で書く `readable` も同じ所に置く。
- `x must ..` の右辺は包まれて届くので、呼んだ結果が関数ならもう 1 度 x で呼ぶ (実 DW の結果と同じになる)。

## 実 DW と違うところ (docs/compat/deviations.md、docs/todo.md)

- TestResult の location: mulay の dw::Runtime location は、引数を通した値 (テストの名前) の場所を持たないので "Unknown location"。
  実 DW は名前の文字列の場所 (例: `"adds"` の 8 行 3〜9 桁)。golden は location を除いて比べる。
- イベントのログ (TestStarted など、実 DW の Maven の plugin が出す形) は作らない。mulay dw test の出力は mulay 独自の形にする (下の追記)。
- inputsFrom・outputFrom・evalPath (2026-11-02): ファイルを読む部分は Clay の組み込み dw::test::internal::Files (inputsOf・outputOf・
  resourceText)。資源の場所はシステムプロパティ dwtestResources (既定 resources。mulay dw test は src/test/resources があれば
  それにする。実 DW の Maven の plugin と同じ)。evalPath のスクリプトはモジュールを探す場所 (--path、スクリプトの場所、
  src/main/resources) から読み、dw::Runtime::eval で評価する。inputsFrom のキーはファイル名の順 (実 DW はファイルの一覧の順)。

## 追記 (2026-11-02)

- `.^skip`・withConfig・testToRun (dw::Runtime::prop で読むシステムプロパティ) を足した。
- `mulay dw test [--path d]... [-D name=value]... [<file-or-dir>...]`: 指定 (既定は src/test/dw か今のディレクトリ) の下の `---` を持つ
  .dwl を評価し、結果が TestResult なら出力する。FAIL か ERROR があれば終了コード 1。本文を持たない .dwl (モジュール) は飛ばし、
  TestResult を返さないスクリプトは ERROR にする。
- 出力は実 DW と揃えず、読みやすさで決める (ユーザーの判断、2026-11-02)。ファイルごとに suite の入れ子を字下げした木にし、
  テストは ✓ (OK)・✗ (FAIL、ERROR は "(error)" を付ける)・○ (SKIP、理由) で並べる。skip した suite は 1 行で、中のテストの数を書く。
  失敗は後ろの Failures にまとめ、`suite › テスト  (ファイル)` の見出しと TestResult の errorMessage を字下げして出す。
  コンパイルや評価で失敗したファイルは Rust 風の診断 (ADR 096) で出す。最後の行は `ok`/`FAILED` と数 (passed・failed・errors・
  skipped、テストとファイルの数、時間)。端末で NO_COLOR が無ければ色を付ける。
- ランナーはスクリプトの sourceIdentifier をファイルの場所 (.dwl を除く) にする (eng/with-source-id)。Asserts の
  "at line N of X.dwl" が anonymous.dwl でなく本当のファイルを指す。dwt と dw-oracle の経路は anonymous のまま。
- errorMessage の文は TestResult の値で、スクリプトから見えるので実 DW と同じ文のまま (golden)。ランナーはその文を分解しない。

## 場所

- tools/dwl/dw/test/{Tests,Asserts}.dwl、tools/gen-dwl-modules.py、src/mulay/dw/stdmods.clay、src/mulay/dw/lib/testdiff.clay、
  src/mulay/dw/engine.clay (load-modules・module-source)
