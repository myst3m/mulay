%dw 2.0
output application/json
---
{
  squares: (1 to 26) map ($ * $),
  numbers: (1 to 10) reduce ((item, acc = 0) -> acc + item)
}