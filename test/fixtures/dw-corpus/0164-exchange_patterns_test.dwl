%dw 2.0
var username = "Bob"
---
"Username: " ++ username ++ " Age: " ++ payload.age as String