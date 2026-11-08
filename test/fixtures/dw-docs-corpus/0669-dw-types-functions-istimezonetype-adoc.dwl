%dw 2.0
import * from dw::core::Types
type ATimeZone = TimeZone
output application/json
---
{
   a: isTimeZoneType(ATimeZone),
   b: isTimeZoneType(TimeZone),
   c: isTimeZoneType(String),
}