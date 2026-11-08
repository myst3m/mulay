%dw 2.0
import * from dw::util::Coercions
output application/dw
---
{
   toTimeZoneOffset: toTimeZone("-03:00"),
   toTimeZoneAbbreviation: toTimeZone("Z"),
   toTimeZoneName: toTimeZone("America/Argentina/Buenos_Aires")
}