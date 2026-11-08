%dw 2.0
output application/xml
var myVar = do {
    var language = "Español"
    ---
    language
}
---
{
  document: {
    language: myVar,
    text: "Hola mundo"
  }
}