%dw 2.0
// 統計的なテキストの処理 (LLM も埋め込みのモデルも使わない)。agent-harness の stat-embed と stat-step が使う。
//
// tokens(s): 英数字の並びは小文字の単語にする (4 文字以上で s で終わる語は、ss で終わるものを除いて末尾の s を落とす:
//   orders → order)。漢字・カタカナ・全角英数は、それぞれの並びを重なりのある 2 文字ずつにする (1 文字だけならその 1 文字)。
//   ひらがなの並びは捨てる (助詞や語尾が大半で、残すと「発送はいつ」の「送は」「はい」のような雑音になる。
//   そのため、ひらがなだけの文は何にも近くならない)。それ以外の文字 (空白・記号) は区切り。STOP の英語は捨てる。
// embed(s): tokens をハッシュで DIMS 次元に振り分けたベクトル (符号付き、出現数の平方根の重み) を L2 で正規化し、
//   小数 6 桁に丸めたもの。IDF を使わないので、文書を足しても前に作ったベクトルは変わらない。
//   言葉が同じ文どうしは近くなるが、言い換え (意味だけが近い文) は近くならない。
// rank(q, examples): 例文の組 [{key, text}] を、問い q との TF-IDF のコサイン類似度で並べた [{key, score}]
//   (key ごとに一番近い例文の値、大きい順)。IDF は sqrt((例文の数 + 1) / (その語を含む例文の数 + 1))。
import charCode from dw::core::Strings

var DIMS = 512

// 英数字、ひらがな、カタカナ (長音の ー を含む)、漢字、全角英数のそれぞれの並び
var RUN = /[A-Za-z0-9]+|[\u3041-\u309f]+|[\u30a0-\u30ff]+|[\u3400-\u9fff\uf900-\ufaff]+|[\uff10-\uff19\uff21-\uff3a\uff41-\uff5a]+/

// 意味の薄い英語 (機能語)
var STOP = ["a", "an", "the", "is", "are", "am", "be", "was", "were", "do", "does", "did", "to", "of", "for", "in", "on",
            "at", "by", "with", "and", "or", "it", "this", "that", "i", "me", "my", "you", "your", "we", "our", "please",
            "can", "could", "would", "will", "what", "how", "tell", "about"]

fun stem(w: String): String = if (sizeOf(w) >= 4 and (w endsWith "s") and not (w endsWith "ss")) w[0 to -2] else w

fun tokens(s: String): Array<String> =
    flatten((s scan RUN) map ((m) -> do {
        var w = m[0]
        var parts = if (w matches /[A-Za-z0-9]+/) [lower(w)]
                    else if (w matches /[\u3041-\u309f]+/) []
                    else if (sizeOf(w) == 1) [w]
                    else (0 to sizeOf(w) - 2) map ((i) -> w[i to i + 1])
        ---
        (parts filter (not (STOP contains $))) map stem($)
    }))

// 31 倍して足していく文字列のハッシュ (2147483647 で割った余り)
fun hash(t: String): Number = (t splitBy "") reduce ((c, acc = 7) -> (acc * 31 + charCode(c)) mod 2147483647)

fun embed(s: String): Array<Number> = do {
    var cells = (tokens(s) groupBy $) pluck ((occ, tok) -> do {
        var h = hash(tok as String)
        ---
        {b: (floor(h / 2) mod DIMS) as String, w: (if ((h mod 2) == 0) 1 else -1) * sqrt(sizeOf(occ))}
    })
    var byB = cells groupBy $.b
    var raw = (0 to DIMS - 1) map ((i) -> sum((byB[i as String] default []) map $.w))
    var norm = sqrt(sum(raw map ($ * $)))
    ---
    if (norm == 0) raw else raw map (round($ / norm * 1000000) / 1000000)
}

// 語ごとの重み (出現数の平方根 × IDF)
fun weights(tf: Object, idf: (String) -> Number): Object =
    tf mapObject ((occ, tok) -> {(tok): sqrt(sizeOf(occ)) * idf(tok as String)})

fun cosine(a: Object, b: Object): Number = do {
    var dot = sum((keysOf(a) map ($ as String)) map ((k) -> (a[k] default 0) * (b[k] default 0)))
    var na = sqrt(sum(valuesOf(a) map ($ * $)))
    var nb = sqrt(sum(valuesOf(b) map ($ * $)))
    ---
    if (na == 0 or nb == 0) 0 else dot / (na * nb)
}

fun rank(q: String, examples: Array): Array = do {
    var docs = examples map {key: $.key, tf: tokens($.text) groupBy $}
    var n = sizeOf(docs)
    var df = flatten(docs map (keysOf($.tf) map ($ as String))) groupBy $
    fun idf(t: String): Number = sqrt((n + 1) / (sizeOf(df[t] default []) + 1))
    var qv = weights(tokens(q) groupBy $, idf)
    var scored = docs map {key: $.key, score: cosine(qv, weights($.tf, idf))}
    ---
    ((scored groupBy $.key) pluck ((xs, k) -> {key: k as String, score: max(xs map $.score) default 0})) orderBy -$.score
}
