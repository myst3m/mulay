%dw 2.0
output application/json
var s1 = (1 to 5000) reduce ((item, acc = 0) -> acc + item * item)
var s2 = (1 to 5000) reduce ((item, acc = 0) -> acc + item * 3)
var s3 = (1 to 5000) reduce ((item, acc = 0) -> acc + (if ((item mod 3) == 0) item else 0))
var s4 = sizeOf((1 to 5000) filter (($ mod 7) == 0))
var s5 = sizeOf((1 to 5000) filter (($ mod 11) == 0))
var s6 = (1 to 3000) map ($ * $ + $ * 3 + 7)
var s7 = s6 reduce ((item, acc = 0) -> acc + item)
---
{
  sum1: s1,
  sum2: s2,
  sum3: s3,
  count4: s4,
  count5: s5,
  sum7: s7
}