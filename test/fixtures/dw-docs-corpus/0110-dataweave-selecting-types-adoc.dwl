%dw 2.0
type User = {name: String}
type NameType = User.name
var name: NameType = "Seba"
---
typeOf(name)