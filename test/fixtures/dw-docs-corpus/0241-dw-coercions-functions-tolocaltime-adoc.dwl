%dw 2.0
import * from dw::util::Coercions
output application/json
---
{
   toLocalTimeEx: toLocalTime("23:57:59"),
   toLocalTimeEx2: toLocalTime("13:44:12.283","HH:mm:ss.n")
}