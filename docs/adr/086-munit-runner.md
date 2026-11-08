# ADR 086: MUnit のテストを `mulay test` で回す

日付: 2026-10-20。状態: 決定。

## 背景

- Mule のアプリのテストは MUnit 3 で書く。テストは `src/test/munit/*.xml` に置く。
  - 要素: munit:config、munit:test (behavior / execution / validation)、munit-tools:assert-that、mock-when、verify-call など。
- 実 MUnit は mvn から組み込みの Mule を立ち上げて回す。1 回の実行に十数秒かかる。
- 正解は実 MUnit 3.7.4 (MULE_EE 4.11.3) とする。
  - `tools/munit-oracle` が fixture のコピーで `mvn test` を回し、surefire の報告から結果を記録する。
  - 記録する中身: テストごとの成否と、失敗の文言の先頭 (スタックを除く)。
- 実 MUnit で確かめたこと (test/fixtures/munit/munit-asserts):
  - suite (ファイル) ごとにアプリを立ち上げ直す。suite の中のテストの間では状態 (ObjectStore) が残る。
  - flow の source (scheduler、listener) は動かない。
  - set-event が無いときの payload は空文字列 (`*/*`)。
  - expectedErrorType があってエラーが出たときは、validation を走らせない。

## 決定

- `mulay test [<app>]`
  - suite のファイルごとに、アプリの設定と suite を 1 つのアプリとして読み込む (`ld/load-test`)。
  - `run/prepare` で Ctx を作り、コネクタは初期化する。source は起動しない。
- MUnit の要素は mule/model の MSuite と MTest にする (mule/parse の `parse-munit`)。
  - 中の処理は普通のプロセッサの列として読む。
  - munit:set-event と munit-tools:* はコネクタの操作 (conn/munit の `munit` と `munit-tools`) になる。
- 判定の順序:
  1. ignore
  2. before-test
  3. behavior と execution
  4. 期待したエラー (型・説明) の照合、または validation
  5. after-test
- 結果は SUCCESS / FAILURE / ERROR / SKIPPED。文言は実 MUnit の形をそのまま作る。
  - assert の失敗: `java.lang.AssertionError: <message> at file: [<suite>], line: [<行>]\nExpected: ..\n     but: ..`。
    - assert の失敗は、cause が `java.lang.AssertionError` の MErr にする。
    - ファイルと行は、エラーの位置 (`<path> @ <app>:<file>:<line>`) から取る。
  - fail と予期しないエラー: `TestExecutionException: Error [NS:ID] while running test '<name>':<description>`。
  - expectedErrorType の型がアプリのどこにも無いとき: `MunitError: The expected error type .. was not found`。
    - 「どこにも無い」の判定: ランタイムとコネクタの型の表 (err/known?) にも、設定の `type=` / `targetType=` にも無いこと。
- `MunitTools::` は munit-tools コネクタが渡す DW のモジュールとする (Connector の `dw-modules` → Hints の `modules` → mule/parse の module-loader)。
  - matcher は `{"type": .., expected: [..]}` のデータで、関数を持たない。
  - 判定は conn/munit の `check` が Clay で行う。DW を使うのは、Diff (equalTo、assert-equals)、`write`、`matches`、比較 (`>`) だけ。
- matcher の文言は 2 系統。
  - DW で判定するもの (equalTo、containsString、greaterThan など) は `Expected: <期待>\n     but: <実際> at <path>`。
    - equalTo は dw::util::Diff の結果をそのまま使う。
    - 実際の値には、Mule の TypedValue の性質を DW の schema として付ける。
      - Java の値: encoding、mediaType、mimeType、class、文字列は contentLength。入れ子の要素は class だけ。
      - Java 以外 (JSON など): 根に encoding、mediaType、mimeType、contentLength (生のバイト数)。
  - 組み合わせ (not、both / allOf、either / anyOf、everyItem、hasItem、hasSize、isEmpty、hasKey、hasValue、withMediaType、withEncoding、closeTo) は Hamcrest の書き方で組み立てる。
    - `was <Java の toString>`、TypedValue の toString、`( and ..)` など。
- `--golden FILE` は、munit-oracle と同じ形で結果を書く。suite の名前、テストの名前の順に並べる。

## クラスパス、source、ポート

- suite の資源は、pom の testResources (既定は src/test/resources) を main の資源より先に探す。DW の readUrl の classpath も、suite ごとにこれにする。
- HTTP の listener のポートは、suite の間ずっと開けておく。要求を受けるのは、そのテストの enable-flow-sources にある flow の listener だけ。
  - 合う listener が無ければ 404 "No listener for endpoint: .." を返す。実 MUnit も同じで、有効にしていないテストからの要求は HTTP:NOT_FOUND になる (munit-asserts の s03)。
  - run/start-flows は、有効な flow 名の atom を要求のたびに見て、経路を絞る。
- munit-maven-plugin の dynamicPorts にあるプロパティ (http.port など) には、実行の初めに空きポートを割り当てる。
- 期待したエラーの型・説明が違うときの `expected:<..> but was:<..>` は JUnit の ComparisonCompactor の書き方にする。
  - 共通の前と後ろは括弧の外に出し、20 文字を超える分は `...` にする。

## mock-when と verify-call

- rt/engine の Ctx に `intercept` (関数の 0 個か 1 個の列) を足す。
  - run-procs は、どのプロセッサを実行する前にもこれを呼ぶ。flow-ref で呼んだ先、スコープの中、エラーハンドラーの中も通る。
  - 返り値 0 なら普通に実行する。1 なら返した event かエラーを使う。
  - `mulay test` だけが関数を入れる。`mulay run` では空で、空かどうかを見るだけになる。
- プロセッサは Loc の elem (`mule:set-payload`、`http:request`) と attrs (書いたままの属性、`doc:name` を含む) で当てる。
  - processor の書き方で接頭辞が無いものは `mule:` とみなす (実 MUnit の verify-call の文言も `On mule:set-payload.`)。
- 実 MUnit で確かめた振る舞い (munit-mocks):
  - then-return の式は、mock-when を実行した時点で評価する (当たった時点ではない)。
  - 当たったプロセッサの payload と attributes は、then-return に無ければ null になる。
  - error は typeId の型で、説明は空。
  - whereValue は式でもよい (評価してから比べる)。
  - verify-call の既定は times 1。文言は `On <proc>. Expected [at least |at most ]N but got M calls` で、ファイルと行は付かない。
  - mock と呼び出しの記録は、テストごとに空にする。
- 接続の失敗の文言の localhost の部分は、`mulay test` では `localhost/[0:0:0:0:0:0:0:1]` にする。
  - 実 Mule の単体は `-Djava.net.preferIPv4Stack=TRUE` で動く。MUnit の組み込みのランタイムはこれが無いので、最後に試した IPv6 の宛先が出る。

## 理由

- matcher を DW の関数として持たせる案は採らない。
  - 実 MunitTools は、matcher にラムダを入れて Java の側で呼ぶ。
  - 決めた時 (2026-10-20) の mulay の DW では、あるスクリプトで作った関数の値を、別にコンパイルしたスクリプトから呼べなかった
    (関数の中の表の番号がずれた)。ADR 108 で呼べるようになった (実 Mule と同じく `rhs: Array` 1 つの関数として) が、matcher はデータのまま。
- Hamcrest の文言は、実 MUnit の記録 (munit-asserts の 73 件) に合わせて書いた。記録の無い組み合わせは推測であり、記録を足して確かめる。
- suite ごとにアプリを読み込み直すのは、実 MUnit と同じく、suite の間で状態を残さないため。
