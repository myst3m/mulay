%dw 2.0
output application/json
import * from dw::core::Types
 type AArray = Array<String> {n: 1}
 type AArray2 = Array<AArray>
 ---
 {
     a: isReferenceType( AArray),
     b: isReferenceType(arrayItem(AArray2)),
     c: isReferenceType(String)
 }