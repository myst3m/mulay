%dw 2.0
import * from dw::util::Tree
output application/json
---
{
  a: isAttributeType([{kind: OBJECT_TYPE, selector: "user", namespace: null},
                      {kind: ATTRIBUTE_TYPE, selector: "name", namespace: null}]),
  b: isAttributeType([{kind: OBJECT_TYPE, selector: "user", namespace: null},
                      {kind: ARRAY_TYPE, selector: "name", namespace: null}]),
  c: isAttributeType([{kind: ATTRIBUTE_TYPE, selector: "name", namespace: null}])
}