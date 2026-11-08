%dw 2.0
import * from dw::Runtime
import equalityReasons, readable from dw::test::internal::Native
import some from dw::core::Arrays

type MatcherResult = {
    "matches": Boolean,
    description: String,
    reasons?: Array<String>
}

type Matcher<T> = (value: T) -> MatcherResult

var MATCHED = { matches: true, description: "" }

fun origin(f): String = do {
    var where = location(f)
    ---
    " From `$(locationString(f))` at line $(where.start.line) of $(where.sourceIdentifier).dwl."
}

fun outcome(got: Any, value: Any): Any =
    if ((typeOf(got) as String) == "Function") got(value) else got

fun must<T>(value: T, matchers: Array<Matcher<T>>): MatcherResult = do {
    fun step(i: Number, last: Object): Object =
        if (i >= sizeOf(matchers)) last
        else do {
            var m = matchers[i]
            var got = outcome(m(value), value)
            var res = if (got is Boolean) { matches: got as Boolean, description: "`$(locationString(m))` was $(readable(value))." } else got as Object
            ---
            if (res.matches as Boolean) step(i + 1, res) else res
        }
    ---
    step(0, MATCHED)
}

fun must<T>(value: T, matcher: Matcher<T>): MatcherResult = do {
    var got = outcome(matcher(value), value)
    var from = origin(matcher)
    ---
    if (got is Boolean)
        { matches: got as Boolean, description: "Assertion `$(locationString(matcher))` failed with value $(readable(value)).$(from)" }
    else {
        matches: got.matches as Boolean,
        description: (got.description as String) ++ from,
        (reasons: (got.reasons as Array<String>) map ($ ++ from)) if (got.reasons?)
    }
}

fun notBe<T>(matcher: Matcher<T>): Matcher<T> = (value) -> do {
    var r = matcher(value)
    ---
    { matches: not (r.matches as Boolean), description: "Expected not `$(r.description).`" }
}

fun anyOf(matchers: Array<Matcher<Any>>): Matcher<Any> = (value) -> do {
    var rs = matchers map $(value)
    ---
    {
        matches: rs some ($.matches as Boolean),
        description: "Expected any of $(rs map $.description joinBy " or ") but was $(readable(value))."
    }
}

fun equalTo(expected: Any, equalToConfig: {unordered?: Boolean} = {}): Matcher<Any> = (actual) -> do {
    var reasons = equalityReasons(actual, expected, equalToConfig.unordered default false)
    ---
    {
        matches: isEmpty(reasons),
        description: "Expected $(readable(expected)) but was $(readable(actual)).",
        reasons: reasons
    }
}

fun equalToResource(resourceName: String, contentType: String = "application/dw", readerProperties: Object = {}): Matcher<Any> =
    equalTo(readUrl("classpath://$(resourceName)", contentType, readerProperties))

fun haveSize(expectedSize: Number): Matcher<Array | String | Object | Null> = (actual) ->
    if (actual == null) { matches: false, description: "Expected size $(expectedSize) but was null." }
    else do {
        var n = sizeOf(actual as Array | String | Object)
        ---
        { matches: n == expectedSize, description: "Expected size $(expectedSize) but was $(n)." }
    }

fun typed(name: String, ok: Boolean, actual: Any): MatcherResult =
    { matches: ok, description: "Expected value to be $(name) type but was $(typeOf(actual) as String)." }

fun beArray(): Matcher = (actual) -> typed("Array", actual is Array, actual)

fun beString(): Matcher = (actual) -> typed("String", actual is String, actual)

fun beNumber(): Matcher = (actual) -> typed("Number", actual is Number, actual)

fun beBoolean(): Matcher = (actual) -> typed("Boolean", actual is Boolean, actual)

fun beObject(): Matcher = (actual) -> typed("Object", actual is Object, actual)

fun beNull(): Matcher = (actual) -> typed("Null", actual is Null, actual)

fun notBeNull(): Matcher = (actual) -> { matches: not (actual is Null), description: "Expected value not to be Null type." }

fun contain(expected: Any): Matcher = (actual) ->
    if (expected is String)
        { matches: actual contains expected, description: "Expected $(actual) to contain $(expected)." }
    else
        { matches: actual contains expected, description: "Expected $(readable(actual)) to contain $(readable(expected))." }

fun beOneOf(expected: Array<Any>): Matcher = (actual) ->
    { matches: expected contains actual, description: "Expected value to be one of $(readable(expected)) but was $(readable(actual))." }

fun endWith(expected: String): Matcher<String> = (actual) ->
    { matches: actual endsWith expected, description: "Expected $(actual) to end with $(expected)." }

fun startWith(expected: String): Matcher<String> = (actual) ->
    { matches: actual startsWith expected, description: "Expected $(actual) to start with $(expected)." }

fun beEmpty(): Matcher<String | Object | Array | Null> = (actual) ->
    { matches: actual == null or isEmpty(actual), description: "Expected $(readable(actual)) to be empty." }

fun beBlank(): Matcher<String | Null> = (actual) ->
    { matches: actual == null or isBlank(actual), description: "Expected $(actual default "null") to be blank." }

fun haveKey(keyName: String): Matcher<Object> = (actual) ->
    { matches: actual[keyName]?, description: "Expected $(readable(actual)) to contain key $(keyName)." }

fun haveValue(value: Any): Matcher<Object> = (actual) ->
    { matches: (actual pluck $) contains value, description: "Expected $(readable(actual)) to contain value $(readable(value))." }

fun beGreaterThan(expected: Comparable, inclusive: Boolean = false): Matcher<Comparable> = (actual) ->
    {
        matches: if (inclusive) actual >= expected else actual > expected,
        description: "Expected value $(readable(actual)) to be greater than $(expected)."
    }

fun beLowerThan(expected: Comparable, inclusive: Boolean = false): Matcher<Comparable> = (actual) ->
    {
        matches: if (inclusive) actual <= expected else actual < expected,
        description: "Expected value $(readable(actual)) to be lower than $(expected)."
    }

fun eachItem(matcher: Matcher<Any>): Matcher<Array<Any>> = (actual) -> do {
    var failed = (actual map { index: $$, result: matcher($) }) filter (not ($.result.matches as Boolean))
    ---
    {
        matches: isEmpty(failed),
        description: "Expected all items of the array to match but $(readable(failed map $.index)) didn't match.",
        reasons: failed map "Item $($.index) $($.result.description)."
    }
}

fun haveItem(matcher: Matcher<Any>): Matcher<Array<Any>> = (actual) ->
    { matches: actual some (matcher($).matches as Boolean), description: "Expected any item of the array to match but none did." }
