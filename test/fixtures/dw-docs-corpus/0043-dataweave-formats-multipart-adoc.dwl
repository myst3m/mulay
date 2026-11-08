%dw 2.0
output text/plain
---
payload.parts.text.content ++ ':' ++ payload.parts[1].headers.'Content-Disposition'.filename