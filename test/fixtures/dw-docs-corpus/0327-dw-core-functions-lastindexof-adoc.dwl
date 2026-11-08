%dw 2.0
output application/json
---
{
  present: "abcd" lastIndexOf "c",
  notPresent: "xyz" lastIndexOf "c",
  presentMoreThanOnce: "abcdc" lastIndexOf "c",
}