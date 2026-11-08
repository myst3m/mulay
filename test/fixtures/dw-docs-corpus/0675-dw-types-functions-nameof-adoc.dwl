%dw 2.0
output application/json
import * from dw::core::Types
type AArray = Array<String> {n: 1}
type AArray2 = Array<String>
---
 {
     a: nameOf(AArray),
     b: nameOf(AArray2),
     c: nameOf(String)
 }