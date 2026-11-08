%dw 2.0
output application/json
---
["Max", "the", "Mule"] map (item, index) -> index ++ " - " ++ item