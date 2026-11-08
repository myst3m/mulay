%dw 2.0
// このアプリのフローで実装するツール (OpenAI の tools の形)。name が N のツールは tools.xml の tool-N のフローが実行する。
// MCP サーバーのツールはここに書かない (agent.xml の tool-catalog が list-tools から足す)。
output application/json
---
[
  {
    "type": "function",
    "function": {
      name: "lookup_order",
      description: "Looks up an order by its id and returns its status.",
      parameters: {
        "type": "object",
        properties: { id: { "type": "string", description: "Order id: one capital letter and three digits, e.g. A100" } },
        required: ["id"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      name: "search_docs",
      description: "Searches the knowledge base (documents added through the admin MCP server) and returns the passages closest to the query.",
      parameters: {
        "type": "object",
        properties: { query: { "type": "string", description: "What to look for" } },
        required: ["query"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      name: "ask_agent",
      description: "Asks another agent (over A2A) and returns its answer.",
      parameters: {
        "type": "object",
        properties: { text: { "type": "string", description: "What to ask the other agent" } },
        required: ["text"]
      }
    }
  }
]
