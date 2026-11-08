%dw 2.0
var myArray = [1,2,3,4,5]
---
myArray map not (($ mod 2) == 0)