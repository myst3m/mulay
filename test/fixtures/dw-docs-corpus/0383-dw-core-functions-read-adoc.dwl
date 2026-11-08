%dw 2.0
var myVar = "Some, Body"
output application/json
---
read(myVar,"application/csv",{header:false})[0]