%dw 2.0
import * from dw::util::Tree
output application/json
---
 {
     user: [{
         name: "mariano",
         lastName: "achaval"
     }],
     group: "data-weave"
 } mapLeafValues (value, path) -> upper(value)