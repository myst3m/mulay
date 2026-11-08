%dw 2.0
output application/json
import * from dw::util::Values
---
[[123, true], [456, true]] mask 1 with false