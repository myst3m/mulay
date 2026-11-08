%dw 2.0
output application/json
import * from dw::util::Values
---
[{name: "Peter Parker", password: "spiderman"}, {name: "Bruce Wayne", password: "batman"}] mask "password" with "*****"