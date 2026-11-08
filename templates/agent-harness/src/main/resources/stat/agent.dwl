%dw 2.0
// 統計的なモデルの 1 回分。llm.provider が stat のとき、agent-loop (agent.xml) が LLM の代わりに呼ぶ (stat.xml の stat-step)。
// Inference コネクタの tools-native-template と同じ形を返す:
//   {response: 答え} か {tools: [{id, type: "function", function: {name, arguments (JSON の文字列)}}]}
// ツールの手がかり (例文、trigger、引数の取り出し方、答えのひな形) は stat/hints.dwl。
//
// 問いから計画を立てる (plan): trigger に当たるツール、無ければ例文との TF-IDF のコサインが一番高いツール (threshold 以上)、
// それも無ければ必須の引数がすべて問いから形で取れるツール (「order X999」の X999 のように、番号だけで分かるもの)。
// 選んだツールの引数を slots で取り出し、ツールの parameters.required のうち取れなかったものを missing にする。
//   - このターンでまだツールを呼んでいない:
//       計画があって引数が揃っていれば、そのツールを呼ぶ。揃っていない・計画が無いときは、fallback のツール (search_docs) に
//       問いを渡す (「when will my order ship?」は注文の番号が無いので、まず文書を探す)。fallback も無ければ、
//       足りない引数を尋ねるか noAnswer。
//   - ツールを呼んだ後 (steps がある): 最後の結果から答えを作る。結果が "error: .." ならそのまま返す。
//       fallback が "no matching documents" なら、足りない引数があればそれを尋ね、無ければ noAnswer。
// ツールは 1 回の問いで 1 つだけ呼ぶ (結果を見て次のツールを選ぶことはしない)。
import rank from stat::text
import HINTS from stat::hints

var NO_DOCS = "no matching documents"

fun hint(name: String) = HINTS[name] default {}

// ひな形の {名前} を vals の値で置き換える
fun fill(tpl: String, vals: Object): String =
    (keysOf(vals) map ($ as String)) reduce ((k, acc = tpl) -> acc replace ("{" ++ k ++ "}") with ((vals[k] default "") as String))

fun answer(name: String, args: Object, result: String) = do {
    var a = hint(name).answer default "{result}"
    ---
    if (a is String) fill(a, args ++ {result: result}) else a(args, result) as String
}

fun slotValue(q: String, spec) =
    if (spec is String) q
    else ((q scan spec.pattern)[0][spec.group]) default null

fun coerce(v, schema) =
    if (v == null) null
    else if (["number", "integer"] contains (schema."type" default "")) v as Number
    else v

// 必須の引数がすべて、問いに当てた正規表現 (slots の pattern) で取れるか ("question" の引数は数えない)
fun slotsFound(t: String, q: String, fns: Object): Boolean = do {
    var req = fns[t].parameters.required default []
    var sl = hint(t).slots default {}
    ---
    (not isEmpty(req)) and (sizeOf(req filter ((r) -> (sl[r] != null) and (not (sl[r] is String)) and (slotValue(q, sl[r]) != null))) == sizeOf(req))
}

fun plan(q: String, fns: Object, threshold: Number) = do {
    var avail = (keysOf(fns) map ($ as String)) filter (HINTS[$] != null)
    var trig = (avail filter ((t) -> (hint(t).trigger != null) and (q contains (hint(t).trigger as Regex))))[0] default null
    var examples = flatten(avail map ((t) -> (hint(t).examples default []) map {key: t, text: $}))
    var best = if (isEmpty(examples)) null else rank(q, examples)[0]
    var bySlots = (avail filter ((t) -> slotsFound(t, q, fns)))[0] default null
    var name = trig default (if ((best != null) and (best.score >= threshold)) best.key else bySlots)
    ---
    if (name == null) null
    else do {
        var fn = fns[name]
        var props = fn.parameters.properties default {}
        var args = (hint(name).slots default {}) mapObject ((spec, p) -> {(p): coerce(slotValue(q, spec), props[p])})
        var have = args filterObject ($ != null)
        ---
        {name: name, args: have, missing: (fn.parameters.required default []) filter (have[$] == null), props: props}
    }
}

fun ask(p) = do {
    var m = p.missing[0] as String
    ---
    "Please tell me " ++ m ++ ": " ++ (p.props[m].description default m) ++ "."
}

fun call(name: String, args: Object, n: Number) =
    {tools: [{id: "stat_" ++ n, "type": "function", "function": {name: name, arguments: write(args, "application/json", {indent: false})}}]}

fun step(q: String, steps: Array, tools: Array, cfg: Object): Object = do {
    var fns = {(tools map {($."function".name as String): $."function"})}
    var fallback = ((keysOf(fns) map ($ as String)) filter (hint($).fallback default false))[0] default null
    var p = plan(q, fns, cfg.threshold)
    var ready = (p != null) and isEmpty(p.missing)
    ---
    if (isEmpty(steps))
        if (ready) call(p.name, p.args, 0)
        else if (fallback != null) call(fallback, {(keysOf(hint(fallback).slots default {query: "question"})[0] as String): q}, 0)
        else if (p != null) {response: ask(p)}
        else {response: cfg.noAnswer}
    else do {
        var last = steps[-1]
        var r = (last.result default "") as String
        ---
        if (r startsWith "error:") {response: r}
        else if ((last.tool == fallback) and (r == NO_DOCS))
            if ((p != null) and (not ready)) {response: ask(p)} else {response: cfg.noAnswer}
        else {response: answer(last.tool, last.arguments default {}, r)}
    }
}
