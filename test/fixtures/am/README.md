# Anypoint Monitoring の _metric.log (実 Mule 4.12.0)

実 Mule 4.12.0 (RTF の `poseidon-runtime-4.12.0:10e-java17`、監視のエージェント analytics-metrics-collector-mule4 3.2.16) を
Runtime Fabric (RTF) のクラスタに配備し、Pod の中から `curl localhost:<port>` で要求を送って、`/opt/mule/logs/_metric.log` に書かれた行のうち
`app_inbound_metric` だけを取ったもの (2026-10-14)。1 行が 1 分の窓。`commons` の組織・環境・クラスタの ID とノード・アプリ・Pod の名前は、公開しないために決まった仮の値 (`11111111-…`、`22222222-…`、`33333333-…`、`rtf-worker-1`、`am-probe…`) に置き換えてある。記録し直すときも同じに置き換え、`test/am/am_test.clay` の `C` とそろえる。

| ファイル | アプリ | 送った要求 |
|---|---|---|
| `hello-world.mule-4.12.0.log` | test/fixtures/apps/hello-world | 5 回 `/hello`、その後 7 分間、7 秒ごとに `/hello` 3 回・`/hello/bob` 3 回・`/nope` 1 回 |
| `core-http-response.mule-4.12.0.log` | test/fixtures/apps/core-http-response | 下の 3 回 |
| `am-inbound.mule-4.12.0.log` | test/fixtures/apps/am-inbound | 下の 1 回 |

## core-http-response

窓 1791981540000 (応答の種類):
`/custom`、`/custom?status=201&reason=Made%20It`、`/custom?status=299`、`/custom?status=404`、`/multi-header/array` (500)、
`/body-override`、`/no-content`、`/error-response` (500)、`/error-response?status=503`、`/error-response?status=200`、
`/error-response-default-body` (418)、`/bad-status?s=abc` (500)、`/bad-status?s=99` (500)、`/bad-status?s=600`、`/binary`、
`/methods`、`/wild/a/b/c`、`/wild/42/detail`、`/wild`、`/nope` (404)、`POST /methods`、`PUT /methods` (405)、`HEAD /methods` (405)、
`/custom` に `Host: example.test:9` と `X-Forwarded-For: 10.1.2.3`、`/custom/`。

窓 1791981660000 (区切りの X):
`/wild/{abc123,123abc,0,-5,1.5,0x1f,deadbeef,DEADBEEF00,550e8400-e29b-41d4-a716-446655440000,550e8400e29b41d4a716446655440000,a%20b,%E3%81%82,AbCdEfGhIjKlMnOpQrStUvWxYz012345,2026-10-14}/detail`、
`/wild/x/42`、`/wild/42`、`/wild/42/43`、`/wild/a.b`、`/wild/a/b/c/d/e/f/g/h/i/j/k/l/m/n`、`/wild/QUJDREVGR0hJSktMTU5PUA==/detail`、
`/wild/user@example.com/detail`、`/wild/12345678901234567890/detail`、`/custom//` (404)、`/wild/a;b=1/detail`、`/WILD/a/detail` (404)、
absolute-form の `http://localhost:18120/wild/7/detail`。

窓 1791982020000 (この順。フロー wild の 6 つ目からの組は endpoint が `other`):
`/wild/foo-bar/d1`、`/wild/foo_bar/d2`、`/wild/foo~bar/d3`、`/wild/foo+bar/d4`、`/wild/foo!bar/d5`、`/wild/%C3%A9t%C3%A9/d6`、
`/wild/a%2Fb/d7`、`/wild/%E4%B8%80/d8`、`/wild/%EF%BC%91/d9`、`/wild/a%20/d10`、`/wild/AB/d11`、`/wild/foo's/d12`、
`/wild/%CE%B1%CE%B2/d13`、`/wild/a,b/d14`、`/wild/a:b/d15`、`/wild/%41%42/d16`。

窓 1791982320000 (非 ASCII の文字):
`/wild/{%E4%B8%80,%CE%B1%CE%B2,AB,%EF%BD%81}/detail`、`/wild/%E4%B8%80`、`/wild/Ab`、`/wild/b-c-d`、`/wild/%E3%81%82`。

## am-inbound

窓 1791982860000 (listener-config の basePath="/api/v1"):
`/api/v1/items/42` 2 回、`/api/v1/items/abc`、`/api/v1/ABC/def`、`/api/v1/cont` (on-error-continue)、`/api/v1/fail` (500)、
`/api/v1//x`、`/api/v1/x/`、`/api/v1`、`/api/v1/`、`/api/v2/x` (404)。
