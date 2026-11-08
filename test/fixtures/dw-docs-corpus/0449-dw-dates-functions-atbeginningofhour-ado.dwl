%dw 2.0
import * from dw::core::Dates
output application/json
---
{
   "atBeginningOfHourLocalTime": atBeginningOfHour(|18:23:20.351|)
}