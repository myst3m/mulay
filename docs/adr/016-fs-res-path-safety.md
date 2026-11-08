# 016 — ファイルの作成は 1 回の open で有無を確かめ、資源のパスは ".." を拒み、シェルに渡すパスは単一引用符で 1 語にする

状態: **採用** (2026-09-29、ca4fceb。資源の集合は 2026-10-01、55cb71e)

## 決定

- `mulay.lib.fs/create-new`: 無ければ空のファイルを作る (O_CREAT | O_EXCL)。有無の確かめと作成を 1 回の open(2) で行う。壊れた symlink も
  「ある」とする。
- `mulay.lib.fs/move`: rename(2)。別のファイルシステムなら写してから消す。
- `mulay.lib.fs/remove-tree` はリンクをたどらない。`stat` はリンク先が無い (壊れたリンク) ならリンクそのものを OTHER として返す。
- `mulay.lib.fs/sh-quote`: パスを POSIX シェルの 1 語にする。単一引用符の中は何も展開されないので、`'` だけを `'\''` (閉じて、逃がした
  `'` を置いて、開き直す) にする。`-` で始まる相対パスはコマンドのオプションに読まれないよう `./` を前に付ける。
- `mulay.lib.res/res-read` (アプリの資源。Java のクラスパスにあたるもの): "classpath:" と先頭の "/" "./" を外して読み、".." を含むパスは
  読まない。メモリ、ディレクトリ、zip の順に探す。`res-url` はディレクトリの資源でファイルがあるときだけ "file:" + 絶対パス
  (ClassLoader.getResource の文字列)。

## 理由

- create-new: 確かめてから書く間に別のファイルや symlink を置かれても、その先を上書きしない (O_EXCL は symlink をたどらない)。
- res-read: パス走査の防止。

## 場所

- `mulay.lib.fs/create-new`、`move`、`remove-tree`、`stat`、`sh-quote`
- `mulay.lib.res/res-read`、`norm-res-path`、`res-url`

## 関連
- ADR 047 (コネクタ側の、外から来たパスと名前)
