%dw 2.0
// 統計的なモデル (stat/agent.dwl) がツールを選び、引数を取り出し、答えを作るための手がかり。
// キーはツールの名前 (このアプリのフローのツールも、MCP サーバーのツールも同じ)。ここに無いツールは、統計的なモデルからは選ばれない
// (LLM を使うときは、tools の説明だけで選ばれる)。
//
//   examples: そのツールを使う問いの例 (英語と日本語)。問いとの TF-IDF のコサインで比べる (stat/text.dwl の rank)
//   trigger:  当てはまれば例文より先にそのツールを選ぶ正規表現。数式や「ask:」のように、形で分かるもの
//   slots:    引数ごとの取り出し方。{pattern, group} は問いに pattern を当てた group 番目、"question" は問いの全体
//   answer:   答えのひな形。文字列なら {result} がツールの結果、{引数名} が渡した引数。関数なら (引数, 結果) -> 答え
//   fallback: true なら、どのツールにも当たらないときにこのツールへ問いを渡す (文書の検索)
//
// ask_agent は trigger だけで選ぶ (例文にも fallback にもしない)。相手 (a2a.peerUrl) の既定はこのアプリ自身なので、
// 「ask:」を外した部分だけを渡さないと、自分に同じ依頼を送り続けてしまう。

var ORDER_ID = /(?:^|[^A-Za-z0-9])([A-Z][0-9]{3})(?:[^A-Za-z0-9]|$)/

var SUM = /(-?[0-9]+(?:[.][0-9]+)?) *(?:[+]|plus|足す|たす) *(-?[0-9]+(?:[.][0-9]+)?)/

var ASK = /^ *(?:[Aa]sk(?: the other agent)?|他のエージェントに聞いて) *[:：] *(.+)$/

var HINTS = {
    lookup_order: {
        examples: ["where is my order", "order status", "check my order", "track an order", "has my order shipped",
                   "注文の状況を教えて", "注文はどうなっていますか", "注文の状態", "注文を調べて", "配送状況"],
        slots: {id: {pattern: ORDER_ID, group: 1}},
        answer: (a, r) -> do {
            var o = read(r, "application/json")
            ---
            "Order " ++ a.id ++ " is " ++ o.status ++ (if (o.eta != null) " (ETA " ++ o.eta ++ ")" else "") ++ "."
        }
    },
    add: {
        trigger: SUM,
        slots: {a: {pattern: SUM, group: 1}, b: {pattern: SUM, group: 2}},
        answer: "{a} + {b} = {result}"
    },
    ask_agent: {
        trigger: ASK,
        slots: {text: {pattern: ASK, group: 1}},
        answer: "The other agent says: {result}"
    },
    search_docs: {
        fallback: true,
        slots: {query: "question"},
        answer: "{result}"
    }
}
