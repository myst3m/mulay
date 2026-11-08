# 003 — 10 進数は Java の BigDecimal と同じ unscaled × 10^-scale で持ち、scale と丸めの規則も Java に合わせる

状態: **採用** (2026-09-28。持ち方を Int と BigInt の 2 通りにしたのは 2026-11-07)

## 決定

- `Dec` = unscaled (`clay.bigint` の BigInt) × 10^-scale。Java の BigDecimal と同じく scale は負もあり得る。
  1.50 と 1.5 は別の値 (scale が違う) で、数としての比較は `cmp` / `eq-numeric?`、表現ごとの比較は `equals?` で行う。
- 値は 2 語で持つ (`Dec` = `w` (Int)、`big` (Vec(BigInt)))。clay.decimal の形 (clay の実験 338) と同じ詰め方。
  - 小さい形: unscaled が -2^57..2^57-1 で scale が -31..31 なら、`w` = unscaled × 64 + (scale + 31)、`big` は `[]` のリテラル。
  - 大きい形: それ以外。`w` = scale × 64 + 63、`big` は unscaled の BigInt を 1 つ。scale は Java の int の範囲まで入る。
  - `w` の下の 6 ビットが 63 なら大きい形。小さいかどうかはメモリを読まずに分かる。
  - 値ごとに形は 1 つ (`mks` と `mkb` だけが作り、収まる値はいつも小さい形)。大きい形の BigInt は 0 や Int に収まる値も
    ありうる (scale が ±31 の外)。そのため `equals?` は形が違えば別の値と言ってよい。`is-zero?` は大きい形も見る。
  - 外から読むのは `scale`、`unscaled` (BigInt)、`unscaled-long`、作るのは `of` と `of-long`。
  - 同じ scale の小さい値どうしは、`w` のまま足し引きし (`w_a ± (w_b - 下の 6 ビット)`、64 ビットであふれるのは結果が
    ±2^57 を出る時とちょうど同じ)、`w` のまま比べる。
  - 大きい数の道 (`mk-big`、`addsub-big`、`cmp-big`、`upscale-big`、`unscaled-long-big`) は `^:cold` にし、速い道の関数を
    小さく保つ。
  - Int で計算する道: 加減算 (scale をそろえる 10^k は 18 桁まで)、乗算、比較、`set-scale` と `round-mc` の桁落とし (18 桁まで)、
    末尾の 0 を削る、`integer?`、`to-int-exact`、`parse` (`parse-plain`: `[+-]数字[.数字]` で 18 桁までを 1 回の走査で積む)、
    文字列化 (`plain-small`: scale 1..18 を整数部と小数部に分けて 1 回の連結で書く)、`div-exact` (割る数の 2 と 5 を Int で外す)、
    `div-mc` (割る数が 10^9 未満で精度が 34 桁まで。商を 10^9 ごとの 4 つの Int で求め、最後に BigInt にする)。
  - あふれは `prim/checked-add`・`checked-sub`・`checked-mul` で調べ、あふれたら BigInt の道でやり直す。Long.MIN_VALUE の符号を
    反転する所 (`neg`、`div-exact` の負の除数) もあふれとして扱う。
  - `mkb` は 20 桁以上の BigInt を `bi/to-int` に渡さない。clay の `bigint->int` は収まらない時に誤りの文言のため値を 10 進の
    文字列にするので、大きな結果のたびに文字列を作っていた (34 桁の割り算の DW で 15% 遅くなった)。
- 演算の結果の scale は Java と同じ規則で決める (add は max、mul は和、div は preferred scale)。
- scale は Int (64 ビット) で持ち、Java の int (32 ビット) の範囲外の scale は `parse` だけが拒む。
- 丸めモードは Int で、値は java.math.RoundingMode の ordinal と同じ (UP DOWN CEILING FLOOR HALF-UP HALF-DOWN HALF-EVEN UNNECESSARY)。
- DataWeave の除算の既定の精度は `DECIMAL128` (34 桁、HALF-EVEN)。`div` は割り切れるなら `div-exact` と同じ正確な結果、
  割り切れなければ精度と丸めモードで丸める (`div-mc`)。
- `pow-mc` は BigDecimal.pow(int, MathContext) の X3.274 の算法そのまま。
- 桁を作る演算 (scale をそろえる加減算、scale を上げる set-scale、整数への変換、累乗) は、結果の unscaled が `MAX-DIGITS`
  (1 千万) 桁を超えるなら `TOO-BIG` で失敗する。`pow-exact` は桁数の下限 (n × (precision - 1 + 0.3)) で先に判定し、作らずに断る。
