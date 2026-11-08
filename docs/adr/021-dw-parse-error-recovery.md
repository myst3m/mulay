# 021 — DW のパーサは誤りから回復して読み続け、診断の連鎖は位置で抑える

状態: **採用** (2026-09-28、ce64f08 の初版から)

## 決定
- **診断が 1 つでもあれば失敗**だが、パーサは止まらずに回復し、回復した部分を `EErr` として木に残す。
- 回復の仕方:
  - 並びの中 (`skip-in`): 括弧の釣り合いを見ながら、深さ 0 の `,` か、いま読んでいる並びの閉じ括弧か、`---` か
    入力の終わりまで飛ばす。深さ 0 の別の閉じ括弧 (`[1, }]` の `}`) は読み飛ばす。
  - 並びの外 (`skip-to-closer`): 深さ 0 の `, ) ] } ---` か入力の終わりまで。
  - 一次式で読めないトークンは、閉じ括弧などを除いて 1 トークン進めて無限ループを防ぐ。
- 診断の連鎖を抑える:
  - 同じ位置に 2 つ目の診断は出さない (`diag-lines`)。
  - "Missing .." を積んだら、次のトークンの位置まで診断を黙らせる (St の `hush`)。後に続く "expected Expression"
    を表に出さないため。
  - 診断は最大 `MAX-DIAGS` (64) 個。
- 最初の診断が利用者に見える文言になるので、実 DW の文言を最初に出すよう順を作る: 入力が括弧の中で終われば、
  "Missing .." や "expected Expression" ではなく、いちばん内側の括弧が待つものの文言にする (`eof-context`、
  トークンを頭から数えるだけの近似で、失敗のときだけ使う)。
- 構文の誤り (parboiled の文言 "Invalid input ..", "Unexpected end of input ..") には実 DW と同じく
  " (line L, column C):" と改行を付け、DW 独自の文言 ("Missing .." など) には付けない。

## 理由
- golden は失敗の 1 行目で比べる。回復で後ろを読み続けても、連鎖した診断が 1 行目を奪わないようにする。

## 場所
- `mulay.dw.parse/diag-lines`、`mulay.dw.parse/missing`、`mulay.dw.parse/MAX-DIAGS`、`mulay.dw.parse/St` (`hush`)
- `mulay.dw.parse/skip-in`、`mulay.dw.parse/skip-to-closer`、`mulay.dw.parse/eof-context`
- `mulay.dw.parse/with-positions`
