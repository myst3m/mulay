%dw 2.0
import * from dw::Runtime
var a = 123
output application/json
---
locationString(a)