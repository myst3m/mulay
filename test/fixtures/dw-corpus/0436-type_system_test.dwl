%dw 2.0
type User = {name: String, age: Number}
output application/java
---
{name: 'John', age: 30} is User