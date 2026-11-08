# 094 — ライブ・ノートの例の実行 (mulay.note.run)

状態: **採用** (2026-10-24)

## 背景

ライブ・ノート (WebIDE、別のリポジトリ) は、例 (Example: リクエスト・期待・固定の時計・乱数の種) を編集のたびに
実行し、ステップごとのトレース (Trace) を見せる。取り決めは livenote の `src/runtime/contract.ts` の `run`・`getValue`・
`components`。同じ実行を native (`mulay note`、隠しコマンド) と wasm (ADR 095) の両方から使う。

## 決定

- **`mulay.note.run`** を cli と並ぶ一番上の層に置く (conn・app・rt を使う)。状態 (読んだアプリ、記録、値の表) は
  大域の atom に持つ。1 つのインスタンスへの呼び出しは 1 本ずつ (取り決め) なので、それで足りる。
- **コネクタは本物を使わない**。`conn/catalog_gen` の表から登録表を作り、外に出ないもの (`BROWSER`: validation、os、mule-apikit) だけ
  本物、ほかは**再生専用のコネクタ** (`replay`) にする。
  - 記録は `livenote/recordings/<例の id>.json` (取り決めの Recordings)。キーは doc:id、無ければパス。値は呼ばれた順。
    `OpCall` の `loc` (ADR なし、rt/conn) で引き、キーごとの回数で次の記録を取る。
  - APIkit の router (2026-10-24) は本物で、実装フロー (`get:\orders:config` など) に振り分ける。実装フローのステップは
    そのフローのパスでトレースに入る (flow-ref と同じ)。APIKIT:NOT_FOUND などのエラーも本物と同じで、main フローの
    error handler が受ける。`components` の `apikit:router` は、Studio の接頭辞 `apikit` を登録表の `mule-apikit` に読み替える。
  - output があれば、その payload (mediaType が無ければ application/java) と attributes を `ok-result` で返す。target と
    targetValue、エラーの対応づけは engine の run-op がそのまま行う (本物のコネクタと同じ道)。
  - error があれば、その type (`NS:ID`) と description のエラーにする。error handler はふつうに拾う (dbdown の例)。
  - 記録が尽きたら (読み込みも書き込みも) `err/halt` で止める。halt は error handler も until-successful も拾わない
    (rt/engine)。そのステップは held、Trace の `stoppedAt` にそのパス、応答は無し。
  - エラーの親子 (`PARENTS`) と class (`CLASSES`) は表から最初のコネクタに持たせる (`new-ctx` が登録する)。
- **トレース**は engine の hook (rt/engine の `Hook`) で取る。before でステップを積み (入力の payload と vars)、after で
  状態・時間・出力・エラーを書く。並びは始まった順 (前順)。router は route の hook で選んだ番号を持つ。
  - 状態: 再生したら replayed、記録のエラーなら failed、halt なら held、エラーなら failed、ほかは ok。
  - 同じパスが 2 回以上動いたら、そのパスのすべてに `iteration` (0 から) を付ける。
  - 先頭に受け口 (`<flow>/source`、状態 ok) を置き、output にフローが受け取った payload・vars・attributes (HTTP の
    リクエストの attributes) を入れる。docId は AppModel の source から取る (受け口の Loc は要素に入る前の状態で作るので
    doc:id を持たない)。各ステップの input・output にも attributes を入れる。
  - flow-ref で呼んだフロー・sub-flow のステップも入る。path は呼ばれたフローのもの (`sub/processors/0`)。同じ sub-flow を
    2 回呼べば iteration で分かれる。
  - 例のフローのステップのうち動かなかったものを、AppModel の順で not-reached として後ろに足す (呼ばれたフローの分は足さない)。
  - `handler` は、トレースの中で最初に `<flow>/errorHandler/<k>/` で始まるパスの entry。
- **値**は TV のまま表 (`VALUES`) に置き、ID は `<例の id>:<通し番号>`。同じ例をもう一度実行すると、その例の ID だけ消す
  (取り決め: 次の load か同じ例の再実行まで有効)。期限の切れた ID の `get-value` は `{"error": ..}`。文字にするのは JSON にするときと `get-value` のとき。
  application/java・`*/*`・mediaType の無い値は、文字列ならそのまま、ほかは JSON で書く (数を Java の直列化のバイト列にしない)。
  PIPE と CURSOR (流れ) は読まずに "(stream)" とする (読むと消費するため)。preview は空白をまとめて 120 文字で切る。
  JSON に入れる文字列は、UTF-8 として壊れた所を U+FFFD に替える (バイナリの応答でも trace の JSON が正しい UTF-8 になるように)。
- **リクエスト**は Example の request から `app/exchange/request-event` で作る (listener と同じ attributes)。uri の
  パラメータは listener の path の `{name}` で取る。listener の config の basePath は今は見ない。応答は
  `app/exchange/reply` (http:response と http:error-response の評価)。
