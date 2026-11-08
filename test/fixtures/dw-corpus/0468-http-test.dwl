%dw 2.0
output application/json
---
{
    message: "hello",
    timestamp: now(),
    method: attributes.method
}