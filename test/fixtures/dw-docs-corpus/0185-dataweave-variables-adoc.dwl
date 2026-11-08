%dw 2.0
output application/json
---
do {
      var myVar = 2
      ---
      [1, myVar, 3]
}