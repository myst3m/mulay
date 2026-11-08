%dw 2.0
import * from dw::util::Tree
output application/json
---
{
  a: isObjectType([{kind: OBJECT_TYPE, selector: "user", namespace: null},
                   {kind: ATTRIBUTE_TYPE, selector: "name", namespace: null}]),
  b: isObjectType([{kind: OBJECT_TYPE, selector: "user", namespace: null},
                   {kind: OBJECT_TYPE, selector: "name", namespace: null}]),
  c: isObjectType([{kind: OBJECT_TYPE, selector: "user", namespace: null}])
}