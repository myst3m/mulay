%dw 2.0
var myVar = { country : "FRANCE" }
output application/json
---
if (myVar.country == "USA")
  { currency: "USD" }
else { currency: "EUR" }