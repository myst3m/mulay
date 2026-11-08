# 101 — アプリの log4j2.xml のログのしきい値に従う

状態: **採用** (2026-10-24)

## 背景

mulay はアプリの log4j2.xml を読まず、いつも実 Mule の既定 (アプリに log4j2.xml が無いとき) のしきい値で、
logger を出すか決めていた (org.mule 系・mulay・com.mulesoft のカテゴリは INFO から、ほかは WARN から)。Studio の雛形の
log4j2.xml は AsyncRoot が INFO なので、実 Mule では `category="orders"` の INFO も出るのに、mulay は出さず、
livenote は「Mule では出ない」(shown:false) と出していた (livenote のレビュー、ユーザーが対応を決めた)。

実 Mule 4.11.3 で確かめた (fixture core-log4j2): Root/AsyncRoot の level、Logger/AsyncLogger の name と level が効き、
子のカテゴリは `.` で区切った一番長い名前の設定を継ぐ (`com.example` → `com.example.child`、`com.examplex` は継がない)。
OFF は何も出さない。AsyncLogger と Logger で違いは無い。

## 決定

- 起動 (CLI の finish、livenote の load) で、アプリの resources の `log4j2-test.xml`、無ければ `log4j2.xml` を読む
  (`rt/log/use-app-config!`)。Loggers の Root/AsyncRoot と Logger/AsyncLogger の level だけを見る (Appender・
  additivity・Filter は見ない)。level が読めない (`${sys:..}` など) 設定は無いものとして親を使う。Root が無ければ ERROR
  (Log4j の既定)。level は ALL・TRACE・DEBUG・INFO・WARN・ERROR・FATAL (ERROR と同じ扱い)・OFF。
- 設定があるときは、カテゴリに一番長く当たる名前の level をしきい値にする。既定の floor (WARN) は使わない。
  CLI のしきい値 (`--log-level` など) が既定の INFO 以外なら、そちらを優先する (利用者が明示した、と見なす)。
- 設定が無いときは今までどおり。livenote の shown もこの判定に従う (ADR 094)。

## 場所

- `mulay.rt.log` (`use-config!`・`use-app-config!`・`threshold`・`enabled?`)、`mulay.cli.boot` の `finish`、`mulay.note.run/load-dir-with`
- テスト: `test/rt/log4j2_test.clay`、`test/note/note_test.clay` (shown-follows-the-apps-log4j2)、fixture core-log4j2 (実 Mule の記録)
