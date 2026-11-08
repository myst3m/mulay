# 004 — 正規表現は java.util.regex.Pattern 互換の部分集合を、明示スタックの後戻り VM と手数の予算で照合する

状態: **採用** (2026-09-28。後戻りの記録の上限と予算の持ち方は 2026-10-04、1a33ba9)

## 決定

- 対象は DataWeave と Mule が使う実用の部分集合。JDK 17 のソースを手本にする。
- 位置 (探す始まり、一致とグループの境目) はすべて**バイトの位置**。`.`、文字クラス、量指定子はコードポイントずつ進む。
  壊れた UTF-8 は U+FFFD として読む (`mulay.lib.uni`)。
- `compile` はパターンを後戻り VM のプログラム (1 命令 4 Int、飛び先は自分の位置からの相対) にする。JDK と同じ leftmost-first
  (POSIX の leftmost-longest ではない)。スタックは明示 (再帰しない)。先読み・後読みと atomic group は sub-VM で走らせ、その深さは
  パターンの入れ子で決まり、入力では決まらない。
- 1 回の検索には手数の予算がある (Pattern の limit、既定 1 億 + 探す入力 1 バイトあたり 64)。超えればエラーの値を返す
  (`(a+)+b` のようなパターンで止まらなくならない)。`with-limit` で変える。find-all、split、置換は全部の検索で 1 つの予算を
  共有する。`search-within` は予算を呼ぶ側が渡し、使った手数を返す。JSON Schema の検証は検証 1 回で 1 つの予算を
  Atom に持ち (`mulay.lib.jsonschema/rx-budget`、`rx-find`)、文字列ごとには 1 バイトあたり 64 だけを足す。超えたら
  合わないとはせず、検証の失敗にする (`not` の中で超えても、検証の結果は失敗)。前は要素ごとに 1 億手から数え直した (2026-11-08)。
- 後戻りの記録は `MAX-STACK` (100 万件) まで。超えればエラーの値。
- パターンの誤りの文言は PatternSyntaxException.getMessage() に合わせる。
- 非対応 (compile がエラーにする): CANON_EQ、`\X`、`\b{g}`、`\N{name}`、`\p{javaMirrored}`。
- 検索の加速に、一致が始まりうるバイトの集合 (`first-set`、256 個の印) を持つ。非 ASCII は保守的に扱い、ASCII の文字そのもの
  (UNICODE_CASE でない) 以外の 1 文字の命令 (クラス、`.`、非 ASCII の文字など) では 0x80 以上のバイトをすべて印にする
  (U+FFFD として読む壊れたバイトは、その文字の UTF-8 の先頭のバイトとは限らないため)。
  一致が空でありうるパターンと、この走査が追わない始まり方 (後方参照、atomic group) は集合を持たず、すべての位置を試す。

## JDK と意図して違う点 (これ以外は test/regex/golden_test.clay で Java 17 と照合する。期待値は tools/gen-regex-golden.java)

- 所有的な繰り返し (と `?+`) のグループで、続きが後で失敗すると、JVM は失敗した試みの内側の捕捉を残す。ここは失敗した道の捕捉を残さない。
- JVM は UTF-16 の単位で進むので、幅 0 の一致や検索の始まりがサロゲート対の間に来うる。ここはすべての位置がコードポイントの境目。
- Unicode の表は `mulay.lib.unitab` のもの (Java 17 の 13.0 より新しい。ADR 005)。
- `\p{javaJavaIdentifier*}` / `\p{javaUnicodeIdentifier*}` は一般カテゴリから近似する。

## JDK をそのまま写した癖 (知っておくべきもの)

- グループは終わりで公開する (グループ 1 の中の `\1` は前の反復の値を見る。JDK の GroupTail)。
- 決定的なグループの空の反復は捨てる (GroupCurly、命令 `CNEXTF`・`RCHKF`)、他のグループでは残す (Loop)。
- 後読みの長さは JDK の TreeInfo と同じ 32 ビットの int の算術: 和は黙って wrap し (`(?<=[^a]+\s*)` は最大が負になり、JVM と同じく
  一致しない)、積が溢れれば長さは不明 (`INV`)。`(?<=\w+.)` はテキストの先頭まで探し、`(?<=a+b+)c` は一致しない。
  JDK の Behind の `from = max(i - rmax, 0)` も int の算術で、負に wrap した最大は i >= rmax + 2^31 で先頭まで戻る。
- `\b` は Character.isLetterOrDigit を使う (Java 17。Java 19 以降の `\w` ではない)。

## 理由

- 予算と記録の上限: 攻撃者の入力で CPU とメモリを使い切らない。予算が照合 1 回ごとだったときは、1 回が O(n) の `a(?=a*$)` を
  find-all すると全体で O(n^2) の手数を使えた。VM のスタックは入力に比例して伸び、1MB の入力の `(a|b)*x` で 300MB を使った
  (1a33ba9)。実 DW は再帰で `(a|b)*` の 1 万回ほどで StackOverflowError になる (利用者から見た違いは docs/compat/deviations.md)。

## 場所

- `mulay.lib.regex/compile`、`run`、`MAX-STACK`、`with-limit`、`first-set`、`MAXR`、`INV`、`mul-mx`
