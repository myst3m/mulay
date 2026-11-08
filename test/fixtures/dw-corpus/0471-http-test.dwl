%dw 2.0
output application/json
---
{
    status: attributes.uriParams.code,
    message: "Response with status " ++ attributes.uriParams.code
}