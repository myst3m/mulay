%dw 2.0
var myVar = "Hello World!"
output application/json
---
{
  indices2to6 : myVar[2 to 6],
  indicesFromEnd : myVar[6 to -1],
  reversal : myVar[11 to -0]
}