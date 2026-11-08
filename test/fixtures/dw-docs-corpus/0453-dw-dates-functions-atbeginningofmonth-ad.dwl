%dw 2.0
import * from dw::core::Dates
output application/json
---
{
  atBeginningOfMonthDate: atBeginningOfMonth(|2020-10-06|)
}