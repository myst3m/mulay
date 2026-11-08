# 074 — http:listener は要求の対象を実 Mule 4.11.3 の Netty の HTTP サービスと同じく扱う

状態: **採用** (2026-10-17)

## 決定
- 404 `No listener for endpoint: <パス>` と 405 `Method not allowed for endpoint: <パス>` の文言には、受け取ったままのパス
  (クエリを除く) を出す。経路はデコードしたパスで選ぶ。
- 文言のパスは commons-text の `escapeHtml4` でエスケープする。要求の対象の各バイトを ISO-8859-1 の 1 文字として読む:
  - `"` `&` `<` `>` は `&quot;` `&amp;` `&lt;` `&gt;`。
  - 0xA0〜0xFF は名前の付いた実体参照 (`&nbsp;` 〜 `&yuml;`)。
  - 0x80〜0x9F はその文字の UTF-8 (2 バイト)。
  - ほかの ASCII はそのまま。
  - 部品は `mulay.lib.html/escape-html4-latin1`。
- mulay の運用の端点 (`/__/`) の 404 も同じ文言にする。
- 要求の対象を `java.net.URI` と同じ規則で調べ、読めなければ 400 `HTTP request parsing failed with error: "<文言>"` を返して
  接続を閉じる (Content-Type なし)。
  - 調べる文字列は `http://<listener の IP>:<port>` と対象をつないだもの。対象が `http` で始まれば (absolute-form) 対象だけ。
    IP は listener の host で、`localhost` は `127.0.0.1`。https の listener でも `http://` で始める。
  - 文言は `URISyntaxException.getMessage()` と同じ `<理由> at index <位置>: <文字列>`。位置はバイトの位置
    (1 バイト 1 文字なので Java の文字の位置と同じ)。文字列の 0x80 以上のバイトは、その文字の UTF-8 にする。
  - 理由は `Malformed escape pair` (`%` の後が 16 進 2 桁でない)、`Illegal character in path` / `query` / `fragment` /
    `authority` / `scheme name` / `opaque part`、`Expected authority`、`Expected scheme name`、`Expected scheme-specific part`。
  - 部品は `mulay.lib.juri` (`check`、`message`)。

## 理由
- 実 Mule 4.11.3 の HTTP サービスは Netty の実装 (`mule-netty-http-service-0.4.3.jar`) で動いている。
  - `NettyHttpMessage.parseUri` が `http://<listener の IP>:<port>` と要求の対象をつないで `java.net.URI` にし、
    `getRawPath()` をパスにする。
  - 404 と 405 の応答は `ErrorRequestHandler.getResolvedEntity` が
    `String.format(<文言>, StringEscapeUtils.escapeHtml4(request.getPath()))` で作る
    (`mule-service-http-1.13.3.jar`、javap で読んだ)。
- Netty は要求行のバイトを 1 バイト 1 文字 (ISO-8859-1) で読む。実 Mule に生のソケットで送って確かめた (2026-10-17)。
  - `/nope/` の後に `C3 A9` (é の UTF-8) を送ると、文言は `/nope/&Atilde;&copy;` になった。
  - `A1` を送ると `&iexcl;` になった。
- 400 は `ForwardingToListenerHandler` が `URISyntaxException` を受けて `handleMalformedUri` で返す (javap で読んだ)。
  `NettyHttpRequestAdapter.getBaseProtocol` は `http` を返すだけなので、https の listener でも `http://` で始まる。
  実 Mule で、壊れた `%`、パス・クエリ・フラグメントに使えない文字、host が localhost の listener、https の listener を記録した。
- `java.net.URI.Parser` の規則:
  - パスに使える文字は英数字、`-_.!~*'()`、`:@&=+$,;/`、クエリとフラグメントはそれに `?[]` を足したもの。
  - `%` の後は 16 進 2 桁。0xA1 以上のバイト (ISO-8859-1 で空白でも制御文字でもない文字) はそのまま使える。
  - authority は、使える文字 (registry の名前の文字) だけなら、server の形として読めなくても registry の名前として通る。
    使えない文字があれば、位置は authority の先頭になる。
  - JDK のソースは手元に無いので、本物の Java 17 の `java.net.URI` に書かせた 1,095 件の期待値 (手で選んだものと乱数で作った
    オリジン形式・absolute-form) で確かめた (test/web、`tools/gen-juri-golden.java`)。
- テストで守っているもの:
  - `java.net.URI` の文言 (test/web の 1,095 件)。
  - 400 の要求 (core-http-response、https-test のシナリオ)。
  - 256 バイト全部と組み合わせの escapeHtml4 (test/web。期待値は `tools/gen-html-golden.java` で commons-text 1.14.0 に書かせた)。
  - 受け取ったままのパスと `&amp;` (core-http-response のシナリオ)。
- テストで守っていないもの: 0x80 以上のバイトを送る要求。シナリオの送り手 (Python の http.client) は非 ASCII の対象を送れないので、
  上の生のソケットでだけ確かめた。

## 残した差
- 400 の応答に clay.http のサーバが Content-Length を付ける。実 Mule は付けずに、接続を閉じて本文を区切る。
- absolute-form の対象の authority に IPv6 の角括弧 (`[` `]`) があれば調べない (clay.http のサーバが先に受けたもの)。
  `java.net.URI` は IPv6 の形を調べて `Malformed IPv6 address` などで断る。

## 場所
- `mulay.app.run`: `handle`、`target-error`、`listener-ip`、`handle-app`、`admin-resp`
- `mulay.lib.html`: `escape-html4-latin1`
- `mulay.lib.juri`: `check`、`message`
