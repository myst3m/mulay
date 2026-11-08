%dw 2.0
import * from dw::util::Coercions
output application/dw
---
{
   a: toTime("23:57:59Z"),
   b: toTime("13:44:12.283-08:00","HH:mm:ss.nxxx")
}