%dw 2.0
output application/json
---
{
  "arraySizes": {
     size3: sizeOf([1,2,3]),
     size2: sizeOf([[1,2,3],[4]]),
     size0: sizeOf([])
   }
}