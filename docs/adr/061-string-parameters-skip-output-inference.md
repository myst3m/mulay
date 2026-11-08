# 061 — String の引数は出力形式を推論せず、DW の String をそのまま Java の String として使う

状態: **採用** (2026-10-12 c19ae1e (raise-error の description)、6868073 (MCP の応答の項目))

## 決定
- 実 Mule が Java の String として受け取る引数は `mulay.rt.engine/eval-string-pval` で評価する。DW の String の結果はそのまま
  使い、出力の mime を推論して書き直さない。String でない値は `eval-pval` と同じ (推論する)。
- 対象: raise-error の description、MCP のサーバーの応答の項目 (text など。`mulay.conn.mcp/srv-attr`)、
  AI 系の prompt / template / instructions / data (docs/connectors.md)。
- 推論しないので、JSON の payload を使った式 (`#[write(payload, ..)]`、`#['id=' ++ payload.id]`) に引用符が付かず、入力の mime が
  混ざっても「Unable to infer a output media type ..」で失敗しない。

## 理由
- 実 Mule 4.11.3 は式の値を Java の String にする (DW の String はそのまま)。推論していたときは、JSON の payload を使う式が JSON の
  文字列として書き直され、引用符付きで返っていた (6868073、c19ae1e)。期待値は実 Mule で取った (test/fixtures/apps/mcp-tools)。

## 場所
- `mulay.rt.engine`: `eval-string-pval`、`eval-pval`、raise-error の実行
- `mulay.conn.mcp`: `srv-attr`
