%dw 2.0
output application/xml
---
employees: {
  ([{name: "John", lastName: "Doe"}, {name: "Jane", lastName: "Smith"}] map {
    employee: {
      name: $.name,
      lastName: $.lastName
    }
  })
}