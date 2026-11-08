%dw 2.0
type PaddedNum = String { format: "000,000" }
output application/java
---
1234 as PaddedNum