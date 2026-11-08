%dw 2.0
import * from dw::util::Tree
output application/dw
---
{
    a: {
          name : "",
          lastName @(foo: ""): "Achaval",
          friends @(id: 123): [{id: "", test: true}, {age: 123}, ""]
        } filterTree ((value, path) ->
            value match  {
                            case s is String -> !isEmpty(s)
                            else -> true
                          }
    ),
    b: null filterTree ((value, path) -> value is String),
    c: [
            {name: "Mariano", friends: []},
            {test: [1,2,3]},
            {dw: ""}
        ] filterTree ((value, path) ->
            value match  {
                            case a is Array ->  !isEmpty(a as Array)
                            else -> true
                        })
}