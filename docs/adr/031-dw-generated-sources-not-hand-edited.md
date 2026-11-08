# 031 — fnarity.clay と stdlib_locs.clay は実 DW の .dwl から生成し、手で編集しない

状態: **採用** (fnarity は 2026-09-29、f1a2a09。stdlib_locs は 2026-09-29、02b5ac7)

## 決定
- `src/mulay/dw/fnarity.clay` は `tools/gen-fn-arity.py` の生成物。一次資料は docs/dw-stdlib-catalog.md
  (DataWeave 2.11.2 の .dwl から取ったシグネチャ)。表は `FN-ARITY` (関数型の引数の引数の数)、`FN-TYPE` (関数型の
  綴り)、`FN-SIG` (オーバーロードごとの引数の数の幅・既定値の有無・型の綴り)、`FN-RET` (引数の型が分からない
  ときの戻り値の単純な型)。
- `src/mulay/dw/stdlib_locs.clay` は `tools/gen-stdlib-locs.py` の生成物。一次資料は実 Mule 4.11.3 同梱の
  DataWeave 2.11.2 の .dwl (wlang-2.11.2.jar)。表は `NATIVE-LOC` (native の関数のオーバーロードごとの位置) と
  `NATIVE-TEXT` (宣言の行)。
- **どちらも手で編集しない**。直すときは生成器か一次資料を直して作り直す。
- `src/mulay/cli/aot.clay` (事前コンパイルの登録表を返す stub) は通常のビルドでは空で、`mulay build` がビルド用の
  ディレクトリで生成したものに差し替える (docs/aot.md §3、ADR 082)。リポジトリの版は空のまま保つ。

## 理由
- 引数の数・型・位置は実 DW の標準ライブラリの宣言が正 (正しさの基準)。手で写すと一次資料とずれる。

## 場所
- `mulay.dw.fnarity/FN-ARITY`、`mulay.dw.fnarity/FN-TYPE`、`mulay.dw.fnarity/FN-SIG`、`mulay.dw.fnarity/FN-RET`
  (使う所: `mulay.dw.resolve/check-arity`、`mulay.dw.resolve/check-fn-args`)
- `mulay.dw.stdlib_locs/NATIVE-LOC`、`mulay.dw.stdlib_locs/NATIVE-TEXT` (使う所: `mulay.dw.loc/stdlib-loc`、
  `mulay.dw.rt/native-frame`)
- `mulay.cli.aot/aot`
- `tools/gen-fn-arity.py`、`tools/gen-stdlib-locs.py`
