%dw 2.0
import * from dw::util::Coercions
output application/json
---
{
    toSecondsEx1: toNumber(|PT1H10M|, "seconds"),
    toSecondsEx2: toNumber(|PT1M7S|, "milliseconds")
}