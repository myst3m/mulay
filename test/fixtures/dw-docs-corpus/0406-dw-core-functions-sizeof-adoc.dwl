%dw 2.0
output application/json
---
{
  sizeOfSting2 : sizeOf("my string"),
  sizeOfEmptyString: sizeOf(""),
  sizeOfNumber : sizeOf("123" as Number)
}