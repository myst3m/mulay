%dw 2.0
---
[{name: "Mariano", age: 37}, {name: "Shoki", age: 30}, {name: "Tomo", age: 25}, {name: "Ana", age: 29}]
          filter ((value, index) -> value.age >= 30)