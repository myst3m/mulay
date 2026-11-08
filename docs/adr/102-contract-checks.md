# ADR 102: 約束の突き合わせと仕様の example (livenote の段階 5)

- 状態: 採用 (2026-10-24)
- 関連: ADR 094 (note の実行)、ADR 097 (AModel)、ADR 098 (アプリ間の呼び出し)、ADR 099 (DB エミュレータ)

## 入力: `@links`

load の予約したパス `@links` (`@properties` と同じ仕組み) に、つながる相手の一覧を JSON で渡す (webide-5c と合意した形)。

```json
[{"name": "customer-sys", "url": "http://customer-sys:8082/api",
  "spec": {"main": "customer.raml", "files": {"customer.raml": "...", "types/order.raml": "..."}}}]
```

- livenote が地図の線から作る。url は今のプロファイルの値で組み立てる。files は相手のアプリの src/main/resources/api の中身。
- spec は main から読み、RAML の include・uses は files から解く (main のディレクトリからの相対)。spec が無い link も書ける (突き合わせはしない)。
- 形が誤っていれば、診断に `links.invalid` の warning を 1 つ出す (load は続ける)。

## 突き合わせの結果: warning の診断

AModel の diagnostics に `"severity": "warning"` で入れ、`code` (決まった名前) と `data` (値の JSON) を付ける。livenote は code で
英語と日本語に訳す。message は英文の原文。実行は止めない (`m/App` の diags には入れない。mulay run・validate・MUnit は変わらない)。

### http:request (`note/contract/http-warnings`)

- アプリの全部の http:request (入れ物の中、error handler の中も) について、URL を静的に組む: `url` 属性か、config の
  request-connection の protocol・host・port と basePath と path。どれかが式なら飛ばす。
- URL が link の url の下にあれば、残りのパスを相手の仕様の resource と区切りごとに比べる (仕様の `{x}` は何にでも合う)。
- `contract.no-operation`: 合う resource にそのメソッドが無い。data は link・spec・method・path (呼ぶ側のパス)。
- `contract.uri-param`: 合ったが、同じ位置の URI パラメーターの名前が違う (呼ぶ側 `{cid}`、仕様 `{id}`)。data に param と expected。
- テストは test/contract。

### SQL (`note/contract/sql-warnings`)

- `@links` に関係なく、`livenote/db/<設定名>.sql` (DB の約束、ADR 099 の seed) がある config の db:select・insert・update・delete
  (bulk も) を調べる。SQL が式 (`#[`) なら飛ばす。
- config ごとに seed で新しいエミュレータを開き (実行中のものとは別、調べ終わったら閉じる)、`db/emu/check` で流す: 方言を
  読み替え、引数は全部 NULL。存在しない表と列だけを拾い、制約の違反などは無視する (調べるための実行で、結果は捨てる)。
- `sql.unknown-table` (data は config・table)、`sql.unknown-column` (config・table・column。table は書いた修飾子で、無ければ "")。
- 方言の決め方は実行と同じ (`conn/db/dialect-of`)。SQLite の config は本物を使うので調べない。

## 仕様の example で答える (`note/contract/answer`、note の `spec-answer`)

- http:request は、記録があれば記録 (今までどおり)、無ければ host の mulay_http。host がつながない ("") とき、URL が
  `@links` の link の下で、仕様にそのメソッドとパスの操作があり、2xx の example があれば、それで答える (2xx の中で一番小さい
  状態コード)。無ければ今までどおり held。`@links` が無ければ動きは変わらない。
- 答えは本物ではないので、ステップの status を `"example"` にし、`example` に出どころを付ける:
  `{"link","spec","method","path" (仕様の resource),"status","mediaType"}`。送った中身 (request) も記録のときと同じく付ける。
- 状態コードと content-type は応答の attributes に入り、http:request の応答の検査 (response-validator) も通る。
- `@links` は load のたびに入れ替える (load-dir-with で空にし、load-dir-full が入れる)。
- テストは test/contract の answers-with-the-spec-example と no-example-stays-held。
