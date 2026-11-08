%dw 2.0
var myArray = [1,2,3,4,5]
var myMap = myArray map not (($ mod 2) == 0)
output application/json
---
{
  "not" : [
    "notTrue" : not true,
    "notFalse" : not false,
    "myMapWithNot" : myMap
  ],
  "and" : [
    "andTrueFalse" : true and false,
    "andIsTrue" : (1 + 1 == 2) and (2 + 2 == 4),
    "andIsFalse" : (1 + 1 == 2) and (2 + 2 == 2)
  ],
  "or" : [
    "orTrueFalse" : true or false,
    "orIsTrue" : (1 + 1 == 2) or (2 + 2 == 2),
    "orIsFalse" : (1 + 1 == 1) or (2 + 2 == 2)
  ],
  "!-vs-not" : [
	  "example-!" : (! true or true),
	  "example-not" : (not true or true)
  ]
}