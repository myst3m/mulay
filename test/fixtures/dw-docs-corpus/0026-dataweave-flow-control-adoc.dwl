%dw 2.0
var myVar = { country : "UK" }
output application/json
---
if (myVar.country =="USA")
	{ currency: "USD" }
else if (myVar.country =="UK")
	{ currency: "GBP" }
else { currency: "EUR" }