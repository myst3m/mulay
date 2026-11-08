%dw 2.0
var conversionRate=13.15
output application/json
---
{
 price_dollars: payload.price,
 price_localCurrency: payload.price * conversionRate
}