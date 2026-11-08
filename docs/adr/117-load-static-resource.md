# 117 — `http:load-static-resource` と `${app.home}`

状態: **採用** (2026-11-03)

## 決定
- `${app.home}` を組み込みのプロパティにする。値はアプリの資源の根の絶対パス。
  - プロジェクトのディレクトリ: `src/main/resources`。
  - JAR: JAR のパスから `.jar` を外したもの (実 Mule が展開する場所と同じ形)。
  - コマンドラインで渡せばそちらが勝つ。
- 資源の集まり (`res/ResSet`) に置き場 (`home`) とディレクトリの判定 (`res-dir?`) を足す。`App` と `OpCall` が集まり (`rset`) を持つ。
- `http:load-static-resource` は、パスが `${app.home}` の下なら資源から読み、それ以外はファイルシステムから読む。
  - JAR のまま動かす RTF でも、展開せずに画面を配れる。
- 手順は実 Mule の `StaticResourceLoader` のとおり。
  1. listener の path から `/*` を外し、`/` でなければその長さだけ requestPath の頭を外す。
  2. `resourceBasePath` + 残りを `Path.normalize` と同じ規則で畳む。ベースの下に無ければ NOT_FOUND。
  3. ディレクトリなら、残りの末尾に `/` を足し、ベース + 残り + `defaultFile` を開く (畳まない。`..` は OS と同じく、手前がディレクトリのときだけたどる)。
  4. 開けなければ NOT_FOUND。
- Content-Type は拡張子の表で決める。表は次の 3 つを、この順に先に当たったものが勝つ形で合わせたもの。
  - Mule の `mule-extensions-mime-types` の `META-INF/mime.types` (同じ拡張子は後の行が勝つ。zip は application/zip)
  - HTTP コネクタの `META-INF/mime.types` (js、css)
  - activation 1.2.2 の `mimetypes.default`
  拡張子は大文字と小文字を区別する (`UPPER.HTML` は既定の表に `HTML` があるので text/html、`X.CSS` は octet-stream)。
- 出力の DataType には既定の charset (UTF-8) を付ける (実 Mule の操作の出力と同じ)。attributes は null。
- NOT_FOUND のエラーは、errorMessage に listener の応答の属性 (404、"Not Found"、空の headers) を持つ。
  - listener は、エラーの型が HTTP:NOT_FOUND、HTTP:BASIC_AUTHENTICATION、MULE:SECURITY のどれかに当たり、
    errorMessage の attributes が listener の応答の属性なら、その状態コード・reason・headers で返す (`HttpListener.hasCustomResponse`)。
  - `http:error-response` の statusCode が書いてあれば、そちらが勝つ。
  - http:request の HTTP:NOT_FOUND は、属性が要求の応答の属性 (HttpResponseAttributes) なので、今までどおり 500。
- 説明文の path は commons-lang3 の `escapeHtml4` で符号化する (表は 3.20.0 から取った 252 項目)。

## 理由
- HTTP コネクタ 1.11.3 の `StaticResourceLoader`、`ResourceNotFoundException`、`HttpListener` を javap で読んだ。
- 実 Mule 4.11.3 で http-static を記録した (2026-11-03、84 要求)。拡張子ごとの Content-Type、ディレクトリ、`..`、
  `%2e%2e`、listener の path が `/*`・`/a/b/*`・ワイルドカード無し、エラーの捕捉、操作の後の DataType と attributes。
- JAR を展開しない理由は deviations.md (`${app.home}` の行)。

## 場所
- `mulay.conn.http_static`: `run`、`load`、`mime-of`、`escape-html4`、`normalize`、`under?`、`strip-listener`
- `mulay.conn.httpmsg`: `listener-attrs`、`listener-custom`
- `mulay.app.exchange`: `custom-of` (`reply` が使う)
- `mulay.lib.res`: `home`、`with-home`、`abs-home`、`res-dir?`
- `mulay.mule.props`: `props-new` の `app.home`
- `test/fixtures/apps/http-static`、`test/conn/http_static_test.clay`
