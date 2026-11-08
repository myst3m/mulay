%dw 2.0
import * from dw::util::Coercions
output application/dw
---
{
    fromEpoch: toDateTime(1443743879),
    fromMillis: toDateTime(1443743879000, "milliseconds")
}