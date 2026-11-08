%dw 2.0
output application/json
type User = {
 address : {country: String, city: String, street: String, number: Number},
 userName : String
}
type Address = User.address

var userAddress: Address = {country: "Argentina", city: "Rosario", street: "Calle Falsa", number: 123}
---
userAddress