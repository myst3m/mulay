%dw 2.0
output application/json
---
{
    key: attributes.queryParams.key,
    exists: vars.exists
}