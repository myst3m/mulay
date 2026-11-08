%dw 2.0
output application/json
---
{
  "com.mulesoft.dw.xml_reader.honourMixedContentStructure": evaluateCompatibilityFlag("com.mulesoft.dw.xml_reader.honourMixedContentStructure")
}