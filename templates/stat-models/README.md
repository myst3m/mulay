# stat-models

ニューラルネットを使わない統計的なモデルを、OpenAI などの API の形で出す Mule アプリ。
埋め込みの口 (`embed.hash512.stat`) と LLM の口 (`llm.tfidf.stat`) を別々のサービスとして置ける (`stat.serve` で選ぶ)。

- 計算は agent-harness の `stat/*.dwl` (このアプリの `src/main/resources/stat` はそこへの symlink。片方だけ直さない)。
  応答の形は `statsvc/api.dwl`。
- `stat.serve`: `embed` (埋め込みの口だけ)、`llm` (LLM の口だけ)、`both` (既定。手元の試験用)。
- 埋め込み (512 次元、言葉が同じ文どうしが近くなる。言い換えには弱い):
  OpenAI `POST /v1/embeddings`、Azure `POST /openai/deployments/<名前>/embeddings`、Ollama `POST /api/embeddings` と `POST /api/embed`、
  `GET /api/tags`。`dimensions` は 512 のときだけ受ける。`encoding_format: base64` でも数の配列で返す (OpenAI の Python SDK はそれで読める)。
- LLM: `POST /v1/chat/completions`。agent-harness の Inference コネクタが送る形 (user の中身が `{question, history, toolResults}` の JSON)
  と、普通の会話 (最後の user が問い、その後の tool のメッセージが結果) を読み、`stat::agent` の `step` に渡す。
  ツールは `stat/hints.dwl` に手がかりがあるもの (lookup_order、add、ask_agent、search_docs) だけが選ばれる。自由な文章は作らない。
  ストリーミングはしない (400)。
- 鍵: `api.key`。既定は資源の `keys.properties` で空 (空なら全部 401)。k8s では `keys.file=/secrets/self/api-key.properties`
  (資源に無い絶対パスはファイルシステムから読む。無ければ起動しない)。Bearer、`api-key` ヘッダ、`?api-key=`、パスの前置き `/k/<鍵>` が通る。
- 試験: `tools/mule-oracle/mule-oracle fill|mulay stat-models` (`test/fixtures/apps/stat-models` はこのディレクトリへの symlink)。
  100 件の埋め込みは、mulay が中央値 0.10 秒、実 Mule 4.11.3 が 0.20 秒 (2026-10-12)。
