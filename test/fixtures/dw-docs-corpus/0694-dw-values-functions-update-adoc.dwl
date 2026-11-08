%dw 2.0
import * from dw::util::Values
output application/json
---
[{role: "a", name: "spiderman"}, {role: "b", name: "batman"}] update "role" with "Super Hero"