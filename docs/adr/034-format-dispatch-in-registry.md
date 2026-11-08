# 034 — データ形式の reader / writer の振り分けは fmt/registry の 1 か所に置く

状態: **採用** (2026-09-28 の記録。初期取り込みからこの形)

## 決定
- MIME から形式を選んで reader / writer を呼ぶのは `mulay.dw.fmt.registry` だけにする。新しい形式はここに 1 か所足す。
  engine、DW の read() / write()、Mule の TypedValue がすべてここを通る。
- 形式ごとの有効なプロパティ・型・既定値は docs/dw-formats.md (実 DW の dataFormatsDescriptor) の表に従い、
  registry の表 (`FORMAT-PROPS`、`OPT-TYPES`) に持つ。各形式のモジュールは未知のプロパティを無視せず、検査は registry が
  まとめてする (`validate`、`validate-strict`)。
- プロパティの取り出しとメタデータの剥がし・付け足しは `mulay.dw.fmt.props` に共通化する。
- multipart の部分の中身は形式ごとの reader / writer で読み書きするが、`mulay.dw.fmt.multipart` は registry を require しない。
  registry が部分の reader / writer を関数として渡す (`part-reader`、`part-writer`)。入れ子の段数は `part-reader` の引数で運ぶ。
- 形式の reader は評価器を使わない。fmt は評価器より下の層なので、application/dw の reader はデータ (リテラル) だけを読み、
  式は失敗にする (利用者から見える違いは docs/compat/deviations.md)。

## 理由
- 振り分けが複数あると、形式やプロパティを足したときに経路ごとに挙動がずれる。
- multipart は他の形式を中で使うが、registry は multipart を含むので、multipart が registry を require すると循環する。

## 場所
- `mulay.dw.fmt.registry/format-id`、`mulay.dw.fmt.registry/read-named`、`mulay.dw.fmt.registry/write-valid`、
  `mulay.dw.fmt.registry/write-script-output`、`mulay.dw.fmt.registry/part-reader`、`mulay.dw.fmt.registry/part-writer`
- `mulay.dw.fmt.multipart/read`、`mulay.dw.fmt.multipart/read-at`
- `mulay.dw.fmt.props/pstr`、`mulay.dw.fmt.props/split-meta`
- `mulay.dw.fmt.dwread/as-type`
