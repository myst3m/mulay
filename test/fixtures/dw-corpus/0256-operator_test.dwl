%dw 2.0
var myInput = {name: "Ken", age: 30}
---
myInput update {
  case age at .age -> age + 1
}