%dw 2.0
fun test(param1: String) = do {
    var suffix = "123"
    fun innerTest(str: String) = lower(str)
   ---
   innerTest(param1 ++ suffix)
}
output application/json
---
test("HELLO")