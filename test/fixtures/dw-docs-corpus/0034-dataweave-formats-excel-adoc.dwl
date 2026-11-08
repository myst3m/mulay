%dw 2.0
output application/xlsx header=true
---
{
  Sheet1: [
    {
      Id: 123,
      Name: George
    },
    {
      Id: 456,
      Name: Lucas
    }
  ]
}