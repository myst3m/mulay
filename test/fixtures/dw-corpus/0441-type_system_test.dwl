%dw 2.0
type Summary = {name: String}
output application/java
---
{name: 'John', age: 30, extra: true} as Summary