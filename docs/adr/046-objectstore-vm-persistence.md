# 046 — ObjectStore と VM の永続は変わるたびにファイル全体を書き直し、店の期限は触れたときに確かめる

状態: **採用** (2026-09-30、8d15968)

## 決定
- ObjectStore の persistent の店 (既定の店を含む) と、VM の queueType="PERSISTENT" のキューは、メモリに持ったうえで、
  変わるたびにその店 (キュー) の全体を rt/persist のファイルに書き直す。起動のときにファイルから読む。書き込みは 1 つずつ順に
  する (ADR 042 の ticket lock)。
- VM の publish-consume の返事の待ち合わせはファイルに残さない。
- ObjectStore の期限 (entryTtl) と件数の上限 (maxEntries) は、実 Mule と同じく expirationInterval ごとの確かめで消える
  (確かめるまでは残る)。mulay は周期のタイマーを持たず、店に触れたとき (操作のとき) に、前の確かめから周期が過ぎていれば確かめる。
  上限を超えた分は古いものから消す。
- 店の表はプロセスに 1 つ。ほかのコネクタ (A2A のタスクの記録) も `put-val` / `get-val` / `rm-val` で同じ店・期限・ファイルを使う。

## 理由
- 実 Mule でも期限切れと上限を超えた分は確かめるまで残る。確かめる時を操作のときに寄せた形で、実 Mule の記録
  (objectstore-limits 11/11) と合う。周期のタイマーを持たない理由はコメントにも git log にも書かれていない。
- A2A の taskRepositoryObjectStore は実コネクタと同じく os の店を正本にする (os:remove で消せば tasks/get は見つからない)。

## 場所
- `mulay.conn.os/St`、`mulay.conn.os/swept`、`mulay.conn.os/update-store`、`mulay.conn.os/save`、`mulay.conn.os/init`、
  `mulay.conn.os/put-val`、`mulay.conn.os/get-val`、`mulay.conn.os/rm-val`
- `mulay.conn.vm/save`、`mulay.conn.vm/init`
- `mulay.rt.persist`

## 関連
- ADR 057 (永続のファイルの形式と一時ファイル)
