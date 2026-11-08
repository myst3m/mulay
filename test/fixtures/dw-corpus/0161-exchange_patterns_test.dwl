%dw 2.0
output application/xml
---
employees: {
  (payload map {
    employee: {
      name: $.name
    }
  })
}