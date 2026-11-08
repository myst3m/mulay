%dw 2.0
---
{name: "Ken", age: 30, address: {street: "Amenabar", zipCode: "AB1234"}} update {
  case .age -> $ + 1
  case .address.street -> "First Street"
}