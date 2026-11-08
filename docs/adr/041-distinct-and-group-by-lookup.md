# 041 — distinctBy と groupBy は、番号を先に決めてから組み立てる

状態: **採用** (2026-09-28 の記録。初期取り込みからこの形)

## 決定
- distinctBy の等しさは `==` と同じ (`v/equal?`)。探索を速くするため、単純な値 (null、Boolean、Number、String、Key) は
  正規化した文字列 (Number は末尾の 0 を削った 10 進) をキーにした表で引き、それ以外 (Array、Object など) は
  型と大きさごとのバケツの中を順に `v/equal?` で比べる。戻りは残す要素の番号の列 (最初に現れたもの)。
- groupBy は各要素のグループ番号を先に求め、最後にまとめて組み立てる。結果のキーは最初に現れた順。

## 理由
- distinctBy: 探索を速くするため。比べる相手を表とバケツで絞り、等しさの意味は `==` のまま保つ。
- groupBy: 結果のキーを最初に現れた順にし、各グループの中で元の順を保つ。

## 場所
- `mulay.dw.lib.core_coll/bucket-key`、`mulay.dw.lib.core_coll/distinct-idx`
- `mulay.dw.lib.core_coll/group-ids`、`mulay.dw.lib.core_coll/group-members`
