%dw 2.0
import * from dw::util::Tree
output application/json
---
{
  a: isArrayType([{kind: OBJECT_TYPE, selector: "user", namespace: null},
                  {kind: ATTRIBUTE_TYPE, selector: "name", namespace: null}]),
  b: isArrayType([{kind: OBJECT_TYPE, selector: "user", namespace: null},
                  {kind: ARRAY_TYPE, selector: 0, namespace: null}]),
  c: isArrayType([{kind: ARRAY_TYPE, selector: 0, namespace: null}])
}