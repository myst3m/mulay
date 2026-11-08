%dw 2.0
output application/json
---
[{name: "Santiago", age: 42},{name: "Leandro", age: 29}, {name: "Mariano", age: 35}] orderBy (person) -> person.age