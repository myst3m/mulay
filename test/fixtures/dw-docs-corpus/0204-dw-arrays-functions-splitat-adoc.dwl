%dw 2.0
import * from dw::core::Arrays
output application/json
var users = ["Mariano", "Leandro", "Julian"]
---
users splitAt 1