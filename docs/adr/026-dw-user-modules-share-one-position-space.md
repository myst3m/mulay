# 026 — 利用者の DW モジュールは本体の後ろの位置から始まるように解析し、位置 1 つでどのソースかを決める

状態: **採用** (2026-09-29、74347c7)

## 決定
- 読み込むのは、本体 (と先に読んだモジュール) が import と修飾名 (`Utils::sum`) で参照した `dw::` 以外の
  モジュールだけ。loader はモジュールの名前 (`"mymod::Utils"`) からソースを返す (Mule のアプリは資源の
  `mymod/Utils.dwl`、dw::Runtime::run は fs の `"/Utils.dwl"`)。依存される側が先の順に読む。
- **モジュールは前に空白を置いて解析し (`(str (spaces b) src)`)、ノードの位置が本体のスクリプトと先に読んだ
  モジュールの後ろに来るようにする**。ソースの表 (`rt/Srcs` の `segs`、`rt/SrcSeg` の `base`) を位置で引けば、
  失敗の位置がどのソースのものかが分かる (`rt/seg-of`、`rt/excerpt-in`、`loc/script-loc-in`)。
- 失敗の表示 (`render-first-error`) は、読めなかったモジュールのエラーを diags の文言より先に出す。誤りが
  モジュールの中なら、抜粋と位置はそのモジュールのソースと名前で出す。

## 理由
- 位置はバイトオフセット 1 つ (ADR 019)。ソースごとに位置の範囲を分けておけば、位置からどのソースかが分かり、
  失敗の抜粋が本体の行と混ざらない (本体の外の位置には本体の抜粋を付けない)。
- モジュールのエラーを先に出すのは、そのモジュールを import した所の「Unable to resolve module」より、実 Mule と
  同じく本当の原因を見せるため。

## 場所
- `mulay.dw.engine/load-modules`、`mulay.dw.engine/compile-with`、`mulay.dw.engine/render-first-error`
- `mulay.dw.rt/Srcs`、`mulay.dw.rt/SrcSeg`、`mulay.dw.rt/seg-of`、`mulay.dw.rt/excerpt-in`
- `mulay.dw.loc/script-loc-in`
