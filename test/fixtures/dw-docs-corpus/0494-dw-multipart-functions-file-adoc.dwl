%dw 2.0
import dw::module::Multipart
var myClients = "myClients.json"
output multipart/form-data
---
Multipart::form([
 Multipart::file("myFile", myClients, 'application/json', "partMyClients.json")
])