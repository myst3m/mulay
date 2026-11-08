%dw 2.0
output application/json
type ID = {id: String, firstName: String, age: Number} | {id: Number, firstName: String, secondName: String}

var nameAge: ID = {firstName: "Seba", id: "123", age: 28}
var fullName: ID = {id: 38123, firstName: "Seba", secondName: "Elizalde"}

var nameString: ID.firstName = "Seba"
var idNumber: ID.id = 38123
---
[nameAge, fullName, nameString ++ " is of type " ++ typeOf(nameString), idNumber ++ " is of type " ++ typeOf(idNumber)]