%dw 2.0
---
payload update {
  case .addresses[0] -> {street: "Second Street", zipCode: "ZZ123"}
}