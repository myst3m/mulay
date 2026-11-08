%dw 2.0
var myInput = [{lastName: "Doe"}, {lastName: "Parker", name: "Peter"}]
---
myInput map ((value) ->
  value update {
    case name at .name! -> if(name == null) "JOHN" else (upper(name))
  }
)