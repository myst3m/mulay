# 092 — アプリのモデルの JSON (mule/amodel と `mulay inspect --json`)

状態: **採用** (2026-10-24)

## 背景

ライブ・ノート (WebIDE、別のリポジトリ) は、Mule の XML を自分で解釈しない。mulay が返すモデル (取り決めは
livenote の `src/runtime/contract.ts` の `AppModel`) を見て描き、位置 (ADR 091) のテキストだけを書き換える。
同じモデルを `mulay inspect --json` と、後で作る wasm の `load` の戻り値の両方で返す。

## 決定

- **組み立ては `mulay.mule.amodel/build`**。XML の木 (`ps/SrcDoc` の root と、位置を持つ `XLines`) をたどって組む。
  `m/App` のモデルだけからは組まない。モデルには書かれたままの要素名 (接頭辞付き)・エスケープ前の属性・`<when>` や
  `<route>` や `<error-handler>` の要素の位置が無く、それを全部モデルに足すとエンジンの値が重くなるため。
  - そのため `mule/load` は Mule の設定を `spans` 付きで読み、`Loaded` に `docs` (読んだ木) を残す。
- **パスは parse と同じ規則で数える**。`processors/k` は `doc:` の要素・`error-handler`・`batch:aggregator` を数えない。
  `<when>` は `route/<when の番号>`、`<otherwise>` は `route/<when の数>`、`<route>` は `route/i`。scope (foreach、try など) の
  本体は scope 自身のパスに `kind: body` の route 1 つで置く。コネクタの操作の子の鎖 (`op-chains`) も body の route にし、
  鎖ごとに 1 つ (each-child の操作は 1 つの body に子を並べる)。
  - 数え方が parse とずれないことは、`test/amodel` の `every-model-path-has-a-step` で守る。全 fixture のアプリについて、
    モデルの全プロセッサの `Loc.path` が JSON のステップにあることを確かめる。
- **種類 (`kind`) はモデルから取る**。同じパスのプロセッサの腕で決める (router: choice・scatter-gather・first-successful・
  round-robin、scope: foreach・parallel-foreach・try・until-successful・async・cache と鎖を持つ操作、unknown: `PrUnknown`)。
  モデルに無いパスは processor。
- **choice には必ず otherwise を最後に置く**。XML に `<otherwise>` が無ければ `spans: null`・ステップ無しの route を作る
  (画面はそこへの drop で `<otherwise>` を作る)。
- **受け口 (source)** の effect は none (画面が例で直接呼ぶので)。support は http:listener と scheduler が browser、
  ほかの受け口は relay (名前空間を知らなければ unsupported)。
- **XML として読めないファイル**も `files` に `root: null` で残す (画面が XML の表示で開いて直せるように)。
  `mule/load` は読めなかった設定の名前と中身を `Loaded` の `bad`・`bad-texts` に残す。診断の span は、xml の
  「line L, column C」(C は文字で数える) を元のバイト位置に戻した 1 文字の範囲。
- **try の中の error handler** は、try のステップの `errorHandler` (フローと同じ形) に置く。内部では ANode の子に
  kind "eh" (要素の範囲を持ち、子が entry) を置き、JSON に書くときに routes から外して errorHandler にする。
  entry も ANode (kind "entry"、`types`、`cond` に when) で表す。レコード同士が互いを持つ形を避けるため。
- **support と effect は conn/catalog の `component-info`** (コネクタの名前と URI は生成した表 conn/catalog_gen から引くので、コネクタのコードを持たない wasm の入口でも使える)。mule の層はコネクタを知らないので、関数を引数で受ける。
  - core・ee・batch の要素は browser / none。`PrUnknown` は unsupported / none。名前空間を知らない要素も unsupported。
  - 知っているコネクタは `op-effect` の表で effect を決め、none なら browser、それ以外は relay。
    純粋なもの (`PURE`: validation、os、vm、mule-apikit、munit、munit-tools、jmx) は none。http の request は method が
    GET・HEAD・OPTIONS なら read。db は select、salesforce は query・retrieve・describe・search・get- で始まる操作、
    file と sftp は read・list、mcp は list-tools が read。ほかは write。
- **診断**は `m/Diag` から作る。severity は今はすべて error (mulay の診断はどれも起動を止めるので)。path があれば、
  そのステップ (またはフロー、handler) の要素の範囲を span にする。file は読んだファイルの名前に接頭辞を付ける。
- **ファイルの名前**は、ディレクトリのプロジェクトなら `src/main/mule/` を付けた、プロジェクトからの相対パス
  (取り決めの `ProjectFile.path` と同じ形)。XML 1 つや JAR から読んだときは付けない。
- livenote は `test/mulay-model.test.ts` で、仮の実行エンジンのモデルと `target/mulay inspect --json` を突き合わせている。
- **`inspect --json` の終了コード**は、診断があれば 1 (文字のときの inspect と同じ)。JSON はどちらでも出す。
  診断は JSON に入るので、標準エラーには出さない。

- **batch:job** (2026-10-24、livenote の図 11): `kind: "scope"` で、routes に中を縦に並べる。route の kind は
  - `batch-step`: path `<job>/process-records/<i>`、`name`、`acceptPolicy` (無ければ NO_FAILURES)、`acceptExpression` (あれば)。
    steps は `<job>/process-records/<i>/processors/<k>`。
  - `aggregator`: その step のすぐ後ろ。path `<step>/aggregator`、`size` (数のとき)、steps は `<step>/aggregator/processors/<k>`。
  - `on-complete`: path `<job>/on-complete`、steps は `<job>/on-complete/processors/<k>`。
  パスは parse (rt の Loc) と同じなので、トレースと同じ版で対応する。それまでは中身の無い processor として出していた。

## 場所

- `mulay.mule.amodel`: `build`、`to-json`、`model-paths`、`step-paths`、`routes-of`、`handlers-of`、`source-info`、`xml-err-span`、`ANode`・`AFlow`・`AGlobal`・`AFile`・
  `ADiag`・`AModel`・`Info`
- `mulay.conn.catalog`: `component-info`、`op-effect`、`PURE`。表は `mulay.conn.catalog_gen` (`tools/gen-catalog/gen.sh` で conn/registry から作り直す。test/amodel の `catalog-matches-registry` がずれを見つける)
- `mulay.mule.load`: `xml-opts` (`:spans true`)、`Loaded` の `docs`
- `mulay.mule.model/proc-loc` (rt/engine から移した)
- `mulay.cli.boot`: `cmd-inspect`、`inspect-json`
- テスト: `test/amodel/amodel_test.clay`、fixture は `test/fixtures/livenote/orders-api` (livenote の `samples/orders-api` の写し)
