%dw 2.0
import * from dw::Runtime
import duration from dw::util::Timer
import firstWith, some from dw::core::Arrays
import * from dw::test::Asserts
import inputsOf, outputOf, resourceText from dw::test::internal::Files

@AnnotationTarget(targets = ["Expression"])
annotation Skip(reason: String = "skipped")

var ERROR_STATUS = "ERROR"
var OK_STATUS = "OK"
var FAIL_STATUS = "FAIL"
var SKIP_STATUS = "SKIP"

type TEST_STATUS = "ERROR" | "OK" | "FAIL" | "SKIP"

type TestResult = {
    name: String,
    time: Number,
    status: TEST_STATUS,
    tests?: Array<TestResult>,
    errorMessage?: String,
    skipReason?: String,
    location?: Object
}

type TestConfig<Ctx <: Object> = {|
    setup: () -> Ctx,
    teardown: (c: Ctx) -> Any
|}

fun decisive(results: Array<MatcherResult>): MatcherResult =
    (results firstWith (not ($.matches as Boolean))) default (results[-1] default MATCHED)

fun selected(testName: String): Boolean = do {
    var wanted = prop("testToRun")
    ---
    if (wanted == null or isBlank(wanted as String)) true
    else ((wanted as String) splitBy ",") some ((testName as String) contains $)
}

fun skipped(testName: String, annotated: Boolean): TestResult = {
    name: testName,
    time: 0,
    status: SKIP_STATUS,
    (skipReason: testName.^skip.reason as String) if annotated
}

fun settle(got: Any, arg: Any): Any =
    if ((typeOf(got) as String) == "Function") settle(got(arg), arg)
    else if (got is Array) (got as Array) map ((g) -> if ((typeOf(g) as String) == "Function") settle(g(arg), arg) else g)
    else got

fun outcome(testName: String, run: Object): TestResult = do {
    var attempt = run.result
    ---
    if (attempt.success) do {
        var got = attempt.result
        var r = if (got is Array) decisive(got as Array<MatcherResult>) else got as MatcherResult
        ---
        {
            name: testName,
            time: run.time,
            status: if (r.matches as Boolean) OK_STATUS else FAIL_STATUS,
            errorMessage: if (r.reasons?) ((r.reasons as Array<String>) joinBy "\n") else r.description as String,
            location: location(testName)
        }
    } else {
        name: testName,
        status: ERROR_STATUS,
        time: run.time,
        errorMessage: "$(attempt.error.kind):$(attempt.error.message) at:\n$(attempt.error.location)",
        location: location(testName)
    }
}

fun withConfig<Ctx <: Object>(testName: String, config: TestConfig<Ctx>) = {
    config: config,
    testName: testName
}

fun in(testName: String, testCases: () -> MatcherResult | Array<MatcherResult>): TestResult =
    if (testName.^skip? or not selected(testName)) skipped(testName, testName.^skip? default false)
    else outcome(testName, duration(() -> try(() -> settle(testCases(), null))))

fun in(testSetup: {config: Object, testName: String}, test: (c: Object) -> MatcherResult | Array<MatcherResult>): TestResult = do {
    var testName = testSetup.testName
    ---
    if (testName.^skip? or not selected(testName)) skipped(testName, testName.^skip? default false)
    else do {
        var ready = try(() -> testSetup.config.setup())
        ---
        if (not ready.success) {
            name: testName,
            time: 0,
            status: SKIP_STATUS,
            skipReason: "Setup failed with: $(ready.error.message)"
        }
        else do {
            var ctx = ready.result
            var result = outcome(testName, duration(() -> try(() -> settle(test(ctx), ctx))))
            var done = testSetup.config.teardown(ctx)
            ---
            result
        }
    }
}

fun describedBy(suite: String, testsToRun: Array<() -> TestResult>): TestResult =
    if (suite.^skip?) {
        name: suite,
        time: 0,
        status: SKIP_STATUS,
        skipReason: suite.^skip.reason as String,
        tests: testsToRun map { name: "", time: 0, status: SKIP_STATUS }
    }
    else do {
        var run = duration(() -> testsToRun map $())
        ---
        {
            name: suite,
            time: run.time,
            status: OK_STATUS,
            tests: run.result,
            location: location(suite)
        }
    }

fun inputsFrom(dir: String): {_?: Any} = inputsOf(dir)

fun outputFrom(dir: String): Any = outputOf(dir)

fun evalPath(fileToExecute: String, inputs: {_?: Any}, mimeType: String): Any = do {
    var text = resourceText(fileToExecute)
    var result = if (text == null) fail("Unable to find the script $(fileToExecute)") else eval(fileToExecute, {(fileToExecute): text as String}, {}, inputs)
    ---
    if (result.success) result.result.value else fail(result.error.message as String)
}
