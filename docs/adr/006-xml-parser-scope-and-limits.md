# 006 — XML は整形式を確かめる pull パーサの上に DOM と書き手を置き、外部の資源は引かず、展開と属性の数に上限を置く

状態: **採用** (2026-09-28。属性の上限と重複の検査は 2026-10-04、777429f)

## 決定

- XML 1.0 (Fifth Edition) と Namespaces in XML 1.0 の整形式を確かめる pull パーサ (`reader`・`next-token`。`next-event` はその上で出来事を組む包み。ADR 105 第 7 段) の上に、DOM を組む
  `parse` と、ストリーミングの書き手 (`writer`) を置く。clay.core と clay.string 以外に依存しない。
- 入力は BOM と encoding 宣言で UTF-8 に変換してから読む (`decode-to-utf8`)。
- 意図して対応しないもの:
  - 外部 DTD サブセットは読まない。外部実体は XmlOpts の `ext` で引けた内容の中の参照だけ展開する。既定の `no-ext` は何も引かない
    (XXE に安全)。それ以外の外部実体への参照は、内容でも属性値でもエラー (Woodstox と同じ)。
  - パラメータ実体は宣言を読み飛ばすだけで展開しない。DTD による妥当性の検証はしない。内部サブセットの ATTLIST は解釈する
    (既定値の補完、CDATA でない属性の空白の圧縮)。内部サブセットの中のコメントと PI はイベントにしない。
  - 名前文字の判定は、ASCII は仕様どおり、0x80 以上のバイトは名前文字として受ける。
  - XML 1.1 は 1.0 として読む。
- `dtd` が false なら内部サブセットの宣言 (ENTITY、ATTLIST) は構文だけ確かめて読み飛ばす。実体参照は宣言の無いものとして失敗し、
  属性の既定値は付けない (DataWeave の supportDtd=false)。
- `max-expansions` は文書全体の実体の展開の回数で、ATTLIST の既定値の中の参照も数える。`parse-attlist` は宣言ごとに数え直さず、
  文書全体の回数に足す。上限を超えたときの文言は Woodstox と同じ。
- `max-attrs` は 1 つの要素の属性の数の上限 (-1 は無制限)。DataWeave の reader は Woodstox の既定と同じ 1000
  ("Attribute limit (1000) exceeded")。
- 属性の重複 (生の名前と、名前空間込みの衝突) は名前の表で引く (`process-start`)。
- 書き手: QName の uri が今の束縛と違えば xmlns の宣言を自動で付ける。属性の uri に接頭辞が無ければ見えている接頭辞を探し、
  無ければ ns0、ns1 .. を作る。1 バイトの符号化で書けない文字は文字参照にする。

## 理由

- 外部の資源を引かないのは XXE を避けるため。展開の回数を文書全体で数えるのは、宣言ごとに数え直すと宣言を並べて上限を越えられるため。
- 属性の重複の検査は属性の数の 2 乗だったので、10 万属性の要素 1 つに 35 秒かかった (777429f)。
- DOM を明示のスタックで組む理由は ADR 001。

## 場所

- `mulay.lib.xml/XmlOpts`、`default-opts`、`no-ext`、`reader`、`next-token`、`next-event`、`decode-to-utf8`、`parse-attlist`、`process-start`、
  `build-dom`、`writer`
