%dw 2.0
output application/json

fun lookupCountryCode(phoneNumber: String): String = do {
    var callingCode = (phoneNumber splitBy("-"))[0]
    ---
    (vars.country_code filter ((item, index) -> item.CALLING_CODE == callingCode) map ((item, index) -> item.COUNTRY_CODE))[0]
}
---
payload map ((item, index) -> { phone: item, countryCode: lookupCountryCode(item)})