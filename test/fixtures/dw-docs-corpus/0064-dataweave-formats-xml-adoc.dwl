%dw 2.0
output application/json
---
{
    test: payload.test is CDATA
}