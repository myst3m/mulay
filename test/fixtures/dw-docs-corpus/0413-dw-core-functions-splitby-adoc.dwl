%dw 2.0
output application/json
---
("192.88.99.0" splitBy("."))[0]