# 053 — 行のストリームは登録表に ID で置き、寿命を要求 (相関 ID) の enter / leave で決める

状態: **採用** (2026-10-03 d40d9d3。所有者の付け替えは 2026-10-03 97ef73e)

## 決定
- 行のストリーム (DB の select の結果。実 Mule の CursorIteratorProvider に当たる。deferred の出力と streamResponse の本文にも使う) は
  `mulay.rt.stream` の登録表に置く。コネクタは `Source` (次の n 行を読む関数と閉じる関数) を `open` で登録して ID を得る。
- 読み方は 2 通りで、混ぜない:
  - `take-vals`: 少しずつ読む (foreach、batch:job)。読んだ行は持たない。
  - `all`: 全部読んで持つ (DW が値として読むとき、境界で書き出すとき)。2 回目からは持っている行を返す。
  - take-vals で読み始めたカーソルを all で読むことはできない (実 Mule は読み直せる。docs/compat/deviations.md)。
- カーソルの状態: FRESH (未読)、STREAM (take-vals で読んでいる)、DONE (all で読み終えた)、SPENT (take-vals で読み終えた)。
- 寿命: 要求の始めに `enter owner`、終わりに `leave owner` (owner は相関 ID)。最後の leave で、その所有者のカーソルのうち
  - 未読で `drain` が true のものは全部読んでから閉じる (DB の接続を返すため)、
  - 読みかけのものと drain でない未読のものは閉じ、
  - すべて登録から消す (all で持っていた行も捨てる)。
- 要求の後も Event を使うもの (async、batch:job、timeout で待たれずに続く parallel の worker) は、
  使い終えるまで所有者に enter しておく。要求より長く読むもの (並行の batch:job、streamResponse の本文の書き手) は
  `adopt` でカーソルを新しい所有者に移す。
- 要求の外へ渡す値 (Object Store、VM のキューなど) は `ev/settle` で読み切った値にしてから渡す。
- 終わった後で使う payload が行のストリームなら、要求の終わりの前に読み切った値にしておく
  (`mulay.rt.engine/run-flow-top`)。HTTP の listener は応答を書き出してから閉じるので、enter と leave を自分で呼ぶ。
- foreach の rootMessage の payload は null にする (値にするとストリームを読み切ってしまう。実 Mule はストリームのまま)。

## 理由
- 大きな結果をメモリに置かずに foreach / batch:job で少しずつ処理するため。
- 読み残したカーソルが DB の接続を握ったままにならないよう、閉じる時点を要求の終わりに揃える。

## 場所
- `mulay.rt.stream`: `Source`、`open`、`take-vals`、`all`、`fresh?`、`enter`、`leave`、`adopt`
- `mulay.rt.event`: `settle`、`realize`
- `mulay.rt.engine`: `run-flow-top`、`run-parallel`、`json-stream`、`items-stream`
- `mulay.app.run`: `piped-resp`
