%dw 2.0
output application/json

var x: String | Number = "clearly a string"
var y: "because" = "because"
---
[typeOf(x), typeOf(y)]