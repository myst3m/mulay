%dw 2.0
output application/json

fun toUpper(a: String) = upper(a)
fun toUpper(a: Any) = null
fun toUpper(a: String, b: Number) = upper(a) ++ b as String
---
toUpper("hi!")