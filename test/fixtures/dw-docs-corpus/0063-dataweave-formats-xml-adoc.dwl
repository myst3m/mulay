%dw 2.0
output application/xml
---
{
    test: "A text <a>" as CData
}