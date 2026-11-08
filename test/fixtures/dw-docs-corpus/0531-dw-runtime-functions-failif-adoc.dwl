%dw 2.0
import failIf from dw::Runtime
var result = {}
output application/json
---
{ "result" : "SUCCESS" failIf (isEmpty(result)) }