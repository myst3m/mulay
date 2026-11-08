%dw 2.0
output application/json
fun toUser(obj) = {
  firstName: obj.field1,
  lastName: obj.field2
}
---
{
  "user" : toUser(payload)
}