- 失敗は `Values(T Str)`。err の文言は Java の例外メッセージに合わせる (0 除算は "Division by zero"、0/0 は "Division undefined")。
- Float の文字列化は Java 19 以降の Double.toString / Float.toString の最短往復表現にする (`float->shortest-str`、
  `float32->shortest-str`)。正規化数は clay の `float->shortest-decimal` (Schubfach) を使い、非正規化数 (4.9E-324 など) だけ
  多倍長整数の道 (`shortest-digits-fe`) で求める。
  - ただし 2^53 以上 2^63 未満の整数の double は、実 Mule が動く Java 17 の FloatingDecimal と同じ整数の道筋にする
    (`jdk17-long-digits`): long にした値の下の桁を `insignificantDigitsForPow2(binExp - 54)` の表の数だけ四捨五入して落とし、
    末尾の 0 を除く。-446744073709551616 は `-4.4674407370955162E17` (最短は `-4.467440737095516E17`)。Java 17 はこの範囲を
    いつもこの決まった手順で桁にするので、最短表現との違いがまれでない (protobuf の int64 や uint64 を DW が double で読む。
    2026-10-18)。期待値は test/dec/dtoa_long_test (Java 17 で作った 103 件)。test/dec/golden_data は Java 21 で作ったので、
    この範囲の行は比べない。

## 理由

- DataWeave の Number の意味論の土台なので、Java の BigDecimal と同じ値・同じ scale・同じ文言が要る。
- 2 通りの持ち方: 前は小さい値も毎回 BigInt で計算し、Java の BigDecimal (64 ビットに収まる間は long で計算する) より
  4〜18 倍遅かった。tools/dec-bench (1 コア、100 万回) で、足し算 22→14 ms、掛けて小数 2 桁に丸める 149→37 ms、
  文字列との往復 79→68 ms、34 桁の割り算 431→241 ms、比較 22→5 ms (Java 17 は 3、9、32、136、2 ms)。
  DW 全体 (tools/dw-bench の dec-div、dec-money、reduce) では 8〜12% 速くなった。
- 2 語に詰める理由: C の ABI は 16 B までの struct をレジスタで渡し受けし、それを超えると番地で渡して写す (clay の ADR 157)。
  3 語 (`[sm big scale]`) の時は、関数を呼ぶ形になると 1 回 10 ns ほど増えた。2 語にして tools/dec-bench で、足し算 14→3 ms、
  掛けて小数 2 桁に丸める 37→17 ms、文字列との往復 68→47 ms (parse-plain と plain-small を含む)、割り算 241→172 ms、
  比較 5→3 ms (Java 17 は 3、9〜13、32、136〜153、2 ms)。DW 全体ではさらに 3〜6% 速い。
- clay.decimal (clay 0.114.0) は使わない。値を正規化して scale を捨てる (1.0E+20 と 1E+20 が同じになる)、桁と小数点の位置が
  1000 までで 1E+999999999 を読めない、割り算が有効数字の桁数で丸められない、の 3 つが DataWeave と合わない。
- 境目の期待値は test/dec/edge_data.clay (tools/gen-dec-edge-golden.java が Java 17 で作る。±2^63、Long.MIN_VALUE、10^18 前後、
  scale -33..33、2^57 の前後、割る数が 10^9 の前後の divmc)。
- MAX-DIGITS: 1E+999999999 のような数は表現だけなら小さいが、展開すると確保に失敗してプロセスごと終わる。Java の BigInteger は
  約 6.5 億桁まで作るが、1 千万桁の加算は Java でも 300 秒で終わらない (利用者から見た違いは docs/compat/deviations.md)。
- 最短表現で clay の Schubfach を正規化数にだけ使ってよい理由: Java は最短が 1 桁なら 2 桁のうち最も近いものにするが、
  正規化数ではそれは常に 1 桁の値 × 10 なので同じ桁になる (x と c×10^q の差は x の 2^-53 倍以下で、2 桁の間隔 10^(q-1) の半分より
  小さい)。非正規化数では 2 桁が別の値になりうる。
- Java 17 の Double.toString と違うこと自体は docs/compat/deviations.md の「Double.toString」の行。

## 場所

- `mulay.lib.dec/Dec`、`small?`、`u-of`、`scale`、`mks`、`mkb`、`mk-big`、`addsub`、`cmp`、`parse-plain`、`plain-small`、`unscaled`、`unscaled-long`、`of-long`、`up-int`、`round-drop-int`、`drop-digits`、`div-exact-small`、`div-mc-small`、`div-mc-limbs`、`mode-of-str`、`DECIMAL128`、`MAX-DIGITS`、`TOO-BIG`、`div`、`div-exact`、`div-mc`、`pow-exact`、`pow-mc`、`parse`
- `mulay.lib.dec/shortest-digits`、`shortest-digits-fe`、`MIN-NORMAL`、`float->shortest-str`、`float32->shortest-str`