- **HTTP 以外の受け口** (scheduler など) の例は request を使わない。payload は request の body があればそれ、無ければ null、
  attributes は null。応答は無い (`response` を書かない)。受け口の無いフローも request の body を payload にする。
- **時計と種**は例ごとに `lib/host` に入れ、終わったら外す (ADR 093)。種が無ければ 0。

## 測った時間 (native、orders-api の 4 例、フローの実行だけ)

0.06〜0.09 ms (2026-10-24、`mulay note test/fixtures/livenote/orders-api <id>` の ms)。

## 場所

- `mulay.note.run`: `load-dir`、`run-example`・`run-example-val`、`examples`、`trace-json`、`get-value`、`components-json`、
  `connectors`、`replay`、`before`・`after`・`routed`、`render`
- `mulay.cli.boot/cmd-note` (`mulay note <dir>` は AppModel、`mulay note <dir> <id>...` は Trace を 1 行ずつ)
- `mulay.rt.engine`: `Hook`、`run-hooked`、`chose`、`handle-error` (halt)、`run-until` (halt)。`mulay.rt.error/halt`・`halt?`
- テスト: `test/note/note_test.clay` (orders-api の 4 例と、記録の無い held)。記録は `test/fixtures/livenote/orders-api/livenote/recordings`

## HTTP 以外の受け口の例 (2026-10-24)

- 例に `request` が無いとき、payload は例の直下の `body` と `mediaType`、attributes は直下の `attributes` (JSON の object)。
  `request` があれば今までどおりそこの body と mediaType を使う。
- 受け口ごとの既定の attributes に、例の attributes をキーごとに上書きする (無いキーは後ろに足す)。形と class は本物のコネクタと同じ。
  - `vm:listener`: queueName (listener の値)、correlationId (null)、timestamp。
  - `file:listener`: fileName (既定 example.txt)、lastModifiedTime・lastAccessTime・creationTime、symbolicLink、regularFile、
    directory、path (listener の directory と fileName をつなぐ)、size (body のバイト数)、name。
  - `sftp:listener`: 同じく fileName・path・size と、permissions (420)、timestamp。
  - ほかの受け口は既定を持たず、例の attributes をそのまま (無ければ null)。
- 時刻は例の clock (無ければ今) を UTC で読む (ブラウザにはタイムゾーンが無く、例の結果を毎回同じにするため)。
- sftp のコネクタは wasm に入らない (SSH) ので、既定の形は note に置く (`source-attrs`)。テストは note_test の non-http-attributes、
  fixture は test/fixtures/livenote/sources。

## batch:job を例の中で回す (2026-10-24)

- 本物の Mule と mulay の run は batch:job を後ろで回す (フローは BatchJobInstance を受けてすぐ進む) ので、中のステップは
  例のトレースに入らなかった。note は `Ctx` の `inline-batch` を true にし、`run-batch` はその場で `batch-body` を最後まで
  回してから進む (並列の道や cursor の道も、この時は順に回す道を使う)。フローの次のステップが見る payload
  (BatchJobInstance) は変わらない。
- 中のステップは、そのパス (ADR 092) で、同じパスが何度も動けば iteration で分かれる (レコードごと、aggregator は塊ごと)。
  on-complete には本物と同じ BatchJobResult が渡る。テストは note_test の batch-runs-inside-the-example、fixture は
  test/fixtures/livenote/batch。
- 例の結果に出る順は mulay の batch の順 (塊ごとに step を回す) で、実 Mule の後ろの並び (非同期) とは合わせない。

## ログをトレースに載せる (2026-10-24)

- `rt/log` に受け口 (`set-sink!`・`capture`) を足した。受け口があると `emit` は書き出さず受け口に渡す。note は load で
  受け口を差し、受け取ったログを、そのとき動いているステップ (FRAMES の一番上) の `logs` に、ステップの外 (フローの
  エラーの報告など) なら全体の `logs` に付ける。形は `{"level","category","message","shown"}`。
- note の Ctx のしきい値は INFO (実 Mule の既定)。前は 5 (何も出さない) だった。
- logger のしきい値より低いもの (カテゴリが org.mule 系でなければ WARN 未満、mulay の既定は実 Mule に合わせてある) は、
  実 Mule では出ず、式も評価されない。note では受け口があるときだけ、式を評価して `shown: false` で載せる (例を書く人が
  「Mule では出ない」と分かるように)。評価が失敗しても、フローは止めず `(not evaluated by Mule at this level)` を載せ、
  イベントは評価の前のものを使う (実 Mule と同じく、出ない logger はフローに影響しない)。
- message は実 Mule と同じ文字 (JSON の payload の値は `"…"` のように JSON で出る)。
- テストは note_test の logger-output-goes-into-the-trace、fixture は test/fixtures/livenote/logs。

