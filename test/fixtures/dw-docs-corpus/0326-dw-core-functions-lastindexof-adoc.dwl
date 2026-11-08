%dw 2.0
output application/json
---
{
  present: ["a","b","c","d"] lastIndexOf "c",
  notPresent: ["x","w","x"] lastIndexOf "c",
  presentMoreThanOnce: ["a","b","c","c"] lastIndexOf "c",
}