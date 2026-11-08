%dw 2.0
output application/json
type UnionType = {name: String} | Number
type Fail = UnionType.name
---
{}