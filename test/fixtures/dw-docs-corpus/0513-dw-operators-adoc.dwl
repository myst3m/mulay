%dw 2.0
output application/json
---
{ "relational" : [
    { "1 < 1" : (1 < 1) },
    { "1 > 2" : (1 > 2) },
    { "1 <= 1" : (1 <= 1) },
    { "1 >= 1" : (1 >= 1) }
  ]
}