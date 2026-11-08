%dw 2.0
output application/json
fun toPhoneFormat(str: String) =
    "(" ++ str[0 to 2] ++ ") " ++ str[3 to 5] ++ "-" ++ str[6 to 9]
---
toPhoneFormat("1234567890")