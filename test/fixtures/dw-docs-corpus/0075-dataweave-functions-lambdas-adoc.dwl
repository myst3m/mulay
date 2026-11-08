%dw 2.0
output application/json
var toUser = (user) -> {
  firstName: user.field1,
  lastName: user.field2
}
---
{
  "user" : toUser(payload)
}