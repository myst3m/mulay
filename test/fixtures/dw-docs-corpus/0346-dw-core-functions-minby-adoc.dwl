%dw 2.0
output  application/json
---
[ { "a" : 1 }, { "a" : 2 }, { "a" : 3 } ] minBy (item) -> item.a