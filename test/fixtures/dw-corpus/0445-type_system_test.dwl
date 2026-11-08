%dw 2.0
type Currency = String { format: "$#,###.00" }
output application/java
---
42 is Currency