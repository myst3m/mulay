# 049 — コネクタの要素は汎用の形で持ち、名前付けの規則を mule/parse と rt/conn の契約にする

状態: **採用** (2026-09-28。初めの取り込み ce64f08 から。操作の中の経路は 2026-10-03 07fd695、子ごとの経路は 2026-10-10 abf4e90)

## 決定
- コネクタの操作・ソース・大域の設定は、コネクタごとの型を作らず汎用の形で持つ (`m/PrConnectorOp`、`m/SrcConnector`、
  `m/Config`)。属性 (`params`) と子要素 (XML の部分木 `children`) をそのまま持ち、子孫の中の式だけをロード時に
  コンパイルして `exprs` に入れる。コネクタ (src/mulay/conn) は rt/conn の `OpCall` を通してこれを名前で引く。
- 要素の判定は (名前空間 URI, ローカル名) で行う。ローカル名だけで引かない。
- 名前付けの規則 (mule/parse が作り、rt/conn とコネクタが読む):
  - コネクタ名 = 名前空間 URI の最後のパス要素 (`.../mule/http` → `http`)。最後が `core` ならその 1 つ前
    (`.../mule/ee/core` → `ee`、`.../mule/core` → `mule`)。`mulay.mule.parse/ns-name`。
  - Config-kind = `<コネクタ名>:<ローカル名>` (`http:listener-config`、`db:config`)。操作は connector = コネクタ名、op = ローカル名。
  - Param の名前は属性名そのまま。名前空間付きの属性は `prefix:local`。`doc:` の名前空間の属性と要素は捨てる。
  - params は要素自身の属性すべて (config-ref、target、targetValue を含む)。値が `#[...]` なら PExpr。
  - children は `${}` 置換済みの子ノード。コメントと空白だけのテキストは除く。接続要素 (`http:listener-connection` など) もそのまま持つ。
  - exprs のキー: 子孫要素の直下のテキストは要素のローカル名のパス `a/b` (`body`、`headers`)、子孫要素の属性は `a/b@attr`。
    同じ親の下に同じローカル名の兄弟が複数あれば、全部に 0 始まりの番号を付ける (`headers/header[0]@value`)。
    大域の設定も同じ規則 (`request-connection/authentication/basic-authentication@username`)。
- 操作の中にプロセッサ列を持つもの (a2a:send-stream-message の on-task-status-update など) は経路 (`m/Chain`) として別に読み、
  exprs の収集ではとばす (`op-chain-names`)。validation:all / any は子の検査を 1 つずつ経路 "0" "1" .. にする (`op-each-child?`)。
- (2026-10-19、ADR 081) この 2 つと、source として読む要素の名前 (前は gRPC だけ parse に表があった) は、コネクタが
  `Connector` の `:op-chains`・`:each-child`・`:source-elems` に書く。cli が `conn/parse-hints` で (名前空間 URI, ローカル名) の表
  (`m/Hints`) にして `LoadOpts` で parse に渡す。`:source-elems` を書いたコネクタの名前空間は、その表だけで source を見分け、
  書かないコネクタは今まで通り名前で推す (`listener` を含む、`subscriber` で終わる、など)。

## 理由
- コネクタを足すたびに IR とパーサの型を増やさずに済む。コネクタの具体は conn 層に閉じ、rt はコネクタを知らない (層の向き)。
- 式はロード時にコンパイルしておくので、実行時に DW を parse しない (mulet の負債 D)。キーの規則を固定すれば、コネクタは
  式を名前で引ける。

## 場所
- `mulay.mule.parse`: `ns-name`、`attr-params`、`collect-exprs`、`parse-chains`、`parse-child-chains`、`op-chain-names`、`op-each-child?`
- `mulay.mule.model`: `PrConnectorOp`、`SrcConnector`、`Config`、`Chain`、`Hints`、`OpChains`
- `mulay.rt.conn`: `OpCall`、`param`、`find-config`、`attr-val`、`child-tv`、`parse-hints`
