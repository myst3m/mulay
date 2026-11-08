%dw 2.0
import * from dw::core::Arrays
output application/json
var users = ["Mariano", "Leandro", "Julian", "Tomo"]
---
users splitWhere (item) -> item startsWith "Jul"