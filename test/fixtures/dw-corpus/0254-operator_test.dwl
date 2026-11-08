%dw 2.0
---
{name: "Ken", lastName: "Shokida", age: 30} update {
  case .age -> $ + 1
}