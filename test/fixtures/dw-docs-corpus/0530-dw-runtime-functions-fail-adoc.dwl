%dw 2.0
import * from dw::Runtime
var result = []
output application/json
---
if(sizeOf(result) <= 0) fail('Data was empty') else result