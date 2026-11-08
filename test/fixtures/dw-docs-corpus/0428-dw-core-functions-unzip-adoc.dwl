%dw 2.0
output application/json
---
unzip([ [0,"a"], [1,"a","foo"], [2], [3,"a"] ])