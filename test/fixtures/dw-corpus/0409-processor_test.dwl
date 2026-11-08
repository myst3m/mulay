%dw 2.0
output application/json
var multiplier = 3
fun multiply(x) = x * multiplier
---
multiply(7)