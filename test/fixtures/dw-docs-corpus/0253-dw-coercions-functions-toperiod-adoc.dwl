%dw 2.0
import * from dw::util::Coercions
output application/dw
---
{
  toPeriodEx1: toPeriod("P1D"),
  toPeriodEx2: toPeriod("PT1H1M")
}