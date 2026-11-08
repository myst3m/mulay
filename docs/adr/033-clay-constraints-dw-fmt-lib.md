# 033 — Clay の制約を避ける書き方 (dw/fmt・dw/lib)

状態: **採用** (2026-09-28 の初期取り込みから 2026-10-11 まで。項目ごとに導入コミットを書く)

## 決定

dw/fmt と dw/lib では、次の書き方を崩さない。見た目は回りくどいが、どれも Clay の性能・スタック・確保・起動の
性質を避けるためのもので、素直な形に「単純化」すると不具合 (2 乗の時間、スタックの溢れ、プロセスごとの abort) が戻る。

### 文字列はアキュムレータを引数で回して `(str out ..)` で積む
- Clay は先頭の引数が変数の `str` をその場追記にする。writer は出力の文字列を引数 `out` で受け、積んだものを戻り値で返す。
- エスケープの要らない連は 1 文字ずつ積まず、連の終わりで 1 回の `subs` にしてまとめて積む。
- 場所: `mulay.dw.fmt.json/escape-into`、`mulay.dw.fmt.json/pad`、`mulay.dw.fmt.xml/pad` (2026-09-28)。
- 積んだ後の枝 (失敗の枝も) で、積む前のアキュムレータを読まない。読むと、Clay は毎周アキュムレータをまるごと写す (`clay build --copies` が警告する)。
  - `mulay.dw.fmt.text/write-urlencoded` は、値を文字列にできないときに `""` を返す (呼び手は失敗のとき出力を捨てる)。
    前は積む前の `o` を返していて、配列の値 8 万個の出力に 0.45 秒かかった。直した後は 0.019 秒 (2026-10-23)。

### 出力の文字列をレコードに入れない
- XML writer の状態 `W` は出力の文字列を持たない。出力は各関数の引数 `out` で受け渡し、戻り値で返す。
  `out` を関数に渡した後は、返ってきた文字列だけを使う。
- レコードの中の文字列に追記すると、そのたびに出力全体が複製され、O(要素数 × 出力の大きさ) になった。
- 場所: `mulay.dw.fmt.xml/W`、`mulay.dw.fmt.xml/write-field`、`mulay.dw.fmt.xml/write-elem`、
  `mulay.dw.fmt.xml/write-content` (db6a797、2026-10-04)。

### 本文の残りを複製して探さない
- multipart の境界と空行は、`subs` で残りを切り出さずに、位置 `from` からの探索 (`str/index-of-after`) と
  位置を指定した前方一致で探す。部分ごとに残りを複製すると本文の大きさの 2 乗になる (1MB の本文に 8 秒かかった)。
- 場所: `mulay.dw.fmt.multipart/index-from`、`mulay.dw.fmt.multipart/starts-at?` (ae050ac、2026-10-04)。
- 部分の頭の終わり (空行) は、まず次の境界までで探す。本文の終わりまで探すと、CRLF の本文には "\n\n" が無いので
  部分ごとに本文の終わりまで探して 2 乗になる (4.5MB・8 万部分で 12.6 秒、直して 69 ms)。次の境界までに無ければ
  その先を探す (実 DW と同じく、後ろの部分の空行までを頭として読む)。その先で見つけた空行までは今の部分になり、同じ所を何度も探さないので、全体は線形。
  場所: `mulay.dw.fmt.multipart/header-end`、`mulay.dw.fmt.multipart/blank-line` (2026-11-08)。

### 再帰の深さを入力に任せない
- JSON reader は入れ子の深さを 2000 までにする (`"Maximum nesting depth exceeded"`)。C のスタックを使い切らないため。
  場所: `mulay.dw.fmt.json/MAX-DEPTH`、`mulay.dw.fmt.json/read-val` (2026-09-28)。
- application/dw reader の `x as A as B ..` は左に伸びる木で、構文解析は演算子の連鎖をループで読むので深さに数えない。
  1 段ごとに再帰すると長い連鎖でスタックが溢れてプロセスごと落ちたので、型を外側から集めてから内側の値に順に当てる。
  場所: `mulay.dw.fmt.dwread/as-chain` (c210b47、2026-10-04)。
- 字句解析で文字列の終わりを探すとき、補間 `$( .. )` の中の文字列・括弧の入れ子は明示のスタック (Vec) で数える
  (`mulay.dw.lex/skip-nested`)。前は skip-string と skip-balanced が互いに再帰し、構文解析の深さの上限 (400) より先に
  字句解析が入れ子を最後までたどるので、`"$(` を 20 万回重ねた 600KB の入力 (application/dw の要求の本文) でプロセスごと落ちた (2026-11-08)。
  残る問題: 構文解析の段ごとに、その段の文字列の終わりを最初から探し直すので、補間の入れ子が深い入力は大きさ × 段数 (400 まで) の
  時間がかかる (1MB で 2.8 秒)。終わりを覚えておく表を構文解析の状態に持てば線形になる。

