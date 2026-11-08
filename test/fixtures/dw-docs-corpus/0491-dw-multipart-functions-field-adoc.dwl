%dw 2.0
import dw::module::Multipart
output multipart/form-data
var myOrder = [
  {
    order: 1,
    amount: 2
  },
  {
    order: 32,
    amount: 1
  }
]
var myClients = {
  clients: {
    client: {
      id: 1,
      name: "Mariano"
    },
    client: {
      id: 2,
      name: "Shoki"
    }
  }
}
---
{
  parts: {
    order: Multipart::field({name:"order",value: myOrder, mime: "application/json", fileName: "order.json"}),
    clients: Multipart::field({name:"clients", value: myClients, mime: "application/xml"})
  }
}