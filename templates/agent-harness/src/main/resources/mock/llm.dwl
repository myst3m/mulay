%dw 2.0
// 偽の LLM の応答 (OpenAI の chat/completions の形)。payload は受けた要求。
// 最後のメッセージ (agent.xml が渡す data) で筋書きを選ぶ:
//   dropped が有る (履歴の要約の要求) → "Earlier: <前の要約>; <捨てた問い>; .." と答える ("failsum" を含むと mock-llm.xml が 500)
//   "loop" を含む → 毎回 lookup_order を呼ばせる (maxSteps の確認)
//   "boom"       → (mock-llm.xml が 500 を返す)
//   toolResults が有る → 結果を並べて答える
//   "<n> + <m>"   → MCP の add を呼ばせる
//   "order <id>" → lookup_order を呼ばせる
//   "ask: <text>" → ask_agent (A2A) を呼ばせる
//   "docs: <text>" → search_docs (文書の検索) を呼ばせる (ほかの言葉より先に見る)
//   それ以外      → 履歴の長さ (と、履歴に要約があれば [summary: ..]) を添えて答える
output application/json
var d = read(payload.messages[-1].content default '{}', 'application/json')
var q = d.question default ''
var results = d.toolResults default []
var sum = (q scan /(\d+)\s*\+\s*(\d+)/)[0] default null
var ord = (q scan /order\s+(\w+)/)[0] default null
var ask = (q scan /ask:\s*(.+)/)[0] default null
var docs = (q scan /docs:\s*(.+)/)[0] default null
var summary = ((d.history default []) filter ($.role == 'summary'))[0].content default null
fun usage() = {prompt_tokens: 10, completion_tokens: 5, total_tokens: 15}
fun reply(text) = {id: 'mock-1', object: 'chat.completion', model: payload.model, choices: [{index: 0, message: {role: 'assistant', content: text}, finish_reason: 'stop'}], usage: usage()}
fun callTool(name, args) = {id: 'mock-2', object: 'chat.completion', model: payload.model, choices: [{index: 0, message: {role: 'assistant', content: null, tool_calls: [{id: 'call_' ++ sizeOf(results), 'type': 'function', 'function': {name: name, arguments: write(args, 'application/json', {indent: false})}}]}, finish_reason: 'tool_calls'}], usage: usage()}
---
if (d.dropped != null) reply('Earlier: ' ++ (((if (d.summary != null) [d.summary replace /^Earlier: / with ''] else []) ++ ((d.dropped filter ($.role == 'user')) map $.content)) joinBy '; '))
else if (q contains 'loop') callTool('lookup_order', {id: 'A100'})
else if (!isEmpty(results)) reply('Tool results: ' ++ ((results map ($.tool ++ ' -> ' ++ $.result)) joinBy '; '))
else if (docs != null) callTool('search_docs', {query: docs[1]})
else if (sum != null) callTool('add', {a: sum[1] as Number, b: sum[2] as Number})
else if (ord != null) callTool('lookup_order', {id: ord[1]})
else if (ask != null) callTool('ask_agent', {text: ask[1]})
else reply('You said: ' ++ q ++ ' (history: ' ++ sizeOf(d.history default []) ++ ' messages, tools: ' ++ ((payload.tools default []) map $.function.name joinBy ',') ++ ')'
           ++ (if (summary != null) ' [summary: ' ++ summary ++ ']' else ''))
