%dw 2.0
output application/json
---
(1 to 50) map {
  index: $,
  value: $ * $ ,
  sqrt: sqrt($ as Number)
}