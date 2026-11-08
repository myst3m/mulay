%dw 2.0
output application/json
var msg = "Hello"

var toUpper = (aString) -> upper(aString)
var toLower = (aString) -> lower(aString)

fun msg2(optParm = "ignore") = "hello"

fun toTitle(text: String) = toLower(text[0]) ++ toUpper(text[1 to -1])

fun combined(function, msg="universe") = function(msg ++ " world")
---
[
   msg: msg,
   msg2: msg2(),
   toUpper: toTitle(msg),
   combined: combined(toUpper, msg),
   combined2: combined((x) -> lower(x) ++ " today", msg)
]