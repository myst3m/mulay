%dw 2.0
output application/json
fun myfun() = do {
    var name = "DataWeave"
    ---
    name
}
---
{ result: myfun() }