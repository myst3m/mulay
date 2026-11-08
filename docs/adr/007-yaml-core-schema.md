# 007 — YAML は 1.2 の core schema だけを解釈し、数の綴りとキーの順・重複をそのまま残す

状態: **採用** (2026-09-28)

## 決定

- YAML 1.2 (core schema) の読み手とブロック形式の書き手。clay.core と clay.string 以外に依存しない。
- `YVal` の数は元の綴りを持つ (`YInt`・`YFloat` は text。"0x1F"、".inf"、"-1.5e3")。Int や Float にするのは `int-value`・`float-value`。
- `YMap` はキーの出現順を保ち、重複したキーもそのまま残す (`get-key` は重複時に最後の値)。
- ローカルタグ (`!include` など) は YOpts の `keep-tags` が true のときだけ `YTagged` にする (false ならタグを捨てて値だけ)。
- アンカーとエイリアスは展開後のノード数に上限を置く (`max-alias-nodes`)。`max-aliases` はエイリアスを使える回数 (-1 は無制限)。
  超えれば "Max number of anchor expansion `maxEntityCount=N` has been exceeded" (DataWeave の maxEntityCount)。
- 対応: ブロック・フロー形式の map と seq、明示キー (`? `)、プレーン・単引用・二重引用スカラー (エスケープ全種、複数行の折り返し)、
  `|` `>` ブロックスカラー (chomping と インデント指示)、コメント、アンカーとエイリアス、タグ (`!!str` などの core のタグ。
  それ以外は無視して値を残す)、複数文書、ディレクティブ (`%YAML` `%TAG` は読み飛ばす)、BOM。
- 非対応:
  - YAML 1.1 の型 (yes/no/on/off、0777 の 8 進、60 進、`<<` のマージキー) は解釈しない。
  - 同じ行のプロパティ (`&a !t`) は直後のノードに付く (`- &a k: v` の `&a` はキー k に付く)。
  - タブをインデントに使うことを厳密には拒まない。
- 書き手は文字列を必要なときだけ二重引用符で囲む (`quote-needed?`: プレーンで書くと別の値や構文に読めてしまうもの)。

## 理由

- YAML 1.2 の core schema に従うので、"1_000" は文字列になる (1.1 の型を解釈しない)。
- 解析は再帰下降で、深さは max-depth で抑える (ADR 001)。

## 場所

- `mulay.lib.yaml/YVal`、`YOpts`、`default-opts`、`parse-all-with`、`int-value`、`float-value`、`get-key`、`quote-needed?`、`dump`
