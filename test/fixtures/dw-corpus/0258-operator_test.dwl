%dw 2.0
---
payload map ((user) ->
  user update {
    case name at .name if(name == "Ken") -> name ++ " (Leandro)"
    case name at .name if(name == "Tomo") -> name ++ " (Christian)"
  }
)