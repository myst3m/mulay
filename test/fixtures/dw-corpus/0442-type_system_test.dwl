%dw 2.0
type Currency = String { format: "$#,###.00" }
output application/java
---
1234.56 as Currency