%dw 2.0
output application/json
---
{
  present: ["a","b","c","d"] indexOf "c",
  notPresent: ["x","w","x"] indexOf "c",
  presentMoreThanOnce: ["a","b","c","c"] indexOf "c",
}