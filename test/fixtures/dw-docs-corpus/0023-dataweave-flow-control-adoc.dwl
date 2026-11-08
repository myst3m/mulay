%dw 2.0
output application/json
fun test(p: String) = do {
    var a = "Foo" ++ p
    ---
    a
}
---
{ result: test(" Bar") }