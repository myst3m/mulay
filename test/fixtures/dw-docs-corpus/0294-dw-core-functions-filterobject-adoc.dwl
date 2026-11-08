%dw 2.0
output application/json
var myObject = {
    str1 : "String 1",
    str2 : "String 2",
    str3 : null,
    str4 : "String 4",
}
---
myObject filterObject $ != null