### 確保の失敗はプロセスごと終わるので、入力で大きさが決まる確保に上限を置く
利用者から見える違いは docs/compat/deviations.md にある。ここではコードの側で崩してはいけない点を残す。
- repeat / leftPad / rightPad の結果は 128MB まで。掛け算を溢れさせずに上限を検査する (`n <= MAX / 文字列の長さ`)。
  場所: `mulay.dw.lib.strings/MAX-STR-BYTES`、`mulay.dw.lib.strings/rep-ok?` (6c374d0、2026-10-04)。
- 入れ子の multipart は 100 段まで。段ごとに中身を複製するので、深い入れ子はメモリを段数 × 大きさだけ使う
  (1MB の本文の 1 万 6 千段で 5.5GB を使った)。場所: `mulay.dw.fmt.multipart/MAX-NEST`、`mulay.dw.fmt.multipart/read-at` (fe74704、2026-10-04)。
- readUrl は中身を全部読むので、通常のファイルでないもの (/dev/zero、FIFO) は開かない (止まるか、メモリを使い切って
  プロセスごと落ちた)。場所: `mulay.dw.lib.core_io/read-regular` (27535ba、2026-10-04)。
- 指数の大きい数 (1e999999999) を整数にする・桁を展開する演算は、展開する前に失敗にするか、展開せずに答えを出す。
  - `BigDecimal.intValue` は scale <= -32 なら 10^-scale が 2^32 の倍数なので 0 を返し、展開しない。
    場所: `mulay.dw.lib.math/int-value`。
  - ceil / floor / round と、duration の小数の繰り下げは、桁を展開しすぎる場合に実 DW と同じ文言で失敗する。
    場所: `mulay.dw.lib.core_num/to-int-mode`、`mulay.dw.lib.periods/duration-of` (60e2c6e・5f9fd98、2026-10-04)。

### C の文字列に NUL を渡さない
- NUL を含む URL は読まない。C の open に渡すと NUL で切れて別のファイルを読む (Java は開けない)。
  場所: `mulay.dw.lib.core_io/load-url` (1e214f8、2026-10-04)。

### 64 ビットの Int を wrap させない
- Clay の Int は 64 ビットで、溢れると wrap する。Number を Int にする所は桁数で先に判定し、収まらなければ飽和させる。
  - 添字: 範囲外は ±(2^63 - 1) に飽和。場所: `mulay.dw.lib.core_coll/trunc-int`。
  - Strings の回数・位置: Int に収まらなければ ±2^62 に丸める。差が展開しすぎて失敗する
    ほど離れていれば、差の符号の向きに ±2^62。場所: `mulay.dw.lib.strings/trunc`、`mulay.dw.lib.strings/sub-clamp`。
  - 集計の和は両辺が Int で溢れないときだけ Int のまま足し、溢れるなら Num で計算する (`bi/add-ov?`)。
    場所: `mulay.dw.lib.core_coll/num-add`。
  - Java の 32 ビットのハッシュは毎回 32 ビットに丸めて計算する。場所: `mulay.dw.fmt.text/java-hash`、
    `mulay.dw.fmt.text/i32`、`mulay.dw.fmt.text/u32`。

### 要素ごとに確保しない
- 集計の合成 (sum(xs map f) など) の状態は、呼ぶ側のループの変数 (受けた数 n と acc) に持ち、要素ごとに確保しない。
  数どうしの足し算は invoke を通らずに直接する。場所: `mulay.dw.lib.core_coll/fold-add`、`mulay.dw.lib.core_coll/fold-run`
  (957ac03、2026-10-04)。

### 起動で払う計算を def に置かない
- Clay 0.80.0 から def は main の前に計算される。pluralize / singularize の規則のコンパイルは `delay` に包み、
  初めて使うときに 1 回だけ作る (clay 0.81.0)。使わないプログラム (mulay version など) の起動で払わない
  (起動の命令 1,660 万 → 800 万)。場所: `mulay.dw.lib.strings/PLURALS`、`mulay.dw.lib.strings/SINGULARS` (8c3ea2f、2026-10-11)。

## 理由
- 上の各項の不具合は実際に起きたもの (導入コミットの説明にある)。コメントを消した後も、次に読む人がこれを
  「冗長な書き方」と見て直さないように残す。

## 注意
- 新しい writer を足すときも、出力は `out` を回す形で書く。
- 入力の大きさで深さや大きさが決まる処理を足すときは、上限を置くか、ループで書く。
