%dw 2.0
var myInput = read("<root>
    <order>
      <items>1</items>
      <items>3</items>
    </order>
    <order>
      <items>2</items>
    </order>
</root>",
"application/xml")
output application/json
---
ContainsRequestedItem: myInput.root.*order.*items contains "3"