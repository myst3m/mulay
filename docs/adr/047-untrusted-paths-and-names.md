# 047 — 外から来たパスと名前で、意図しないファイルや要求の構造に届かせない

状態: **採用** (2026-10-04 File と Salesforce、2026-10-08 jmx、2026-10-09 http:request の OAuth)

## 決定
- **File: NUL を含むパスは失敗にする**。read などは MULE:UNKNOWN "Nul character not allowed: ..."、write は FILE:ILLEGAL_PATH
  (実 Mule の Java の Paths.get と同じ。file-ops に記録)。dw の readUrl も資源が無いのと同じ失敗にする。(1e214f8)
- **File: write の CREATE_NEW は、有無の確かめと作成を 1 回の open (lib/fs の `create-new`) でする**。(ce07735)
- **Salesforce: XML の名前でないフィールド名は SOAP の本文に書かずに SALESFORCE:INVALID_INPUT で断る**。送る前に `records-err` で
  確かめる (create / update / upsert / merge / findDuplicates / platform event / streaming channel)。Salesforce の API 名は英字で
  始まり、英数字と `_` (と関係の `.`) だけ。(0d21bd7)
- **jmx: fileName が絶対パスか ".." を含むときは読まない** (`{"error":"Invalid log file name: .."}`)。実モジュールは logDir の外も読む
  (docs/compat/deviations.md)。(efa6f81)
- **http:request の OAuth: トークンと secret はログにもエラーにも出さない** (docs/connectors.md にも記載)。(e1a65dd)

## 理由
- NUL: C の open に渡すと NUL で切れ、付け足した拡張子などを外した別のファイルを開く。
  `path="#['data/' ++ attributes.queryParams.id ++ '.json']"` に `?id=../../etc/passwd%00` で /etc/passwd を読めた。
- CREATE_NEW: stat で確かめてから書いていたので、その間に同じ名前の symlink を置くとリンク先を上書きできた。実コネクタ
  (Files.newOutputStream の CREATE_NEW) も確かめと作成を 1 回で行う。
- Salesforce: フィールド名はタグ名にそのまま書くので、データのキー (`"Name>x</urn1:Name></urn:sObjects><urn:sObjects>.."`) で
  指定した type 以外の sObject を同じ要求に差し込めた。

## 場所
- `mulay.conn.file/path-arg`、`mulay.conn.file/write-path-arg`、`mulay.conn.file/run-write`、`mulay.lib.fs/create-new`
- `mulay.conn.sf_core/field-name?`、`mulay.conn.sf_core/records-err`、`mulay.conn.sf_core/sobject-xml`
- `mulay.conn.jmx/escapes?`
- `mulay.conn.http/fetch-token`、`mulay.conn.http/oauth-token`

## 関連
- ADR 016 (lib/fs と lib/res の安全)
