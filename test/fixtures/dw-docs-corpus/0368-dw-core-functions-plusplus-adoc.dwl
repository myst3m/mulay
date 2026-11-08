%dw 2.0
output application/xml
---
{ concat : {aa: "a", bb: "b"} ++ {cc: "c"} }