## エラーハンドラーの中の error (2026-10-24)

- ステップに入るときのイベントにエラーがあれば (on-error の中など)、DataWeave の `error` と同じ値 (`err/to-val`:
  description・detailedDescription・errorType {identifier, namespace, parentErrorType}・errorMessage・cause・childErrors)
  を値の表に置き、トレースの `input.error` に ValueRef で付ける。テストは note_test の error-handler-steps-see-the-error。

## 送った中身と、記録の要求との突き合わせ (2026-10-24)

- コネクタの操作のステップごとに、送った中身 `{payload, <属性の名前>: 値, <子の式の名前>: 値}` (式は評価した値、
  リテラルは文字) を値の表に置き、トレースの `request` に ValueRef で付ける (再生・エミュレータ・アプリ間の呼び出しの
  どの道でも)。livenote は「送った中身」の欄に出し、記録を作るときに `request` として残せる。
- 記録の呼び出しに `request` (同じ形の JSON) があれば、そのキーごとに今の値と比べ (DataWeave の JSON を
  indent 無しで書いた文字で)、違えば `warnings` に「the request differs from the recording: <キー> was .. but now ..」を
  付ける。状態は replayed のまま。記録に無いキーは比べない。
- テストは note_test の replay-compares-what-was-sent (fixture は dbapp の sent-same・sent-diff)。
- 記録の値の文字に `******` があれば、そこは何とでも合うものとして比べる (2026-10-25)。livenote は秘密の値を
  `******` に置き換えて記録を残すので、そのままでは再生のたびに違うと警告していた。`******` で区切った断片が、
  先頭は今の文字の先頭に、最後は末尾に、間の断片は左から順に重ならず現れれば合う (断片を左端から探すだけで決まる)。
  テストは note_test の replay-masked-recording-matches-anything (fixture は dbapp の sent-masked・sent-masked-diff)。

## 入口の無いフローの例 (2026-10-24)

- 例の flow に入口の無いフロー (sub-flow や source の無い flow) を指定すると、応答を作る所で入口を読んで落ちていた
  (wasm では trap、webide-5c が見つけた)。入口が無いときは、HTTP 以外の入口と同じく応答の無いトレースを返す。
  payload は例の body と mediaType (request の中でも直下でも)。テストは note_test の flows-without-a-source-run-without-a-response。

## 送った中身に文字だけの子要素も入れる (2026-10-24)

- ステップの request (と記録の request との突き合わせ) に、`db:sql` のように文字だけを持つ子要素を、要素の名前で入れる
  (同じ名前の式があればそちらを使う)。前は属性と式だけで、SQL の文を変えても記録と突き合わなかった (webide-5c のレビュー)。
  テストは note_test の replay-compares-the-sql-text (fixture dbapp の sent-sql)。
- 記録の request に無い鍵は比べないのは今までどおり。古い記録 (sql の鍵が無い) では SQL の違いは出ない。

## 例のリクエストもリスナーを通す (2026-10-24)

- 前は例の flow を直接動かしていたので、例の method と path がリスナーと合わなくても動いた (GET /nope が 201 で緑になった。
  webide-5c のレビュー、livenote のユーザーが実 Mule に合わせる案を選んだ)。
- HTTP の入口のフローの例は、まず例の flow のリスナーで振り分ける。合えば今までどおり。合わなければアプリの全部のリスナーで
  振り分け、メソッドもパスも合うフローがあれば、実 Mule と同じくそれを動かす。パスだけ合えば 405、どれにも合わなければ 404 で、
  フローは動かさない (ステップは全部 not-reached)。本文は実 Mule の HTTP リスナーと同じ「Method not allowed for endpoint: <生の
  パス>」「No listener for endpoint: <生のパス>」(HTML の escape、HEAD は空)、content-type は text/plain (fixture core-http-response)。
- アプリ間の呼び出し (call) も同じ振り分けと本文を使う。入口の無いフローや HTTP 以外の入口の例は、今までどおり直接動かす。
- テストは note_test の example-requests-go-through-the-listener。

## 動いた error handler の受け口 (2026-10-24)

- try のステップに `handler` (動いた受け口の path、例 `f/processors/0/errorHandler/1`) を付ける。前は受け口の中のステップから
  推していたので、中身の無い受け口 (実 Mule は受け付ける) が動いても分からなかった (webide-5c のレビュー)。
- エンジンの Hook の `handled` が、受け口が合って動き出すときに、その受け口の Loc で呼ばれる。note は path の最後の
  `/errorHandler/` より前を持ち主 (try のステップかフロー) として覚え、持ち主のステップの after で付ける。
- フローの Trace の handler も、ステップから推せないときはこれを使う。テストは note_test の try-steps-name-the-handler-that-ran
  (fixture tryapp)。
