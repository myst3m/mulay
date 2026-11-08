%dw 2.0
var data = [1, 2, 11, 1, 1, 2]
---
[1, 2, 11] map sizeOf(data find $)