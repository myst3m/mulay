%dw 2.0
import * from dw::core::Dates
output application/json
---
{
  atBeginningOfWeekDate: atBeginningOfWeek(|2020-10-06|)
}