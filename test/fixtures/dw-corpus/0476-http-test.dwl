%dw 2.0
output application/json
---
{
    original: payload,
    extracted: payload.message
}