%dw 2.0
output application/json
---
{
    results: payload map ((item) -> item.payload)
}