%dw 2.0
import * from dw::core::Arrays
var users = ["Mariano", "Leandro", "Julian"]
output application/json
---
take(users, 2)