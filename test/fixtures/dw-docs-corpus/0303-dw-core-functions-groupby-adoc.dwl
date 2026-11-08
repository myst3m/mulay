%dw 2.0
var myArray = [
   { "name": "Foo", "language": "Java" },
   { "name": "Bar", "language": "Scala" },
   { "name": "FooBar", "language": "Java" }
]
output application/json
---
myArray groupBy (item) -> item.language