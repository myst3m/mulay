%dw 2.0
output application/json
---
{
    error: "Method Not Allowed",
    message: error.description
}