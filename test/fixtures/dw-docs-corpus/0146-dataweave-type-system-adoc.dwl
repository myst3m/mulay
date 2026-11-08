%dw 2.0
fun head<ItemType>(elements: Array<ItemType>): ItemType = elements[0]!

var firstString:String = head(["DataWeave", "Java", "Scala", "Haskell"]) ++ " Rules!!!"
var firstNumber:Number = head([1,2,3])
output application/json
---
firstNumber