%dw 2.0
output application/json
---
{
  request: "prepared",
  items: (1 to 50) map { id: $, val: $ * 3.14 }
}