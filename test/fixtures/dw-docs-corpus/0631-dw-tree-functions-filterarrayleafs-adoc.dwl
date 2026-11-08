%dw 2.0
import * from dw::util::Tree
var myArray = [1, {name: ["", true], test: 213}, "123", null]
output application/json
---
{
   a: myArray filterArrayLeafs ((value, path) ->
        !(value is Null or value is String)),
   b:  myArray filterArrayLeafs ((value, path) ->
        (value is Null or value == 1)),
   c: { a : [1,2] } filterArrayLeafs ((value, path) ->
        (value is Null or value == 1)),
   d: myArray filterArrayLeafs ((value, path) ->
        !isArrayType(path))
}