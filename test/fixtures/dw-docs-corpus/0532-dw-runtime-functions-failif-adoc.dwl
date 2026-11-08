%dw 2.0
import failIf from dw::Runtime
var result = {"a":"test"}
output application/json
---
{ "result" : result failIf isEmpty($) }