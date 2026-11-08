%dw 2.0
import * from dw::core::Types
type ARange = Range
output application/json
---
{
   a: isRangeType(ARange),
   b: isRangeType(Range),
   c: isRangeType(String),
}