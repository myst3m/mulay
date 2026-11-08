%dw 2.0
output application/json
---
{
    root: payload.root,
    firstItem: payload.root.item[0],
    secondItem: payload.root.item[1]
}