%dw 2.0
output application/json
var array1 = [1,2,3]
var array2 = [4,5,6]
var array3 = [7,8,9]
var arrayOfArrays = [array1, array2, array3]
---
flatten(arrayOfArrays)