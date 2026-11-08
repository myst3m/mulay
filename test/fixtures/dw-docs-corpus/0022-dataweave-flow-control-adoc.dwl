%dw 2.0
output application/json
var myVar = do {
    var name = "DataWeave"
    ---
    name
}
---
{ result: myVar }