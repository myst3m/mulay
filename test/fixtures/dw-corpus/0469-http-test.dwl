%dw 2.0
output application/json
---
{
    body: payload,
    headers: attributes.headers,
    method: attributes.method,
    queryParams: attributes.queryParams
}