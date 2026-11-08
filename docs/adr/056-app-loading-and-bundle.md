# 056 — アプリはディレクトリ・JAR・単体の XML から同じ形 (Loaded) に読み、埋め込みは長さ付きの文字列の束にする

状態: **採用** (2026-09-28。束は 2026-09-29 d680f7f、JAR の資源だけの展開は 2026-10-12 8e52f4b)

## 決定
- `mulay.mule.load/load-path` は path の種類で読み方を変え、どれも `Loaded {app res files texts}` にする:
  1. ディレクトリ: Mule プロジェクト。src/main/mule 以下の `*.xml` (再帰、名前順) のうちルートが `<mule>` のもの
     (application-types.xml などを除く)。mule-artifact.json に `configs` があればその並び。資源は src/main/resources。
  2. `*.jar` / `*.zip`: デプロイ可能な JAR。META-INF/mule-artifact/mule-artifact.json の `configs` を読む。資源は JAR の中身。
  3. それ以外: 単体の XML。資源は `.../src/main/mule/x.xml` なら `.../src/main/resources`、そうでなければ XML のあるディレクトリ。
- ディレクトリを歩くとき、`.` で始まる名前は読まない。Kubernetes の ConfigMap のマウントは `..data` と `..2026_xx/` を置き、
  同じファイルが 2 度見えるため。
- JAR の資源は、アプリの資源だけを展開してメモリの表にする。除くエントリはディレクトリ、`repository/` (Java の依存の JAR)、
  `META-INF/` (Maven とデプロイの情報。mule-artifact.json は読み込みのときだけ読む)。埋め込み (`bundle-of`) も同じ規則で除く。
  展開した大きさの合計は 1 GB (`JAR-RES-MAX`) まで。エントリごとに中央ディレクトリの展開後の大きさで先に確かめ、超えれば
  展開せずに diag `<名前>: the application's resources are too large (more than 1073741824 bytes in total)` にする
  (1 エントリは今までどおり 256 MB まで)。前は合計に上限が無く、圧縮率の高いエントリを並べた JAR でメモリを使い切った
  (2026-10-25、敵対的レビュー)。テストは test/mule/load_jar_test の jar-resources-have-a-total-limit。
- 複数ファイルのフローは 1 つの App に統合する。フロー名・大域要素名の重複は diag (フローとサブフローは同じ名前空間)。
  `<import file="..">` は同じ規則で探して読み、既に読んだものは読まない。global-property はすべて先に読み、ファイル名の `${}` に使う。
- **埋め込み (mulay build。docs/aot.md)**: 読み込んだアプリを、設定ファイル (import したものを含む) と資源の束 `Bundle` にする。
  - 資源は、ディレクトリなら再帰的に全ファイル (`.` で始まる名前を除く)、JAR なら上の除外を除く全エントリ。合計が
    `BUNDLE-MAX` (64 MB) を超えたら失敗。
  - 文字列の形: `mulay-bundle-2\n` のあと、各文字列を `<長さ>:<中身>` で並べる (名前、ファイル数、各ファイルのラベルと本文、
    資源の数、各資源のパスと中身、pom の依存の数、各依存の groupId・artifactId・version)。壊れていれば `bundle-decode` が失敗を返す。
    2026-11-02 に依存を足して 2 にした (APIkit の版で振る舞いを変えるため。古い束は読まない: 束は同じ mulay が作って埋め込む)。
- **pom の依存**: プロジェクトの pom.xml (ディレクトリ、src/main/mule の XML を直に渡した時はその上の pom、JAR は
  META-INF/maven/*/*/pom.xml) の `<dependencies>` を `App` の `deps` (groupId・artifactId・version。`${x}` は `<properties>` から) に持つ。
  - 起動時は束からメモリ上で読む (`load-bundle`)。import は束の中のファイルから探す。

## 理由
- 埋め込んだ実行ファイルは引数なしでアプリを起動し、`mulay run` と同じ結果になる (d680f7f: tools/mule-oracle-aot.sh の
  アプリごとの結果が mulay run と一致)。そのため読み込みは束からも同じ Loaded を作る。
- `.` で始まる名前と JAR の除外の理由は上の各項に書いた (ConfigMap の二重の見え方、RSS。ADR 048)。

## 場所
- `mulay.mule.load`: `load-path`、`load-texts`、`Loaded`、`xml-files`、`artifact-json`、`jar-skip?`、`jar-res`、`build`、
  `Bundle`、`BUNDLE-MAX`、`bundle-of`、`walk-res`、`bundle-encode`、`bundle-decode`、`take-str`、`load-bundle`
- `mulay.mule.parse`: `check-dups`
