%dw 2.0
output application/json
var names = ["john", "peter", "matt"]
---
users: names map((name) -> upper(name))