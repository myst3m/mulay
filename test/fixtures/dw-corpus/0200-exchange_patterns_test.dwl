%dw 2.0
var add = (x, y = 10) -> x + y
---
add(5, 20)