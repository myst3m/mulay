%dw 2.0
output application/json
---
["Argentina", "USA", "Brazil"] map (country) -> do {
  var hello = if(country == "Argentina") "Hola"
   else if(country == "USA") "Hello"
   else if(country == "Brazil") "Ola"
   else "Sorry! We don't know $(country)'s language."
   ---
   "$(hello) DataWeave"
}