%dw 2.0
output application/json
var toUpper = (aString) -> upper(aString)

var addSuffix = (msg, aFunction, suffix) -> aFunction(msg ++ suffix)
---
addSuffix("hello", toUpper, " world") //result is "HELLO WORLD"