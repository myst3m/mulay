%dw 2.0
output application/json
---
{
  present: "abcd" indexOf "c",
  notPresent: "xyz" indexOf "c",
  presentMoreThanOnce: "abcdc" indexOf "c",
}