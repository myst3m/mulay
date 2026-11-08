%dw 2.0
output application/json
---
flatten("www.mulesoft.com" scan(/([w]*)\.([a-z]*)\.([a-z]*)/))