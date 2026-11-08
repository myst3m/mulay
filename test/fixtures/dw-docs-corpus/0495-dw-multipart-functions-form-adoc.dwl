%dw 2.0
import dw::module::Multipart
output multipart/form-data
var myOrders = "./orders.xml"
var fileArgs = { name: "file", path: myOrders, mime: "application/xml", fileName: "myorders.xml"}
var fieldArgs = {name:"userName",value: "Annie Point", mime: "text/plain"}
---
Multipart::form([
  Multipart::file(fileArgs),
  Multipart::field(fieldArgs),
  Multipart::field("myJson", {"user": "Annie Point"}, "application/json", "userInfo.json")
])