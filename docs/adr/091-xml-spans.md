# 091 — XML の要素と属性のバイト位置 (lib/xml の XSpan)

状態: **採用** (2026-10-24)

## 背景

ライブ・ノート (WebIDE、別のリポジトリ) では、正はファイルのテキストである。画面は Mule の XML を自分で解釈しない。
mulay が XML を読んでモデルと位置を返し、画面はその位置のテキストだけを書き換えて、もう一度読ませる。
取り決めは livenote の `src/runtime/contract.ts` (`ElementSpans`、`AttrSpans`)。

## 決定

- `XmlOpts` の `spans` が true のときだけ位置を取る。既定は false で、DW の XML 読み込みなど位置の要らない読み込みには
  余計な仕事をさせない。
- 位置は `XLines` (要素ごとの行番号の木) の `span` 欄 (`XSpan`) に置く。`XNode` には足さない。`XNode` は DW、コネクタ、
  SOAP などあらゆる所で作り・比べる値で、位置を持たせるとそのすべてに響く。`XLines` を使うのは Mule の設定を読む所だけ。
  - `open`・`open-end`: 開始タグの `<` から `>` (または `/>`) の後まで。
  - `close`・`close-end`: 終了タグ。自己終了タグなら -1。要素全体は `open` から `close-end` (自己終了なら `open-end`) まで。
  - `attrs` (`XASpan`): 書かれた順のすべての属性 (`xmlns` の宣言も含む)。`name` は書かれたままの修飾名、`raw` は引用符の中の
    エスケープを戻す前のテキスト。`start`・`end` は `name="value"` 全体、`vstart`・`vend` は引用符の中、`quote` は引用符の
    バイト (34 か 39)。DTD の既定値で足された属性は含まない (ファイルに無いので)。
  - 位置を取らないときは、すべて `NO-SPAN` (位置 -1、属性なし) を共有する。
- 位置は **元のファイルの UTF-8 のバイト位置**で、区間は `[start, end)`。
  - reader は UTF-8 の BOM を外し、改行を正規化 (CRLF → LF、単独の CR → LF) したテキストを読む。そこで読んだ位置を
    `to-raw` で元のバイト位置に戻す。外した BOM の 3 バイトと、CRLF で消えた CR の位置 (`crlf-cuts`、正規化後の LF の位置の並び)
    を覚えておき、境界 p の前で消えた CR の数を二分探索で足す。単独の CR は LF に置き換わるだけで長さは変わらない。
  - 境界は「p より前で消えた CR」(`<`) を数える。終わりの位置が CRLF の直前にあるとき、`<=` で数えると CR の後ろを指してしまう。
  - UTF-8・US-ASCII 以外の文字コードで書かれたファイルは、UTF-8 に変換した後の位置になる (元のバイト位置ではない)。
    Mule の設定ファイルは UTF-8 なので、これで困らない。
- 実体参照の置換テキストの中から出た要素の位置は -1 (元のファイルに無い)。reader は置換テキストを読む間 `:en` > 0 になり、
  実体の終わりは次の字句を読む前に戻すので、イベントの時点の `:en` で判定できる。
- reader は最後に読んだタグの始まりを `:tpos` に、開始タグの属性の位置を `:aspans` に置く (位置を取るときだけ)。
  自己終了の要素の終わり (`XeEnd`) は reader がタグを読まずに出すので、`:tpos` が開始タグのままになる。
  build-dom はそれで終了タグの有無を見分ける。
- read-start は `(:adefs r)` を `assoc r` より前に束ねる。`if` で分けた assoc の後で読むと、開始タグごとに reader を写す
  (ADR 001 の「next-event に渡した reader は、その後で読まない」と同じ理由)。

## 場所

- `mulay.lib.xml`: `XmlOpts` の `spans`、`XASpan`、`XSpan`、`XLines`、`no-span`、`NO-SPAN`、`XmlReader` の `tpos`・`aspans`、
  `read-start`、`read-end`、`build-dom`、`crlf-cuts`、`to-raw`、`raw-aspans`
- テスト: `test/xml/xml_spans_test.clay`
