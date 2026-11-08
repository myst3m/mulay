# ADR 082: mulay build は、入り口の package にある stub を差し替えてビルドする

日付: 2026-10-20。状態: 決定。ADR 081 の「決めていないこと」の `mulay build` を決める。docs/aot.md §3 も参照。

## 背景

- `mulay build` は、アプリと事前コンパイルした DataWeave を埋め込んだ実行ファイルを作る。
- 今の作り:
  - ビルド用のディレクトリに src/mulay を symlink で写す。
  - 本体のモジュール `mulay.dw.genreg` (登録表と埋め込みの文字列) を、生成したものに差し替える。
  - 生成したモジュール `mulay.gen.*` を足し、`mulay/cli/main.clay` をビルドする。
- 配布物 (ADR 081) では、mulay は `git:` で取ってきた package になる。clay の ADR 111 により、取ってきた package は次しか読めない。
  - 自分の checkout の中
  - 自分の `clay.pkg` が `git:` で名指しした package
  - stdlib
- そのため、mulay の中のモジュールを差し替えることも、mulay の中から配布物の側の生成物を `:require` することもできない。
- 配布物の実行ファイルは、自分のソースの場所も知らない。

## 決定

1. **生成物は、入り口の package の stub から実行時に渡す**
   - 本体は生成物を `:require` しない。
   - 入り口の package は、stub のモジュールを 1 つ持つ。
     - 本体では `mulay/cli/aot.clay` (ns `mulay.cli.aot`)。
     - 配布物の見本では `aot.clay` (ns `aot`)。
   - stub の `aot` 関数は `genreg/Aot` を返す。中身は次のとおり。
     - 自分の ns
     - root から見た自分の path
     - 入り口の path
     - 登録表 (`Vec(Gen)`)
     - 埋め込んだアプリ
     - 埋め込んだプロパティ
   - 入り口は `(boot/boot-from-argv conns (aot/aot))` と書く。
   - boot は、まず `eng/set-generated!` で登録表を DW のエンジンに渡し、それから argv を読んでアプリを読み込む。
   - 登録表は、dw/engine の atom に `Dyn` として入れる。Fn を持つ record を `->dyn` / `dyn->rec` で出し入れして呼べることは確かめた (2026-10-20)。
     - 入れるのは起動時の 1 回だけで、worker のスレッドは読むだけ。
     - 引くのは compile のときだけなので、要求ごとの費用は無い。
2. **argv の解釈と埋め込みの判定は boot-from-argv の中で行う**
   - 前は `mulay.cli.boot` の大域の def `ARGV` が、モジュールの初期化の時に `genreg/embedded` を読んでいた。
   - 埋め込みが入り口から来るようになると、この def は入り口の `BOOT` より先に評価されるので、値が決まらない。
   - そこで `Boot` に、引数・argv の誤り・`Aot` を持たせ、`run-main` はそれを見る。
3. **build は stub が名乗る path の 1 file だけを差し替える**
   - ビルド用のディレクトリ `<out>.build` に、ソースの root を写す。stub までの途中のディレクトリだけを実体にし、それ以外は symlink にする。
   - stub の file を、生成した stub で置き換える。生成した stub は、同じ ns で、登録表と埋め込みが入ったもの。
   - 生成したモジュールは、stub と同じディレクトリに並べる。
     - DataWeave は `<ns>_s<ハッシュ>`。
     - 埋め込みは `<ns>_app`。
     - file は `<stub の path から .clay を除いたもの>_s<ハッシュ>.clay` と `.._app.clay`。
   - 下のディレクトリ (`<ns>.s<ハッシュ>`) にしない理由は clay の package の探し方にある (2026-10-20 に pkg-check で確かめた)。
     - clay は、package のディレクトリの直下の `.clay` を、ns によらず全部取り込む。
     - path で探すときの root は、package のディレクトリの親になる。
     - 配布物の見本の stub (ns `aot`、直下の `aot.clay`) の下に `aot/s<ハッシュ>.clay` を置くと、どちらの規則でも見つからない。
     - 隣に並べれば、本体 (path で探す) でも配布物 (直下を取り込む) でも見つかる。
   - `mulay.` の接頭辞は使わない。配布物では、取ってきた mulay の root と重なるため。
   - clay でビルドする。
     - ソースの root に `clay.pkg` があれば、ビルド用のディレクトリを渡す。`clay.pkg` は symlink で写るので、`git:` の固定はそのまま使われ、依存は clay の cache から来る。
     - `clay.pkg` が無ければ (本体)、入り口の file (`<out>.build/<entry>`) を渡す。clay は、file を渡すと `clay.pkg` を読まない。
4. **ソースの root は、入り口の path で見つける**
   - 次の順に探し、`<候補>/<entry>` が file として在る最初のものを使う。
     1. 環境変数 `MULAY_SRC`
     2. 実行ファイルのディレクトリ
     3. 実行ファイルのディレクトリの `../src`
   - 本体 (`target/mulay` → `src/`) と、配布物 (配布物のディレクトリでビルドした実行ファイル) の両方が、設定なしで見つかる。
   - 配布物では `<out>.build` がソースの root の中にできることがある。写すときは、root の直下のその名前を飛ばす (自分自身への link を作らない)。
5. **DataWeave の golden の事前コンパイル (`tools/dwt-aot.sh`、cli/dwt) も同じ stub を使う**
   - dwt の main は、起動時に `mulay.cli.aot` の登録表を `set-generated!` で渡す。
   - `tools/dwt-aot.sh` は、`mulay/cli/aot.clay` を差し替える。

## 考えたが採らなかったもの

- **clay に、依存の module を上の package から差し替える機能 (cargo の patch のようなもの) を頼む**
  - ADR 111 が「取ってきた package は commit で固定した中身で組む」とした趣旨に反する。
  - mulay の側の反転で済む。
- **登録表を LoadOpts で compile まで引数で通す**
  - DataWeave を compile する経路は load の外にもある。
  - atom に入れる形が動いたので、採らなかった。
