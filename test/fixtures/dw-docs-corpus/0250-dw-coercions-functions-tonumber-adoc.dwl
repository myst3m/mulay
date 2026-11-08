%dw 2.0
import * from dw::util::Coercions
var myKey = keysOf({"123" : "myValue"})
output application/json
---
 {
     "default": toNumber("1.0"),
     "withFormat": toNumber("0.005",".00"),
     "withLocal": toNumber("1,25","#.##","ES"),
     "withExtraPlaceholders": toNumber("5.55","####.####"),
     "keyToNumber": toNumber(myKey[0])
 }