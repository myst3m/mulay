%dw 2.0
---
payload map {
  FirstName: $.firstname,
  LastName: $.surname,
  Email: $.email
}