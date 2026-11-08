%dw 2.0
output application/json
var msg = "Hello"

var msg2 = (x = "ignore") -> "hello"

var toUpper = (aString) -> upper(aString)

var combined = (function, msg="universe") -> function(msg ++ " WORLD")
---
[
   msg: msg,
   msg2: msg2(),
   toUpper: toUpper(msg),
   combined: combined(toUpper, "hello"),
   combined2: combined(((x) -> lower(x) ++ " Today"), msg)
]