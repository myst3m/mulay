%dw 2.0
output application/xml
ns html http://www.w3.org/TR/html4/
ns furniture https://www.w3schools.com/furniture
---
root: {
     a: payload.root.html#table,
     b: payload.root.furniture#table
 }