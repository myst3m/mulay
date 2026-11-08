%dw 2.0
type User = {name: String, age: Number}
output application/java
---
{name: 'John'} is User