%dw 2.0
import * from dw::core::Arrays
output application/json
---
{
  "divideBy" : [
      { "divideBy2" : [1, 2, 3, 4, 5] divideBy 2 },
      { "divideBy2" : [1, 2, 3, 4, 5, 6] divideBy 2 },
      { "divideBy3" : [1, 2, 3, 4, 5] divideBy 3 }
  ]
}