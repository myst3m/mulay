# 060 — CLI は <app> を省けばカレントディレクトリとし、埋め込んだ実行ファイルはプロパティとログレベルだけを受ける

状態: **採用** (2026-09-29 d680f7f。<app> の省略は 2026-10-08 1eb29ad)

## 決定
- `run` / `validate` / `inspect` / `build` は `<app>` を省くとカレントディレクトリ (`.`) を対象にする。2 つ目の引数が無いか、
  オプションに見える (`-` で始まる、または `key=value`) ときに `.` を差し込む (`with-default-app`)。
- プロパティは `key=value` と `-p key=value` で渡し、アプリ自身の値より優先する。`-p` の後の値に `=` が無ければプロパティではなく
  残りの引数に回す。`-l LEVEL` はログレベル。
- 引数の誤りは理由と使い方の行を標準エラーへ出し、終了コード 2 (`misuse`)。
- 読み込みの診断に解決できなかったプロパティがあれば、その名前 (重複なし、出た順) をオプションで渡す案内を出す
  (`unresolved-keys`、`missing-hint`)。
- `mulay build` で作った実行ファイルはアプリを埋め込んでおり、引数なしで起動する。受けるのは `key=value` と `-l LEVEL`
  (と、封じたプロパティの鍵 `-k` / `--key`、先頭の `run`)。version と help のほかは起動する。埋め込んだプロパティに実行時の
  オプションを重ね、同じ名前は実行時が勝つ (`merge-props`)。埋め込むプロパティの形は `"<長さ>:<名前><長さ>:<値>"` の列で、
  埋め込みの文字列は "" が無し、`P…` が平文、`E…` が封じたもの (鍵が要る)。
- `dw-gen` は内部用 (docs/aot.md) なので help に載せない。
- `mulay build` のビルド用の引数 (`-o` の値など) は、シェルに渡すとき `fs/sh-quote` で引用し、コマンドとして読まれないようにする (`q`)。

## 理由
- 埋め込んだ実行ファイルはアプリの起動だけに使い、`mulay run` と同じ結果にする (d680f7f)。

## 場所
- `mulay.cli.opts`: `wants-help?`、`serves-app?`、`parse`、`unresolved-keys`、`missing-hint`、`take-key`、`take-flag`、
  `encode-props`、`decode-props`、`merge-props`、`need-key-hint`、`with-default-app`
- `mulay.cli.main`: `main`、`misuse`、`embedded-props`、`key-of`、`q`、`cmd-build`、`cmd-dw-gen`
- `mulay.cli.help`
