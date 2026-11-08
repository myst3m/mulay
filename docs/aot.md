# DataWeave の事前コンパイル (mulay build)

`mulay run` は DataWeave を読み込み時に閉包の木にして実行する (docs/dw-eval.md §5)。重い計算
(bench の compute) では JIT を持つ Mule に届かない。`mulay build` は、アプリの DataWeave を Clay の
ソースに変換し、clay でアプリ専用の実行ファイルを作る。

## 1. 使い方と前提

```
mulay build <project-dir|app.jar|file.xml> -o app-bin [key=value ...] [--encrypt -k 鍵]   # clay と clang が要る
./app-bin                          # アプリを埋め込んでいるので引数は要らない (${..} のプロパティが全部決まっているなら)
./app-bin http.port=9090 -l DEBUG  # プロパティ (key=value か -p key=value) とログレベルだけ受け付ける
./app-bin version
```

- ビルドのときの `key=value` (`-p key=value`) は、アプリの検査と DataWeave の事前コンパイルに使い、実行ファイルにも埋め込む。
  実行時に渡した `key=value` は埋め込んだ値より優先する。埋め込みは `--encrypt` の有無で決める:
  - なし: 値は base64 で入るだけ (難読化にもならない。誰でも戻せる)。
  - `mulay build ... --encrypt -k <鍵>` (鍵は環境変数 `MULAY_KEY` でも渡せる): 埋め込む値をまとめて封じる (lib/seal。
    PBKDF2-HMAC-SHA256 で鍵を導き、AES-256-CBC で暗号化して HMAC-SHA256 を付ける)。鍵は実行ファイルに入れない。
    実行ファイルは起動のとき `-k <鍵>` か `MULAY_KEY` が要る。無ければ `<this executable> -k <key>` と案内して終了し、
    鍵が違うか壊れていれば `wrong key, or the data is corrupted` で終了する。
  - 暗号化するのは `-p` で渡したプロパティだけ。アプリ自身の設定ファイル (`src/main/resources` の .yaml など) は平文で入る。
    設定ファイルの秘密は secure-properties (`![...]`) にする。
  - 引数 (`-k <鍵>`) は `ps` で他のユーザーから見える。鍵は `MULAY_KEY` で渡す方がよい。
  `${..}` のプロパティは起動のたびに解決する。解決できないものがあれば、起動時に名前を挙げて
  `error: 3 configuration properties are not set: http.port, greeting, who` / `Pass them as options:  <this executable> http.port=<value> ..` と案内する
  (`mulay run` / `validate` / `build` も同じ。cli/opts)。
- 生成した実行ファイルは、アプリ (設定ファイルと資源) と、事前コンパイルした DataWeave を埋め込む。
  起動時は埋め込んだ束からメモリ上で読み込む (mule/load の bundle-of / load-bundle)。
- 資源は、プロジェクトなら src/main/resources 以下の全ファイル、JAR なら repository/ と META-INF/ を除く
  全エントリ (Java の依存は mulay では使わない)。単体の XML ならその XML のディレクトリ以下 (合計 64 MB まで)。
- DataWeave のスクリプトは本文のハッシュで生成済みのコードを引き、見つからなければ閉包のコンパイルで動く
  (結果は同じ。遅いだけ)。埋め込んだアプリのスクリプトは全部見つかる。
- ビルドの時点で clay と clang が要る。実行には要らない。
- 実行ファイルは 14 MB 前後 (シナリオの 35 アプリで 13.9〜14.4 MB)。動的にリンクするのは
  libc と libm (glibc) だけ (2026-10-13 から。完全な静的リンクとクロスコンパイルはまだ)。
- 起動は十数 ms、起動直後の RSS は 16 MB ほど (vm-test、2026-09-30)。

## 2. 実行の仕組みが 2 つになることについて

閉包のコンパイル (`ev/compile-prog`) と生成したコード (`dw/gen`) は、同じ意味を 2 通りに実装する。
食い違いを防ぐために:

- 生成するコードは、節の意味を持つ実行時の補助関数 (eval の公開関数) を呼ぶ。制御の流れ (if、and/or、
  default、match、ループ) だけを生成側で書く。
- DataWeave の golden (test/fixtures/dw の 3,319 件) を両方で回す (`tools/dwt-all.sh` と `tools/dwt-aot.sh`)。
  失敗の集合が同じであることを確かめる。

## 3. 仕組み

