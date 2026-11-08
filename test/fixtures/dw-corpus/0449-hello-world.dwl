%dw 2.0
output application/json
---
{
    message: "Hello, " ++ attributes.uriParams.name ++ "!",
    timestamp: now()
}