%dw 2.0
var greet = (name, prefix = "Hello") -> prefix ++ " " ++ name
---
greet("World")