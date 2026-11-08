%dw 2.0
import * from dw::util::Values
output application/json
---
{user: {name: "Mariano"}} update ["user", field("name")] with "Data Weave"