%dw 2.0
output application/json
---
{

BinarySizeOf: sizeOf("'my word'" as Binary) ++ " " ++ sizeOf("'my word'" as Binary),

StringSizeOf: sizeOf("'my word'") ++ " " ++ sizeOf("'my word'")

}