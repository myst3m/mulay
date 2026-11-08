<?xml version="1.0" encoding="UTF-8"?>
<mule xmlns="http://www.mulesoft.org/schema/mule/core">
  <flow name="transform-flow">
    <transform-message>
      <set-payload><![CDATA[%dw 2.0
output application/xml
---
{root: {value: payload}}]]></set-payload>
    </transform-message>
  </flow>
</mule>