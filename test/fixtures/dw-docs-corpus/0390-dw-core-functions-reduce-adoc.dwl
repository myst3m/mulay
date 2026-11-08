%dw 2.0
var myNums = [1,2,3,4]
var myEmptyList = []
output application/json
---
{
   "sum" : myNums reduce ($$ + $),
   "concat" : myNums reduce ($$ ++ $),
   "emptyList" : myEmptyList reduce ($$ ++ $)
}