%dw 2.0
output  application/json
---
[ { "a" : 1 }, { "a" : 3 }, { "a" : 2 } ] maxBy ((item) -> item.a)