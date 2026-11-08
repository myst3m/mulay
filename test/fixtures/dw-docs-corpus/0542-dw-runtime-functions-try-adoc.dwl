%dw 2.0
import try, fail from dw::Runtime
output application/json
fun randomNumber() =
if(random() > 0.5)
  fail("This function is failing")
 else
  "OK"
---
try(() -> randomNumber())