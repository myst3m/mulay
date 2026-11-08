%dw 2.0
import * from dw::core::Dates
output application/json
---
{
   "atBeginningOfHourTime": atBeginningOfHour(|18:23:20.351-03:00|)
}