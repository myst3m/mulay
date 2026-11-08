%dw 2.0
var myRead =
read("<prices><price>9.99</price><price>10.99</price></prices>","application/xml")
output application/json
---
myRead.prices groupBy "costs"