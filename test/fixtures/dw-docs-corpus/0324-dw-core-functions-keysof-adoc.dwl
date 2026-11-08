%dw 2.0
output application/json
---
{ "keysOf" : keysOf({ "a" : true, "b" : 1}) }