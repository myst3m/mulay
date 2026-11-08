%dw 2.0
type Currency = String { format: "$#,###.00" }
output application/java
---
'hello' is Currency