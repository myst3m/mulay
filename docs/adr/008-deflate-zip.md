# 008 — DEFLATE・gzip・ZIP は純 Clay で書き、展開に上限を置き、書き出しは固定 Huffman と固定の時刻にする

状態: **採用** (2026-09-28)

## 決定

- `mulay.lib.inflate`: DEFLATE (RFC 1951) の展開と圧縮、gzip (RFC 1952)、CRC-32。clay.core 以外に依存しない。バイト列は Str。
  - 展開: stored / fixed / dynamic Huffman のブロック。ビットの読み取りは (pos bitbuf bitcnt) をループの変数で持ち回る。
    Huffman の復号は 2^maxlen 個の表を 1 回引く (表の値 = 記号 × 16 + 符号長)。長さと距離の組が丸ごと入るよう 48 ビット以上を
    貯めておく。後方参照は 1 バイトずつ写す。
  - `inflate-limit`: 出力が max-out バイトを超えたらエラー (zip bomb の対策)。
  - 圧縮 (`deflate`): ハッシュ連鎖の貪欲な LZ77 と固定 Huffman の 1 ブロック。縮まない入力は stored。
  - `gunzip` は 1 メンバを読み、CRC とサイズを確かめる。
- `mulay.lib.zip`: メモリ上の ZIP / JAR。中央ディレクトリを読み (ZIP64 を含む)、エントリを取り出して CRC-32 を確かめ、書き出す。
  - `read-entry-limit` は展開後 max バイトを超えたらエラー。
  - 書き出し (`write`) の圧縮は固定 Huffman の deflate (縮まなければ stored)。時刻は 1980-01-01 00:00 に固定する。
    65535 エントリか 4 GiB を超えれば ZIP64 の EOCD を書く。
  - 非対応: 暗号化したエントリ (エラーを返す)、deflate 以外の圧縮 (bzip2 など)、分割したアーカイブ。

## 理由

- 時刻を固定するのは、同じ入力から同じバイト列を作る (再現できる出力) ため。
- 展開の上限は zip bomb の対策。
- 出力の積み方と assoc の前に読む書き方は ADR 001。

## 場所

- `mulay.lib.inflate/inflate`、`inflate-limit`、`inflate-codes`、`build-table`、`deflate`、`deflate-fixed`、`gunzip`、`gzip`、`crc32`
- `mulay.lib.zip/entries`、`read-entry`、`read-entry-limit`、`write`、`DOS-DATE`
