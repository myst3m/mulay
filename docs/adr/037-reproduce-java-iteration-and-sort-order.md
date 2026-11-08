# 037 — 実 DW の結果に出る Java / Scala の内部の順序を、同じ計算で再現する

状態: **採用** (2026-09-28。envVars は 2026-09-30、1acbac1)

## 決定
実 DW の出力の並びや失敗の文言が Java / Scala のハッシュ表や整列の内部の順序で決まる所は、挿入順や辞書順で近似せず、
同じハッシュと同じ手順で順序を計算する。
- text/x-java-properties の reader のフィールドの順: 4 件以下は `java.util.Properties` (ConcurrentHashMap。容量 16 から
  負荷率 0.75 で倍々、同じ位置は挿入順) の走査順、それより多いと Scala 2.12 の immutable.HashMap の走査順 (improve した
  ハッシュの下位 5 ビットずつの辞書順)。ハッシュは `String.hashCode` (UTF-16 単位) を 32 ビットで計算する。
  同じキーは後勝ち (Properties と同じ)。writer は Properties の走査順。
- envVars(): Java の `System.getenv()` (ProcessEnvironment が environ を後ろから `new HashMap<>(件数 + 3)` に入れた反復順) を、
  Scala 2.12 の immutable.HashMap に入れ直した反復順。同じ名前が複数あれば後のものの値。
- application/java の writer: 重複キーは後の値が最初の位置に入る (LinkedHashMap.put)。
- orderBy などの安定な整列は、比較の順序を Java の TimSort と同じにする (32 未満は run の検出と二分挿入、それ以上は
  下から積み上げるマージ。右が真に小さいときだけ右を先に取る)。比べられない値があったとき、実 DW と同じ組の型を
  文言 (`Types `A` and `B` can not be compared.`) に出すため。

## 理由
- これらは実 DW の出力そのもの (golden の期待値) に現れる。近似すると件数やキーによって結果が食い違う。

## 場所
- `mulay.dw.fmt.text/read-properties`、`mulay.dw.fmt.text/chm-order`、`mulay.dw.fmt.text/trie-order`、`mulay.dw.fmt.text/java-hash`、
  `mulay.dw.fmt.text/write-java`
- `mulay.dw.lib.system/env-fields` (`mulay.lib.jhash/hashmap-order-with`、`mulay.lib.jhash/scala-map-order` を使う)
- `mulay.dw.lib.core_coll/sort-by-keys`、`mulay.dw.lib.core_coll/binary-sort`、`mulay.dw.lib.core_coll/merge-sort`

## 注意
- props() のキーの順は再現しない (JVM の全プロパティで決まる。docs/compat/deviations.md)。

## 関連
- ADR 014 (lib/jhash の順序の手順)
