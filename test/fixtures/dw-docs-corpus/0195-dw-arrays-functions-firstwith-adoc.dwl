%dw 2.0
output application/json
import firstWith from dw::core::Arrays
var users = [{name: "Mariano", lastName: "Achaval"}, {name: "Ana", lastName: "Felisatti"}, {name: "Mariano", lastName: "de Sousa"}]
---
{
  a: users firstWith ((user, index) -> user.name == "Mariano"),
  b: users firstWith ((user, index) -> user.name == "Peter")
}