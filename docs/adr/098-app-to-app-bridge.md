# 098 — livenote でアプリ間の http:request をつなぐ (host の関数 mulay_http と export call)

状態: **採用** (2026-10-24)

## 背景

livenote はアプリごとに mulay.wasm のインスタンスを作る (ADR 095)。Workspace の地図で「orders-exp-api が customer-sys-api を
呼ぶ」と線を引いたとき、例の中の http:request を、記録の再生でなく、呼ばれる側のインスタンスで本当に動かしたい
(livenote の設計書の段階 8)。ブラウザの wasm はソケットを持たないので、つなぐのは host (JS) の役目になる。

## 決定

- **呼ぶ側**: note の http コネクタは、`request` の操作で記録が無いとき、リクエストを JSON にして host の関数
  `env.mulay_http(req) -> res` を呼ぶ (`lib/host/http-call`。clay ADR 094 の wasm-import)。
  - req: `{"method","url","path","headers":{名前:値},"body","mediaType","from":{"flowPath","docId"}}`。url・path・ヘッダー・
    本文は本物の http:request と同じ組み方 (`conn/http_req` の `target`・`body-of`・`user-headers`)。認証・proxy・TLS は入れない
    (ブラウザの中のアプリどうしで、外に出ないため)。
  - 本文が UTF-8 でなければ、req は `"body":""` と `"bodyBase64"` で渡し、res も `bodyBase64` があればそれを本文にする
    (JSON の文字列ではバイナリが壊れるため)。
  - res が `""` なら、つながない (今までどおり記録を探し、無ければ held)。どの URL をどのアプリにつなぐか (つなぎ先の表) は
    livenote が決める。
  - res が `{"status","headers","body","mediaType","reason"?}` なら、本物と同じく応答の attributes を作り、状態コードを
    検査する (`status-result`: 既定は 0〜399 が成功、response-validator があればそれ)。404 なら HTTP:NOT_FOUND で、
    description も本物と同じ。`{"error":{"type","description"}}` なら、そのエラーで失敗する (例: HTTP:CONNECTIVITY)。
  - 記録があれば記録が勝つ (例の結果を毎回同じにできるため)。
- **呼ばれる側**: export `call(req)` (`note/call-json`)。`{"method","path"(クエリ込み),"headers","body","mediaType","clock"?}` で、
  AppModel の HTTP の入口 (ADR 097) から path と method の合うものを選び、例と同じに流す。戻りは
  `{"status","headers":{},"body","mediaType","trace":<Trace>}`。trace は呼ばれた側のトレースで、livenote は「呼び出しから」の
  チップに使う。値の ID は `call:..` で、次の run か call まで有効。
  - 合う入口が無ければ 404 `No listener for endpoint: <path>`、path は合うが method が違えば 405
    `Method not allowed for endpoint: <path>` (実 Mule の文)。trace は null。
  - 応答のヘッダー (http:response の headers など) も返す (2026-10-24)。名前は小文字、content-length・transfer-encoding・
    date・connection は除く (呼ぶ側には意味が無いため)。
- **一本ずつの約束**: 呼ぶ側のインスタンスは mulay_http の中で止まっている。host は別のインスタンスの call を呼ぶので、
  ADR 095 の「1 つのインスタンスへの呼び出しは 1 本ずつ」は守られる。同じアプリが自分を呼ぶ (A → A) のは、host が断る
  (`{"error":..}` を返す)。
- **conn/http_req**: リクエストの組み立てと応答の読み替えを、wasm で組めないソケットや待ち時間の部品 (conn/http) から分けた。
  conn/http はこれを使い、ソケットで送る所・認証・proxy・TLS・ストリームだけを持つ。
- native では `host/set-http-bridge!` で関数を差し込める (テスト用)。差し込まなければ "" (つながない)。

