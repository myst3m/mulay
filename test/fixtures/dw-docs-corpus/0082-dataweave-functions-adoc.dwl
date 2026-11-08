%dw 2.0
output application/json
fun createUserData(name, countryCode = "US") = { "User name" : name, "Location": countryCode}
---
[createUserData("Cristian", "AR"), createUserData("Max The Mule")]