%dw 2.0
output application/json
---
(readUrl("classpath://name.dwl", "application/dw")).firstName