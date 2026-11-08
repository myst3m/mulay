# 100 — 存在しない config-ref と、XSD の列挙の外の値を読み込みのエラーにする

状態: **採用** (2026-10-24)

## 背景

実 Mule は次の 2 つでデプロイを止めるが、mulay は何も言わずに通していた。livenote では記録の再生で動いてしまい、
例が緑のまま通る (レビューで見つかった)。

- config-ref が、どの global の設定にも当たらない。または当たっても、その操作の設定の種類ではない。
- 属性の値が XSD の列挙の外 (logger の `level="DEBUGG"`、大文字小文字も区別する)。

実 Mule 4.11.3 で確かめた文 (2026-10-24、壊したアプリをデプロイした):
- `[a.xml:8]: Referenced component 'Missing_Cfg' must be one of stereotypes [HTTP:REQUEST_CONFIG].` (デプロイ)
- `lineNumber: 8; columnNumber: 41; cvc-enumeration-valid: Value 'DEBUGG' is not facet-valid with respect to enumeration
  '[ERROR, WARN, INFO, DEBUG, TRACE]'. It must be a value from the enumeration.` (mule-maven-plugin の XSD の検証)

## 決定

- **config-ref** (`mule/parse` の `check-config-refs`): 受け口 (listener と、コネクタの受け口) と、すべての中の
  コネクタの操作の config-ref を見る。`${}` や `#[]` を含む値は見ない。
  - 名前の設定が無ければ error。名前はあっても種類が違うときは、期待する種類が確かな所 (HTTP の request と listener)
    だけ error にする (ほかのコネクタは設定の要素名がまちまちで、操作ごとの種類を mulay が持たないため)。
  - stereotype の名前は「コネクタの名前空間の大文字 : 設定の要素名の大文字 (`-` は `_`)」(`HTTP:REQUEST_CONFIG`・
    `DB:CONFIG`)。アプリに同じコネクタの設定があればその要素名、無ければ HTTP は request/listener、salesforce は
    `sfdc-config`、ほかは `config`。名前空間は mule-apikit だけ `APIKIT`。HTTP と DB 以外は実 Mule の綴りと違うことがある。
- **列挙**: logger の level と、fixed-frequency の timeUnit だけを見る (XSD 全体は持たない)。`${}` は見ない。
  文は実 Mule の cvc-enumeration-valid の 1 行目 (2 行目の cvc-attribute.3 は出さない)。前は timeUnit を
  `<fixed-frequency>: unknown timeUnit` と言っていた。小文字の `warn` も実 Mule と同じくエラーにする (前は通していた)。
- 診断は Diag (error) なので、validate・run の起動・livenote の load の diagnostics に出る。fixture のアプリ 108 本と
  mulet のサンプルでは新しい診断は 0 件だった。

## 場所

- `mulay.mule.parse` (`check-config-refs`・`ref-diag`・`stereo`・`enum-check`・`LOG-LEVELS`・`TIME-UNITS`)
- テスト: `test/mparse/parse_test.clay` (config-ref-to-missing-config・enum-attribute-out-of-range)。単体テストの小さな XML には、
  使う設定 (L・R・D・F) を後ろに足した (`CFGS`)。

## 空の入れ物 (2026-10-24)

実 Mule 4.11.3 は、処理を 1 つも持たない入れ物を mule-maven-plugin の XSD の検査で拒む (アプリが作れない)。壊したアプリを
デプロイして確かめた文をそのまま出す (`mule/parse/empty-check`)。入れ物の中身を読む `parse-procs` で、処理が 0 個のときだけ
その入れ物を調べる。診断の path は入れ物の path (when なら `f/processors/1/route/0`、sub-flow なら `s`。livenote が箱に出すため)。

- when・otherwise・try・foreach・until-successful・async・parallel-foreach:
  `cvc-complex-type.2.4.b: The content of element 'X' is not complete. One of '{core:annotations, core:abstract-message-processor, core:abstract-mixed-content-message-processor}' is expected.`
- route (scatter-gather・first-successful・round-robin) と sub-flow: 同じ文で、集合に `core:description` が加わる。
- flow (受け口も処理も無い): 集合に `core:description` と `core:abstract-message-source` が加わる。受け口だけの flow は通る。
- try の中が error-handler だけ: `cvc-complex-type.2.4.a: Invalid content was found starting with element '{core:error-handler}'. ..`
  (行は error-handler の行)。flow の中が error-handler だけの場合は確かめていないので、何も出さない。
- 中身の無い on-error-continue・on-error-propagate は受け付ける (応答も普通に返る)。
- 自己終了の形 (`<when .../>`) も中が空なので同じ。doc: の要素、description、annotations は中身に数えない。
- 134 の fixture アプリ (mulet のサンプルと livenote・MUnit を含む) で、誤って止めたものは 0。テストは mparse の empty-scopes-are-incomplete と empty-scope-diags-carry-the-path。

## 存在しないエラーの種類 (2026-10-24)

実 Mule 4.11.3 は、on-error-continue・on-error-propagate の type に無い種類があると、アプリを作る段階で
`[a.xml:10]: Could not find error 'APP:NEVER'` と言って止める (行は on-error の行、書いたままの名前。`NOPE` のように
名前空間の無いものも同じ)。壊したアプリで確かめた (`APP:NEVER`・`HTTP:NOPE`・`MULE:NOPE`・`NOPE`)。

mulay が判断できる範囲だけを検査する (`mule/parse/type-diags`)。誤って止めないことを優先する。
- `MULE:` と名前空間の無いもの: コアの表 (`mule/errtypes/CORE-PARENTS`) に無ければ誤り。`ANY` は通す。
- アプリが自分で作る名前空間: どこかの raise-error の type か error-mapping の targetType で定義されていなければ誤り。
- コネクタの名前空間 (アプリの xmlns の接頭辞と URI の最後の段 (`mule-` を除く)、それと `EXTENSION-NSS` の表): 判断しない。
  mulay はコネクタのエラーの種類を全部は持っていない (親のある物だけ) ため。`HTTP:NOPE` は実 Mule では止まるが、mulay は通す
  (残りの課題: コネクタの jar からエラーの種類の表を作る)。
- 134 の fixture アプリと Exchange の例 18 個で、誤検出は 0。テストは mparse の unknown-error-types。

## db:config の無い接続の要素 (2026-10-24)

DB コネクタ (1.16.4) の接続は generic・derby・oracle・my-sql・mssql・data-source の 6 つだけ。`<db:postgres-connection>` などを
書くと、実 Mule は XSD の検査で `cvc-complex-type.2.4.a: Invalid content was found starting with element
'{"http://www.mulesoft.org/schema/mule/db":postgres-connection}'. One of '{core:annotations, core:abstractConnectionProvider,
core:expiration-policy}' is expected.` と言って止める (壊したアプリで確かめた。行はその要素の行)。mulay も同じ文で診断する
(`mule/parse/check-db-connection`、db の名前空間で `-connection` で終わる子だけ)。PostgreSQL は generic-connection に
`jdbc:postgresql:` の URL で書く。mulet から移したサンプル db-test-postgres と livenote の見本 orders-api がこの要素を
使っていたので、generic-connection に直した。テストは mparse の db-config-unknown-connection。
