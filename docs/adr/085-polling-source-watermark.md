# ADR 085: ポーリングの source の watermark と id は rt/poll で、実 Mule の PollingSourceWrapper と同じ手順で扱う

日付: 2026-10-20。状態: 決定。

## 背景

- `http:polling-source` と `db:listener` は、Mule SDK の PollingSource の上にある。
  - コネクタは 1 回のポーリングで取れた項目を、watermark と id 付きで渡す。
  - 流すか捨てるかは、ランタイムの PollingSourceWrapper (mule-module-extensions-support 4.11.3) が決める。
- 規則は「watermark より新しいものだけ流す」という単純なものではない。
  - http-polling の記録 (実 Mule) では、watermark 30 の後で ts=5 の項目が流れた。
  - watermark 40 と同じ ts=40 で新しい id の項目は、流れなかった。
  - 理由: HttpPollingSource が watermark を文字列にしている。"5" は "30" より大きいので流れ、watermark が "5" になる。
- この規則は、bytecode (PollingSourceWrapper$DefaultPollContext の passesWatermark と saveWatermarkValue、
  PollingSourceWrapper の updateWatermark と updateRecentlyProcessedIds) から読んだ。

## 決定

- `mulay.rt.poll` に、source ごと (`"<flow> <source>"`) の状態を置く。
  - current: 前回までの watermark。
  - updated: このポーリングで上がった watermark。
  - recent: id から、流したときの watermark への表。
  - on-updated: updated と同じ watermark で流した id。
- 項目ごとの判定 (passesWatermark)。
  1. watermark の無い項目は流す (状態は変えない)。
  2. current も updated も無ければ「新しい最高」(ON_NEW_HIGH)。
  3. c = compare(current, 項目)。current が無ければ -1。
     - c < 0 のとき: id が recent にあり、項目の watermark がそのときの値以下なら捨てる。
       そうでなければ cu = compare(updated, 項目) (updated が無ければ -1) で決める。cu = 0 なら ON_HIGH、cu < 0 なら ON_NEW_HIGH、それ以外は PASSED。
     - c = 0 のとき: id があって recent に無ければ PASSED。それ以外は捨てる。
     - c > 0 のとき: 捨てる。
- 流した後に状態を更新する (saveWatermarkValue。switch は下に落ちる)。
  - ON_NEW_HIGH: updated を項目の値にし、on-updated を空にする。
  - ON_NEW_HIGH と ON_HIGH: on-updated に id を足す。
  - すべて: recent に id を入れる。
- ポーリングの終わり (updateWatermark): updated があり、current より大きいとき (current が無いときを含む) だけ更新する。
  - recent を on-updated で置き換え、on-updated を空にし、current を updated にする。
- 比較は DW の `>` と `==` で行う。数値は数値として、文字列は辞書順で比べる。
- http は watermarkExpression と idExpression の結果を文字列にして渡す。db は列の値をそのまま渡す。
- 状態はプロセスの中だけに持つ。実 Mule は ObjectStore に永続し、再起動しても watermark が残る。この違いは deviations.md に書く。

## 理由

- 規則が単純でなく、文字列の watermark では直感に反する結果になる。そのため、実 Mule の手順をそのまま写す。
- http と db で同じ手順を使うので、rt に 1 つだけ置く。どちらのコネクタも rt を使ってよい (層の向きは conn → rt)。
