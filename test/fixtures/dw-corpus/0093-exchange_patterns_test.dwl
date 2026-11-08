%dw 2.0
output application/xml
var data = {employees: {employee: [{name: "John", addresses: {address: ["123 Main", "456 Oak"]}}, {name: "Jane", addresses: {address: ["789 Elm"]}}]}}
---
employees: {
  (data.employees.employee map {
    employee: {
      name: $.name,
      addresses: {
        ($.addresses.address map {
          address: $
        })
      }
    }
  })
}