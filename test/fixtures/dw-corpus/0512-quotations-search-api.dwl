%dw 2.0
output application/json
---
{
    count: sizeOf(payload),
    results: payload
}