%dw 2.0
import dw::module::Multipart
output multipart/form-data
var ordersFilePath = "./orders.xml"
var myArgs = { name: "file", path: ordersFilePath, mime: "application/xml", fileName: "myorders.xml"}
---
Multipart::form([
  Multipart::file(myArgs)
])