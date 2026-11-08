%dw 2.0
output application/xml
---
{
    Supermarket: {
        Item: {
            Value: payload..*Item.Name
        }
    }
}