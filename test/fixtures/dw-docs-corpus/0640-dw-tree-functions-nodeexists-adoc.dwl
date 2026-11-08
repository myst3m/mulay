%dw 2.0
import * from dw::util::Tree
var myObject =  {
     user: [{
         name: "mariano",
         lastName: "achaval",
         friends: [
             {
                 name: "julian"
             },
             {
                 name: "tom"
             }
         ]
     },
     {
         name: "leandro",
         lastName: "shokida",
         friends: [
             {
                 name: "peter"
             },
             {
                 name: "robert"
             }
         ]

     }
     ]
 }
output application/json
---
{
    mariano : myObject nodeExists ((value, path) -> path[-1].selector == "name" and value == "mariano"),
    julian : myObject nodeExists ((value, path) -> path[-1].selector == "name" and value == "julian"),
    tom : myObject nodeExists ($$[-1].selector == "name" and $ == "tom"),
    leandro : myObject nodeExists ($$[-1].selector == "name" and $ ==  "leandro"),
    peter : myObject nodeExists ($$[-1].selector == "name" and $ == "peter"),
    wrongField: myObject nodeExists ($$[-1].selector == "wrongField"),
    teo: myObject nodeExists ($$[-1].selector == "name" and $ == "teo")
}