- **登録表**: (スクリプトのハッシュ, 組み立て関数) の表 (`mulay.dw.genreg/Gen` の Vec)。入り口の package の stub
  (本体は `mulay/cli/aot.clay`) の `aot` 関数が、表と埋め込みを `genreg/Aot` で返す。通常のビルドでは空。
  boot は起動時に `eng/set-generated!` で表を dw/engine に渡す (ADR 082)。
  `mulay build` はビルド用のディレクトリにソースの root を写し、stub を生成した表に差し替え、生成した
  モジュール (`<stub の ns>_s<ハッシュ>` と `<stub の ns>_app`) を stub と同じディレクトリに足して、clay でビルドする。
- **引き当て**: dw/engine の compile (compile-with) は、解決した IR (r/Prog) を作ったあと、本文と入力名のハッシュで表を引く。
  見つかれば組み立て関数に r/Prog を渡して ev/CProg を得る。無ければ ev/compile-prog。どちらも結果は
  Compiled に入り、起動状態の def で不死になる。
- **節の番号**: `gen/nodes` は r/Prog の式の節を決まった順 (前順) に並べる。生成側と実行時の両方がこれを
  使うので、生成したコードは節を番号で指せる。
- **任せる節**: 生成側が書かない節 (update、match、キー以外のセレクタ、名前空間か属性の付いたキーのオブジェクト
  など) は、実行時にその節を閉包にコンパイルしたもの (`ev/cx`。`gen/make-g` が `gen/G` の cs に置く) を呼ぶ。任せた節の下の部分木も閉包に
  なる (`sum(..) as String` の sum も) ので、よく通る節は生成側で書く。2026-10-04 の golden の全スクリプトで、
  任せる箇所は 298 (as / is / 補間 / 式のキーと展開のオブジェクトを書く前は 684)。残りの多くは型の値 (RTypeV)、
  添字のセレクタ (`x[i]`)、match、`?`。

## 4. 段階

1. **そのまま変換** (済み): IR の各節を Clay の式にする。値は箱入り (v/Val) のまま、関数本体は末尾呼び出しを
   含めて閉包と同じ規約 (`T`) の関数にする。生成するのは、定数・slot・算術・if・and/or/not・default・
   do の var・呼び出し・クロージャ・キー選択・オブジェクト (名前か式のキー、展開)・配列・as / is・文字列の補間。
   オブジェクトの名前のキーはモジュールの定数 (`KEY<i>`) にして確保しない。as / is の型は `gen/G` の vals に VType で置く。
2. **高階関数の展開** (済み): `map`・`filter`・`reduce`・`orderBy` の関数引数がその場のラムダなら、生成側の
   ループにする。ラムダの slot は Clay の局所変数になり、引数の Vec・フレーム・組み込み関数の経由がなくなる。
   条件: コレクションが実行時に Array か Range (違えば組み込み関数を呼ぶ)、ラムダの本体の末尾位置に
   呼び出しが無い (末尾呼び出しの深さの数え方が変わるため)、渡さない引数にはすべて既定値がある。
   集計 (sizeOf / sum / avg / max / min) の引数が展開できる map / filter なら、要素を配列に集めずに
   `cc/fold-add` に渡す (eval の集計の合成と同じ。docs/dw-eval.md §5)。
3. **Int の推測** (まだ): Int であることが多い値を、型を確かめたうえで箱に入れずに計算する。

## 5. 検証

- `tools/dwt-aot.sh [-e] [-v]`: 全フィクスチャのスクリプトを生成してビルドし、golden を回す。
  失敗の集合が `tools/dwt-all.sh` (閉包) と同じであることを確かめる
  (2026-09-30: 2,710 件すべて通る。生成したモジュールは 2,312。生成とビルドで約 1 分)。
- `tools/mule-oracle-aot.sh [app ...]`: アプリごとに mulay build で実行ファイルを作り、シナリオを回す
  (2026-09-30: 35 アプリで 779/781。外れは mulay run と同じ core-modules の 1 件と db-pg の 1 件。全体で約 8 分)。
- 生成したコードが実際に使われていることは、生成したモジュールの本体を壊すと該当のフィクスチャが落ちる
  ことで確かめた。

## 6. 計測

bench (`test/fixtures/mulet-samples/bench`、2 コア、`wrk -t2 -c8`、同じ負荷の下で交互に計測)。req/s。2026-09-28 の計測。

| フロー | mulay run (閉包) | mulay build | Mule 4.11.2 |
|---|---:|---:|---:|
| compute | 667 | 1,175 | 1,010 |
| nested | 657 | 1,323 | 477 |
| transform | 9,133 | 10,381 | — |
| pipeline | 7,190 | 8,116 | — |

手書きの試作 (`(1 to 5000) reduce ((item, acc = 0) -> acc + item * item)` を 400 回): 閉包 156 ms、
そのまま変換 121 ms、本体の Int の推測 101 ms。残りは reduce の仕組みで、段階 2 で消えた。
