%dw 2.0
import * from dw::core::Dates
output application/json
---
{
 "atBeginningOfMonthLocalDateTime": atBeginningOfMonth(|2020-10-06T18:23:20.351|)
}