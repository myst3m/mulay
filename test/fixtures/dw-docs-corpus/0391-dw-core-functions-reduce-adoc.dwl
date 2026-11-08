%dw 2.0
output application/json
---
{
   "concat" : ["a", "b", "c", "d"] reduce ((item, acc = "z") -> acc ++ item),
   "sum": [0, 1, 2, 3, 4, 5] reduce ((item, acc = 3) -> acc + item),
   "multiply" : [2,3,3] reduce ((item, acc) -> acc * item),
   "multiplyAcc" : [2,2,3] reduce ((item, acc = 3) -> acc * item)
}