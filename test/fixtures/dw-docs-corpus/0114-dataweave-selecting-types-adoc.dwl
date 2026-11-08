%dw 2.0
output application/json
ns ns1 http://acme.com
type User = {
 ns1#name : String,
 name : Number,
}
var nameString: User.ns1#name = "Seba"
var nameNumber: User.name = 123
---
{
   "NameString" : typeOf(nameString),
   "NameNumber" : typeOf(nameNumber)
}