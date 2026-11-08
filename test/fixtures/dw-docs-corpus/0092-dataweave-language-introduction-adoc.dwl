%dw 2.0
output application/xml
---
{
  user: {
    firstName: payload.user_firstname,
    lastName: payload.user_lastName
  }
}