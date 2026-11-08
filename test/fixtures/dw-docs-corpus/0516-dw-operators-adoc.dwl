%dw 2.0
var orNot = if (1 + 1 == 4 or not 1 == 2) {"answer": "orNot - Condition met"}
             else {"answer": "nope"}
var andNot = if (1 + 1 == 2 and not 1 == 2) {"answer": "andNot - Condition met"}
             else {"answer": "nope"}
var notWithAndNot = if (not (1 + 1 == 2 and not 1 == 1)) {"answer": "notWithAndNot - Condition met"}
              else {"answer": "nope"}
output application/json
---
{ "answers" :
  [
    orNot,
    andNot,
    notWithAndNot
  ]
}