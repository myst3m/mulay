%dw 2.0
import * from dw::util::Coercions
output application/json
---
{
    epoch: toNumber(|2015-10-01T23:57:59Z|),
    millis: toNumber(|2015-10-01T23:57:59Z|, "milliseconds")
}