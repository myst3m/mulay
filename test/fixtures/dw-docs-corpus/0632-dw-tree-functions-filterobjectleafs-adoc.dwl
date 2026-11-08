%dw 2.0
import * from dw::util::Tree
var myArray = [{name @(mail: "me@me.com", test:123 ): "", id:"test"},
               {name: "Me", id:null}]
output application/json
---
{
 a: {
     name: "Mariano",
     lastName: null,
     age: 123,
     friends: myArray
    }  filterObjectLeafs ((value, path) ->
         !(value is Null or value is String)),
 b: { c : null, d : "hello" } filterObjectLeafs ((value, path) ->
         (value is Null and isObjectType(path)))
}