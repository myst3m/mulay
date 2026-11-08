%dw 2.0
output application/xml
---
{
   "XML" : read("<prices><basic>9.99</basic></prices>",
                "application/xml",
                { indexedReader: "false" })."prices"
}