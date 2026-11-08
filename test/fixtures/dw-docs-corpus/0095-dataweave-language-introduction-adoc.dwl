%dw 2.0
output application/json
fun toUser(user) = {firstName: user.name, lastName: user.lastName}
---
{
  user: toUser(payload)
}