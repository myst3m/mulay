# ADR 083: ObjectStore の店は rt に置き、os コネクタは操作の層にする

日付: 2026-10-20。状態: 決定。ADR 081 (rt はコネクタを知らない) の続き。

## 背景

- `idempotent-message-validator` と Cache スコープ (`ee:cache`) は、ObjectStore に書く。
  - どちらも `objectStore="S"` で `os:object-store` を指せる。
  - 書いた値は、同じアプリの `os:retrieve`・`os:retrieve-all-keys` から見える (実 Mule で確かめた。core-idempotent の `/keys`、core-cache の `/c6keys`)。
- そのため、validator と Cache (rt/engine) と os コネクタは、同じ店を使う必要がある。
- 今まで店の本体 (Store、Entry、掃除、永続化) は conn/os の中にあった。rt は conn を `:require` できない。
- 実 Mule でも、店を管理する ObjectStoreManager はランタイムの部品で、os コネクタはその利用者にすぎない。

## 決定

- 店の本体を `mulay.rt.ostore` に移す。
  - 中身は、店の表 (大域の `ST`)、設定 (`Cfg`。TTL・上限・掃除の間隔・永続するか)、掃除、永続化。
  - 操作は `put!`・`remove!`・`clear!`・`entries`。a2a が使っていた `put-val`・`get-val`・`rm-val` も、ここに移す。
  - 設定の属性 (`entryTtl`・`entryTtlUnit`・`maxEntries`・`expirationInterval`・`expirationIntervalUnit`・`persistent`) の読み方は `cfg-of` に置く。
    - これは ObjectStoreSettings の項目で、`os:object-store` と `os:private-object-store` で同じ。
- conn/os は操作 (store・retrieve・contains・remove・clear・retrieve-all(-keys)) の層にする。
  - `:init` は、アプリの `os:object-store` の設定を `st/init!` に渡す (永続した中身の読み込みも、ここで行う)。
  - `os:object-store` という要素名は rt に持ち込まない。
- validator と Cache の私的な店 (要素の中の `os:private-object-store`、既定の店) は、rt が名前を付けて `ostore` に設定を登録して使う。
