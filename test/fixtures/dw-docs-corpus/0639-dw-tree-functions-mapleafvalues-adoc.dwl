%dw 2.0
output application/json
import * from dw::util::Tree
---
{
    name: "Mariano",
    test: [1,2,3]
} mapLeafValues ((value, path) -> if(isObjectType(path))
                                        "***"
                                  else if(isArrayType(path))
                                        "In an array"
                                  else "Is an attribute")