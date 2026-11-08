# 109 — `mulay dw` は --path・スクリプトのディレクトリ・Mule プロジェクトの src/main/resources からモジュールを読む

状態: **採用** (2026-11-01)

## 問題

- `mulay dw <script.dwl>` は、ユーザーのモジュール (`import * from domain::Application`、`a::b::C` は `a/b/C.dwl`) を読まなかった
  (コンパイルにモジュールの読み手を渡していなかった)。アプリの中 (`mulay run`・`validate`) では src/main/resources から読めるので、
  ドメインのモジュール (純粋な関数) をアプリを起動せずに確かめられなかった (別のプロジェクトからの報告、2026-11-01)。

## 決定

- `mulay dw [--path <dir>]... <script.dwl> [name=mime:file ...]`。モジュールは次の順に探し、最初に見つかったものを読む:
  1. `--path` に書いたディレクトリ (書いた順)
  2. スクリプトのディレクトリ
  3. スクリプトのディレクトリから上へたどって最初に見つかった、`src/main/resources` を持つディレクトリの `src/main/resources`
     (スクリプトを持つ Mule プロジェクトのクラスパス)
  4. 作業ディレクトリから同じくたどって見つかった `src/main/resources`
- 同じディレクトリは 1 度だけ探す。見つからなければ今までと同じ "Unable to resolve module with identifier ..."。
- Exchange の依存 (jar の中のモジュール) は読まない。

## 理由

- Mule のアプリでモジュールが見えるのはクラスパス (src/main/resources) で、プロジェクトの中のスクリプトは、何も書かずにアプリと同じ
  モジュールが見えるのが自然。プロジェクトの外のスクリプトや別の置き場所は --path で足す。
- スクリプトのディレクトリを探すのは、1 つのディレクトリに置いたスクリプトとモジュールを、そのまま試せるようにするため。

## 場所

- `mulay.cli.dwpath/roots`・`loader`、`mulay.cli.boot` の `cmd-dw`、`mulay.dw.engine/run-text-with`
