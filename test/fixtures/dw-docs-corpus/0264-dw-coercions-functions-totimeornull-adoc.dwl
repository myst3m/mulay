%dw 2.0
import * from dw::util::Coercions
output application/dw
---
{
  a: toTimeOrNull("13:44:12.283-08:00", [{format: "HH:mm:ss.xxx"}, {format: "HH:mm:ss.nxxx"}]),
  b: toTimeOrNull("13:44:12.283-08:00", [{format: "HH:mm:ss.xxx"}])
}