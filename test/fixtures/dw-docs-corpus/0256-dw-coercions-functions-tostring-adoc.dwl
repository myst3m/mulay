%dw 2.0
import * from dw::util::Coercions
output application/json
---
{
    a: toString(1.0),
    b: toString(0.005,".00"),
    c: toString(0.035,"#.##","ES"),
    d: toString(0.005,"#.##","ES","HALF_EVEN"),
    e: toString(0.035,"#.00",null,"HALF_EVEN"),
    f: toString(1.1234,"\$.## 'in my account'")
}