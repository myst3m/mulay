%dw 2.0
output application/json
---
{
   objectSizes : {
     sizeIs2: sizeOf({a:1,b:2}),
     sizeIs0: sizeOf({})
   }
}