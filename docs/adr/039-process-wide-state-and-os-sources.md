# 039 — Mule との接点は大域の atom に持ち、環境変数と乱数は OS から直接取る

状態: **採用** (2026-09-28。乱数の取り方は 2026-10-02、5156bb0)

## 決定
- dw::Mule の p() が読むアプリのプロパティは、アプリの読み込み時に app 層が `set-properties!` で渡し、大域の atom に持つ。
  プロセスで 1 アプリなので大域でよい。DW 単体 (mulay dw、golden) では空。
- readUrl の classpath:// は、アプリが資源を登録していれば (`set-classpath!`) その資源だけを見る (実 Mule のアプリの
  クラスパス)。登録が無ければ (DW 単体) 作業ディレクトリ相対で、無ければ src/main/resources/ も見る。evalUrl / runUrl も
  同じ経路で探し、アプリの資源の外 ("..", 絶対パス) を作業ディレクトリから読まない。
- Mule::lookup はランタイムとの連携が要るので持たない (docs/compat/deviations.md)。
- envVars() / envVar() は getenv ではなく environ を直接読む。getenv は未設定と空文字列を区別できない。
- random() と uuid() は OS の暗号用の乱数から作る (random は 53 ビット、uuid は版 4)。取れなければ clay の擬似乱数に落とす。

## 理由
- 評価器 (dw 層) は app 層を require できない。app 層が値を流し込む口を dw 層に置けば、層の向きを守れる。

## 場所
- `mulay.dw.lib.mule/PROPS`、`mulay.dw.lib.mule/set-properties!`
- `mulay.dw.lib.core_io/CLASSPATH`、`mulay.dw.lib.core_io/set-classpath!`、`mulay.dw.lib.core_io/clear-classpath!`、`mulay.dw.lib.core_io/load-url`
- `mulay.dw.lib.system/environ`、`mulay.dw.lib.system/env-lookup`
- `mulay.dw.lib.core_num/random-float`、`mulay.dw.lib.core_misc/uuid4`
