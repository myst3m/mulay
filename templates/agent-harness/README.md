# agent-harness

A template for building an agent as a Mule app with standard connectors only.
It runs on both real Mule 4 and mulay; `scenario.scn` checks that the two behave the same.

- LLM: Inference connector (`ms-inference`, openai-compatible connection), `tools-native-template`. Without an LLM (`llm.url` empty, the default), a statistical model answers instead: it picks a tool by comparing the question with example questions and fills the answer into a template (see [Statistical model](#statistical-model)). It needs no API key, GPU or network.
- Tools: flows in this app (`tool-<name>`), plus tools on an MCP server called through the MCP client.
- Agent-to-agent: the A2A connector. The agent is exposed at `/agent` (card at `/agent/.well-known/agent-card.json`), and the `ask_agent` tool sends questions to another agent.
- Input checks: the Validation module (`validation:*`).
- A SOAP backend: the Web Service Consumer (`wsc`). The `lookup_order` tool asks an order system described by `wsdl/orders.wsdl`; a SOAP Fault from it becomes the tool result `error: <faultstring>`.
- Documents (RAG): the Vectors connector (`ms-vectors`). Documents are added, listed, searched and deleted through a separate admin MCP server at `/admin/mcp` (key required); the `search_docs` tool returns the passages closest to a query. Embeddings are statistical by default (no model needed).
- Conversation history: Object Store, keyed by the conversation key. `/chat`'s `sessionId` and A2A's `contextId` are the same key, so one conversation can move between the two entry points. It keeps the last `agent.historyMax` messages, at most `agent.historyMaxChars` characters in total, is persistent, and expires after `store.ttlHours`. With `agent.summarize=true` and an LLM, the messages that fall out are summarized instead of dropped (see [History](#history)).

```bash
mulay run templates/agent-harness            # port 8081. No LLM: the statistical model answers
curl -s localhost:8081/chat -H 'Content-Type: application/json' -d '{"message":"what is 2 + 3?","sessionId":"s1"}'
# → {"sessionId": "s1", "answer": "2 + 3 = 5", "steps": [{"tool": "add", "arguments": {"a": 2, "b": 3}, "result": "5"}]}
curl -s localhost:8081/chat -H 'Content-Type: application/json' -d '{"message":"注文 B200 の状況を教えて","sessionId":"s2"}'
# → {"sessionId": "s2", "answer": "Order B200 is packing.", "steps": [{"tool": "lookup_order", "arguments": {"id": "B200"}, ...}]}

# Over A2A (JSON-RPC message/send; message/stream for SSE progress). contextId = the same conversation as sessionId
curl -s localhost:8081/agent -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"message/send","params":{"message":{"kind":"message","role":"user","messageId":"u-1","parts":[{"kind":"text","text":"hello"}]}}}'

# A real LLM (any OpenAI-compatible endpoint). Setting llm.url switches from the statistical model to the LLM
mulay run templates/agent-harness llm.url=https://api.openai.com/v1 llm.model=gpt-4o-mini llm.key=$OPENAI_API_KEY

# The scripted mock LLM the test scenario uses (mock-llm.xml)
mulay run templates/agent-harness mockLlm.state=started llm.url=http://localhost:8081/mock-llm/v1 llm.model=mock-model llm.key=sk-mock
```

## How it works (src/main/mule/agent.xml)

1. `POST /chat {"message", "sessionId"}`. `validation:all` checks that `message` is not blank and that `sessionId` is 1 to 64 of `[A-Za-z0-9_.-]` (it becomes the Object Store key). All failures come back together as 400 `{error, description, problems: [..]}`.
2. `tool-catalog` builds the tool list. It combines `tools/local-tools.dwl` with the MCP server's `list-tools`, mapped into OpenAI's `tools` shape.
3. `agent-loop` calls `llm-step` at most `agent.maxSteps` times. `llm-step` asks the LLM (`tools-native-template`), or the statistical model when there is no LLM:
   - When the LLM returns `tools` (tool_calls), `run-tool` runs each one and appends the result to `steps`.
   - When it returns `response`, that is the answer.
   - When there is still no answer after the limit, `AGENT:MAX_STEPS` (422).
4. The question and the answer are added to the history (`save-history`). The reply is `{sessionId, answer, steps}`.

The A2A entry point (`a2a.xml`) runs the same `converse` sub-flow. It takes the message's text as the question and replies with a `completed` Task.
The answer is both the status message and an artifact. When it fails (for example on `MAX_STEPS` or an LLM error), it replies with a `failed` Task.
Task records live in the `A2aTasks` Object Store (`<a2a:history taskRepositoryObjectStore>`), so `tasks/get` works and survives restarts.
`a2a-authorize` (the authorization listener) lets everyone read them; add your checks there before exposing the agent.
`ask_agent` sends `peer-<conversation key>` as `contextId`, so repeated questions from one conversation stay in one context on the peer.

Long-running work over A2A:
- `message/stream` (SSE): the agent sends `working` status updates when it receives the task and each time it calls a tool. Then it sends the answer as an artifact and closes with `completed`; on errors it closes with `failed`.
- Push notifications: `message/send` with `configuration.pushNotificationConfig` returns a `submitted` Task right away. The finished Task is then POSTed to the URL, with `X-A2A-Notification-Token` when a token was given. `a2a-push-config` accepts every http/https URL; restrict it before exposing the agent. mulay refuses to deliver to URLs that resolve to loopback, link-local or private addresses unless `mulay.a2a.allowPrivatePushUrls=true` (the test scenario sets it for `/mock-hook`).

`tools-native-template` only returns tool_calls; it does not run the tools.
Its messages can carry only `role` and `content`, so a `tool` message cannot be sent.
For both reasons, the tool results are passed to the next call in the JSON of `data`: `{question, history, toolResults}`.
If a tool fails, the agent does not stop: the result becomes `error: <description>` and goes back to the LLM.
Tools check their arguments the same way: `tool-lookup_order` uses `validation:matches-regex` on the order id, so a bad id from the LLM becomes `error: invalid order id: ..` and the LLM can try again.
`converse` itself refuses an empty question (`VALIDATION:BLANK_STRING`), which turns an A2A message without text into a `failed` Task.

## Statistical model

When no LLM is given (`llm.url` is empty and `llm.provider` is `auto`, the defaults), `agent-loop` calls `stat-step` (`stat.xml`) instead of the Inference connector.
It returns the same shape as `tools-native-template` (`{tools: [tool_calls]}` or `{response}`), so tools, history and A2A work the same way.
It is deterministic, runs inside the app and needs no API key, GPU or network, which makes it a usable default for a deployment that has no LLM yet.

How it decides (`stat/agent.dwl`, with per-tool hints in `stat/hints.dwl`):

1. Pick a tool: the first tool whose `trigger` regex matches (`2 + 3`, `ask: ..`); otherwise the tool whose `examples` are closest to the question (TF-IDF cosine ≥ `stat.threshold`); otherwise a tool whose required arguments can all be read from the question by their patterns (`order X999`).
2. Read the arguments from the question with the `slots` patterns (an order id like `A100`, the two numbers of a sum, the text after `ask:`).
3. Call the tool, then fill the result into the tool's `answer` template (`Order A100 is shipped (ETA 2026-10-12).`, `2 + 3 = 5`). A result starting with `error:` is returned as is.
4. If no tool fits, or a required argument is missing, search the documents (`search_docs`) with the whole question and answer with the passages it finds.
   If nothing is found either, ask for the missing argument (`Please tell me id: ..`) or answer `stat.noAnswer`.

Limits, by design:

- It calls at most one tool per question and does not chain tools.
- It does not write free text: answers are tool results in templates or passages from the documents.
- It matches words, not meaning. Add `examples` in both languages your users write in. Japanese is compared on kanji and katakana (hiragana is ignored).
- `agent.summarize` needs an LLM; with the statistical model, messages that fall out of the history are dropped.
- A tool without an entry in `stat/hints.dwl` is never picked by the statistical model (an LLM still sees it).
- `ask_agent` is picked only by its trigger (`ask: <text>`, `他のエージェントに聞いて: <text>`), and only the text after it is sent. The default peer is this app itself, so this keeps it from forwarding the same request to itself forever.

`test/fixtures/apps/agent-harness-stat` checks the statistical model against real Mule (the same app with the default settings).

## History

Every LLM call gets the whole stored history in `data.history` (the Inference connector sends only a system and a user message, so the turns are JSON inside `data`, not chat messages). Tool results are kept only within one turn; the history keeps the question and the final answer.

`save-history` (in `agent.xml`) trims the history after each turn:

- It keeps the newest messages that fit in both `agent.historyMax` (count) and `agent.historyMaxChars` (sum of the `content` lengths). Messages are dropped whole, oldest first, and an answer whose question was dropped goes with it. A single turn longer than `agent.historyMaxChars` leaves the history empty.
- `agent.summarize` (default `false`): when `true`, the dropped messages and the previous summary are sent to the LLM (`agent-define-prompt-template` with `agent.summaryPrompt`) and the result is kept as the first history item, `{role: "summary", content}`, cut to `agent.summaryMaxChars`. The summary is not counted in `historyMax` / `historyMaxChars`, so the history sent to the LLM is at most `historyMaxChars + summaryMaxChars` characters.
- Cost: once the history is full, every turn makes one more LLM call (the summary), before the reply is returned.
- If the summary call fails, the turn still succeeds: the messages are dropped and the previous summary is kept (a WARN is logged).

`test/fixtures/apps/agent-harness-summary` checks the summary mode against real Mule (the same app with `agent.summarize=true`).

## Documents (src/main/mule/rag.xml, admin.xml, stat.xml)

Documents are managed through a second MCP server, `docs-admin` at `admin.path` (default `/admin/mcp`).
It is separate from the agent's own `/mcp` on purpose: the tools on `/mcp` are handed to the LLM, so a delete tool there could be triggered by text in a conversation or in a document.
The path prefix is separate too, so a gateway can put stricter policies on `/admin/*` only.

Every request needs `Authorization: Bearer <admin.key>`. `admin.key` is empty by default, which keeps the admin server closed (403 on connect, an error on every tool).
A wrong or missing key gets 401 on connect, and each tool call checks the key again.

```bash
mulay run templates/agent-harness admin.key=$DOCS_ADMIN_KEY
claude mcp add --transport http docs http://localhost:8081/admin/mcp --header "Authorization: Bearer $DOCS_ADMIN_KEY"
# → in Claude Code: "add this README as source=faq", "show the documents", "search for refunds"
curl -s localhost:8081/chat -H 'Content-Type: application/json' -d '{"message":"docs: when will my order ship?","sessionId":"s9"}'
```

| Tool | Arguments | What it does |
|---|---|---|
| `add_document` | `text`, `id` (optional), `source` (optional) | Splits (`docs.chunkSize` / `docs.chunkOverlap` characters), embeds and stores a document. The same `id` replaces the old passages. Returns `{id, chunks, replaced}` |
| `delete_document` | `id` | Deletes a document and its passages. Returns `{id, deleted}` |
| `list_documents` | | `[{id, source, chars, chunks, added, model}]`, sorted by id |
| `search_documents` | `query`, `maxResults` (optional) | The same search as `search_docs`, with scores: `[{score, id, source, text}]` |
| `reindex_documents` | | Embeds every document again from its saved text with the current `embed.model` |

- Passages carry `source` and `docId` as metadata. The original text and the counts are kept in the `DocsIndex` Object Store, which `list_documents` and `reindex_documents` read.
- `search_docs` (the agent's tool) and `search_documents` embed the query and run `query`: at most `docs.maxResults` passages with score ≥ `docs.minScore`.
  The score is LangChain4j's relevance score, (cosine + 1) / 2, so an unrelated passage scores 0.5. The default 0.6 (cosine 0.2) suits the statistical embeddings; for a neural model start around 0.75.
- Embeddings come from an Ollama-compatible `/api/embeddings` at `embed.url` (`embed.model`). The default is the statistical embedder in `stat.xml` (`stat/text.dwl`), which needs no model:
  - English words (lower-cased; a trailing `s` dropped from words of four letters or more) and overlapping two-character pieces of kanji, katakana and full-width runs are hashed into 512 dimensions.
  - Hiragana runs (particles and endings) are dropped, so "発送はいつ" matches "…2日以内に発送します" on 発送. Text written only in hiragana matches nothing.
  - Passages that share words come close; paraphrases with no shared words do not. For those, use a real model: `embed.url=http://localhost:11434 embed.model=nomic-embed-text` (Ollama).
- Each embedding model gets its own store (`docs.store`, default `docs-${embed.model}`), because vectors from different models cannot be compared. After changing `embed.model`, run `reindex_documents`.
- Documents are stored in the `docs.dir` directory (the Vectors `ephemeral-file` store, one JSON file per store). A relative `docs.dir` is relative to the process's current directory (`add_document` creates it through the `DocsDir` file config with `workingDir="."`, the same base the store uses).
- On CloudHub and other platforms where the disk does not survive a redeploy, the passages are lost but `DocsIndex` (a persistent Object Store) is not: `list_documents` still shows the documents, and `reindex_documents` rebuilds the passages. For a production vector database, switch the `store-config` connection (pgvector, OpenSearch, ...; only `ephemeral-file` runs on mulay today).
- The real Mule app needs langchain4j in `additionalPluginDependencies` (already in `pom.xml`).

## Customizing

| What | Where |
|---|---|
| Add a tool (implemented in a flow) | A definition in `src/main/resources/tools/local-tools.dwl` and a `tool-<name>` flow in `tools.xml` |
| Documents for search_docs | The admin MCP server (`/admin/mcp`, `admin.key`); `docs.*` and `embed.*` in `config.yaml` |
| Order system (SOAP) for lookup_order | `wsdl/orders.wsdl` and `orders.url` in `config.yaml` (the default is a mock in `mock-llm.xml`; `mockOrders.state=stopped` stops it) |
| Check inputs or tool arguments | `validation:*` operations (e.g. `is-email`, `is-number`, `matches-regex`, `all`); failures are `VALIDATION:*` errors. Inside DataWeave, `Validation::isEmail(..)` and friends return Boolean |
| Add a tool (exposed over MCP) | `mcp:tool-listener` in `tools.xml`. To use another MCP server, set `mcp.url` / `mcp.path` |
| Prompt, step limit, history length (`historyMax`, `historyMaxChars`), summary (`summarize`, `summaryMaxChars`, `summaryPrompt`) | `agent.*` in `config.yaml` |
| Persistence and expiry of history and A2A tasks | `store.*` in `config.yaml` |
| A2A card, peer agent | `a2a.*` in `config.yaml` (`a2a.peerUrl` defaults to this app itself) |
| LLM endpoint | `llm.url` / `llm.model` / `llm.key` (put the key in a secure property in production). An empty `llm.url` (the default) means the statistical model; `llm.provider` (`auto`, `stat`, `openai`) forces one |
| What the statistical model can do | `src/main/resources/stat/hints.dwl` (examples, triggers, argument patterns and answer templates per tool), `stat.threshold`, `stat.noAnswer` |
| The mock LLM (tests) | `mockLlm.state=started` and `llm.url` pointing at `/mock-llm/v1`. Delete `mock-llm.xml` and `src/main/resources/mock/` when you no longer need it |
| Test-only endpoints | `testHooks.state=started` turns on `/mock-llm/last` (what was sent to the LLM), `/mock-hook` (A2A push notifications) and `DELETE /test/docs` (deletes every document). They are off by default because they expose requests or delete data; the test scenarios turn them on |

Stores are persistent by default (`store.persistent`). Set `store.persistent=false` for throwaway runs; the test scenario does this.
