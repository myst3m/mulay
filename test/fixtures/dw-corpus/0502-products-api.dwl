%dw 2.0
output application/json
---
{
    error: "Bad Request",
    message: error.description
}