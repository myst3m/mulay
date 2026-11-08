%dw 2.0
// stat-models の応答を組み立てる (計算は agent-harness の stat/text.dwl と stat/agent.dwl をそのまま使う)。
// どの関数も {status, body} を返す。body は JSON にする値。
//
//   埋め込み (embed.hash512.stat): stat::text の embed (単語と文字の 2 文字ずつをハッシュで 512 次元に振り分けたベクトル)
//     OpenAI   POST /v1/embeddings                         {input, model, dimensions} → {object, data, model, usage}
//     Azure    POST /openai/deployments/<名前>/embeddings   同じ形 (model は deployment の名前)
//     Ollama   POST /api/embeddings {model, prompt} → {embedding}、POST /api/embed {model, input} → {model, embeddings, ..}
//   LLM (llm.tfidf.stat): stat::agent の step (問いを例文と比べてツールを選び、ひな形で答える)
//     POST /v1/chat/completions。agent-harness の Inference コネクタが送る形 (user の中身が {question, history, toolResults} の JSON)
//     と、普通の会話 (最後の user が問い、その後の tool のメッセージが結果) の両方を読む。ツールの手がかりは stat/hints.dwl にある
//     ものだけ (それ以外のツールは選ばれない)。ストリーミングはしない。
import embed, tokens from stat::text
import step from stat::agent
import try from dw::Runtime

var DIMS_MSG = "This model does not support specifying dimensions."

fun err(kind: String, status: Number, msg: String) =
    if (kind == "ollama") {error: msg}
    else if (kind == "azure") {error: {code: status as String, message: msg}}
    else {error: {message: msg, "type": if (status < 500) "invalid_request_error" else "server_error", param: null, code: null}}

fun fail(kind: String, status: Number, msg: String) = {status: status, body: err(kind, status, msg)}

fun ok(body) = {status: 200, body: body}

fun count(xs: Array) = sum(xs) default 0

// ---- 埋め込み ----

fun inputsOf(x) = if (x is String) [x] else if (x is Array) x else null

fun allStrings(xs: Array) = isEmpty(xs filter (not ($ is String)))

fun openaiEmbed(body, model: String, dims: Number, kind: String) = do {
    var ins = if (body is Object) inputsOf(body."input") else null
    ---
    if (not (body is Object)) fail(kind, 400, "We could not parse the JSON body of your request.")
    else if (body."input" == null) fail(kind, 400, "'input' is a required property")
    else if ((ins == null) or (not allStrings(ins))) fail(kind, 400, "'input' must be a string or an array of strings")
    else if ((body.dimensions != null) and (body.dimensions != dims)) fail(kind, 400, DIMS_MSG)
    else do {
        var n = count(ins map sizeOf(tokens($)))
        ---
        ok({object: "list",
            data: ins map ((t, i) -> {object: "embedding", index: i, embedding: embed(t)}),
            model: model,
            usage: {prompt_tokens: n, total_tokens: n}})
    }
}

fun ollamaLegacy(body) =
    if (not (body is Object)) fail("ollama", 400, "invalid request body")
    else if ((body.model default "") == "") fail("ollama", 400, "model is required")
    else ok({embedding: if ((body.prompt default "") == "") [] else embed(body.prompt as String)})

fun ollamaEmbed(body, dims: Number) = do {
    var ins = if (body is Object) (if (body."input" == null) [] else inputsOf(body."input")) else null
    ---
    if (not (body is Object)) fail("ollama", 400, "invalid request body")
    else if ((body.model default "") == "") fail("ollama", 400, "model is required")
    else if ((ins == null) or (not allStrings(ins))) fail("ollama", 400, "invalid input type")
    else if ((body.dimensions != null) and (body.dimensions != dims)) fail("ollama", 400, DIMS_MSG)
    else ok({model: body.model, embeddings: ins map embed($), total_duration: 0, load_duration: 0,
             prompt_eval_count: count(ins map sizeOf(tokens($)))})
}

fun ollamaTags() = ok({models: [{name: "hash512:latest", model: "hash512:latest", modified_at: "2026-10-12T00:00:00Z", size: 0,
    digest: "", details: {parent_model: "", format: "dwl", family: "hash", families: ["hash"], parameter_size: "0", quantization_level: ""}}]})

// ---- LLM ----

fun textOf(c) =
    if (c is String) c
    else if (c is Array) ((c filter ($."type" == "text")) map ($.text default "")) joinBy "\n"
    else ""

// 普通の会話の、最後の user の後の tool のメッセージを、stat::agent の steps ({tool, arguments, result}) にする
fun stepsOf(msgs: Array, from: Number) = do {
    var calls = flatten((msgs filter ($.role == "assistant")) map ($.tool_calls default []))
    var tools = msgs[from + 1 to -1] default []
    ---
    (tools filter ($.role == "tool")) map ((t) -> do {
        var c = (calls filter ($.id == t.tool_call_id))[0] default {}
        ---
        {tool: c."function".name default "", arguments: try(() -> read(c."function".arguments default "{}", "application/json")).result default {},
         result: textOf(t.content)}
    })
}

fun chat(body, cfg: Object, id: String, created: Number) =
    if (not (body is Object)) fail("openai", 400, "We could not parse the JSON body of your request.")
    else if (body.stream default false) fail("openai", 400, "stream is not supported by llm.tfidf.stat")
    else do {
        var msgs = body.messages default []
        var last = max((msgs map ((m, i) -> if (m.role == "user") i else -1))) default -1
        var content = if (last >= 0) textOf(msgs[last].content) else ""
        var data = try(() -> read(content, "application/json")).result default null
        var harness = (data is Object) and (data.question != null)
        var q = if (harness) data.question as String else content
        var steps = if (harness) (data.toolResults default []) else stepsOf(msgs, last)
        var tools = if (body.tool_choice == "none") [] else ((body.tools default []) filter ($."type" == "function"))
        var r = step(q, steps, tools, cfg)
        var calls = r.tools default []
        ---
        if (last < 0) fail("openai", 400, "messages must contain a user message")
        else ok({id: id, object: "chat.completion", created: created, model: body.model default "tfidf",
                 choices: [{index: 0,
                            message: {role: "assistant", content: if (isEmpty(calls)) r.response else null, (tool_calls: calls) if (not isEmpty(calls))},
                            finish_reason: if (isEmpty(calls)) "stop" else "tool_calls"}],
                 usage: {prompt_tokens: sizeOf(tokens(q)), completion_tokens: 0, total_tokens: sizeOf(tokens(q))}})
    }

fun models(serve: String) = ok({object: "list", data:
    (if (serve != "llm") [{id: "hash512", object: "model", created: 0, owned_by: "stat"}] else []) ++
    (if (serve != "embed") [{id: "tfidf", object: "model", created: 0, owned_by: "stat"}] else [])})

fun describe(serve: String) = ok({
    name: if (serve == "embed") "embed.hash512.stat" else if (serve == "llm") "llm.tfidf.stat" else "stat-models",
    what: "Statistical models without any neural network, served by a Mule app (mulay templates/stat-models).",
    endpoints: (if (serve != "llm") ["POST /v1/embeddings", "POST /openai/deployments/{deployment}/embeddings", "POST /api/embeddings", "POST /api/embed", "GET /api/tags"] else []) ++
               (if (serve != "embed") ["POST /v1/chat/completions"] else []) ++ ["GET /v1/models"],
    auth: "Authorization: Bearer <key>, api-key: <key>, ?api-key=<key>, or the base URL https://<host>/k/<key>",
    source: "mulay templates/stat-models (stat/*.dwl shared with templates/agent-harness)"})
