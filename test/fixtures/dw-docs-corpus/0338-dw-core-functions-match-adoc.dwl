%dw 2.0
output application/json
---
"me@mulesoft.com" match(/([a-z]*)@([a-z]*)\.com/)