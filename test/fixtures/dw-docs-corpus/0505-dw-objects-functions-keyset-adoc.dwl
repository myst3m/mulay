%dw 2.0
import * from dw::core::Objects
output application/json
---
{ "keySet" : keySet({ "a" : true, "b" : 1}) }