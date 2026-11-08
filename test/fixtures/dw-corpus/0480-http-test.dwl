%dw 2.0
output application/json
---
{
    error: true,
    status: 404,
    description: error.description
}