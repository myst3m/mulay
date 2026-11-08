%dw 2.0
import myFunc as appendDash, myVar as weaveName from modules::MyModule
var myVar = "Mapping"
output application/json
---
appendDash("dataweave") ++ weaveName ++ "_" ++ myVar