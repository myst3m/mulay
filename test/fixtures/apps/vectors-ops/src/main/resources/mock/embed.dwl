%dw 2.0
// 偽の Ollama の埋め込み。キーワードの出現数 (と定数 0.5) のベクトルなので、似た文は近くなる。
// /api/embed は {model, input: [..]} → {model, embeddings: [[..]]}、/api/embeddings は {model, prompt} → {embedding: [..]}
output application/json
var keys = ["order", "ship", "refund", "agent", "mule", "weather"]
fun vec(t) = (keys map ((k) -> sizeOf(lower(t default '') find k))) ++ [0.5]
---
if (payload.'input' is Array) {model: payload.model, embeddings: payload.'input' map vec($)}
else if (payload.'input' is String) {model: payload.model, embeddings: [vec(payload.'input')]}
else {embedding: vec(payload.prompt)}
