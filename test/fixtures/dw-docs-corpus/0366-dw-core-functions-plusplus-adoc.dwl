%dw 2.0
output application/json
---
{ "a" : [0, 1, true, "my string"] ++ [2, [3,4,5], {"a": 6}] }