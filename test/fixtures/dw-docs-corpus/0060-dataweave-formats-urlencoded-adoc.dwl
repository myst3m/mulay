%dw 2.0
output application/x-www-form-urlencoded
---
{
  "key" : "value",
  "key 1": "@here",
  "key" : "other value",
  "key 2%": null
}