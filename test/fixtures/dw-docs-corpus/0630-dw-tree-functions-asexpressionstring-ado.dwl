%dw 2.0
import * from dw::util::Tree
output application/json
---
asExpressionString([
        {kind: OBJECT_TYPE, selector: "user", namespace: null},
        {kind: ATTRIBUTE_TYPE, selector: "name", namespace: null}
    ])