- **既定の host (`tools/wasm/host.mjs`、2026-10-24、ユーザーの案)**: wasm の import は省けないので、mulay が既定の host を
  JS で持つ。`instantiate(bytes, {route, http, allowWrites})` が env (clay の出力・trap・時計と `mulay_http`) と Str の
  呼び出しをまとめる。livenote はこれを使えば mulay_http を自分で書かなくてよい。
  - **JSPI** (Chrome): `mulay_http` を `WebAssembly.Suspending` で包み、JS が `fetch` を await する間 wasm を止める。
    mulay_http に届きうる export (`run`・`call`) は `WebAssembly.promising` で包んで呼ぶ (`st.run(name, s)` が Promise を返す)。
    `load`・`get_value`・`components`・`scaffold` は届かないので同期の `st.call`。clay の wasm には手を入れずに動く
    (止まっている間に `clay_alloc` を呼んで答えを書いてよい。1 つのインスタンスへの呼び出しは 1 本ずつの約束 (ADR 095) は保たれる)。
    初めは同期の XMLHttpRequest (Worker だけ) にしたが、メインスレッドで使えず古い使い方なので、JSPI に替えた。
  - 誰に渡すか: `route(req)` が別のインスタンスを返せば、その `run('call')` へ (自分自身なら断る)。返さなければ
    `http(req)` (非同期でよい)、無ければ `fetchHttp`。
  - `fetchHttp` が既定で送るのは GET・HEAD・OPTIONS だけ。POST などは送らず "" (held)。livenote の決まり「書き込みは
    利用者が明示したときだけ」に合わせるため。`allowWrites: true` で送る。本文は `bodyBase64` ならバイト列で送り、
    応答が UTF-8 でなければ `bodyBase64` で返す。CORS で断られたときと繋がらないときは区別できず、どちらも HTTP:CONNECTIVITY。
  - **宛先と Cookie の守り (2026-11-03、脆弱性の点検)**: アプリは他人が作ったもの (Exchange、zip) のこともあり、DW から秘密
    (`${secure::..}`) も読めるので、`fetchHttp` は次のようにする。
    - **既定では何も送らない (2026-11-05、ユーザーの決定)**。送るのは `opts.allow(url)` が true を返す宛先だけ (許可の表にする)。
      公開の宛先も既定では断る。許すと、他人のアプリが `https://攻撃者/?k=秘密` で秘密を外へ出せるため。
      断ったときは HTTP:CONNECTIVITY "is not allowed from the browser"。
    - `allowedUrl(url)` は `opts.allow` に使える決まりで、公開の名前と番地だけを通す (許可の表と組み合わせて使う)。
      http と https だけ。localhost・`*.localhost`・`*.local`・`*.internal`、ループバック、私設 (10/8、172.16/12、192.168/16、
      100.64/10)、リンクローカル (169.254/16。クラウドのメタデータ)、0/8、マルチキャスト、IPv6 の ::1・fc00::/7・fe80::/10・
      IPv4 を埋めたものは通さない。名前は URL の解析で正規化してから
      見る (`2130706433` や `0x7f.1` も 127.0.0.1)。ブラウザでは DNS を引けないので、名前が私設の番地を指すものは防げない。
    - `credentials: 'omit'` (利用者の Cookie や認証を付けない)。応答は `opts.maxBytes` (既定 16 MiB) まで読む。
  - JSPI が無い所 (Node 22) では mulay_http は同期でしか答えられない: route の先の同期の call、同期の `http`、無ければ "" (held)。
  - 試すのは `node tools/wasm/host_test.mjs <wasm>` (JSPI 無しの道と、偽の fetch での fetchHttp) と
    `tools/wasm/chrome_test.sh <wasm>` (headless の Chrome で JSPI の道。許した fetch、404、続けて 2 回、許していない宛先を断る、POST を送らない、別のインスタンス)。

## 場所

- `mulay.lib.host` (`http-call`・`set-http-bridge!`・`clear-http-bridge!`)、`mulay.conn.http_req`、`mulay.note.run` (`bridged`・`call-json`)、
  `mulay.wasm.main/call`
- `tools/wasm/host.mjs` (既定の host)、`tools/wasm/host_test.mjs`、`tools/wasm/chrome_test.sh` と `chrome_test.html`、`tools/wasm/run.mjs <wasm> <アプリ> [<呼ばれるアプリ>]` (host.mjs の route で 2 つのインスタンスをつなぐ)
- テスト: `test/note/note_test.clay` (http-request-goes-through-the-host-bridge・call-runs-the-matching-listener)、
  fixture は test/fixtures/livenote/linked と customer-sys
